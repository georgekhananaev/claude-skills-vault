#!/usr/bin/env python3
"""
SVG <-> PNG/JPG/WEBP converter.

Usage:
    python3 svg_convert.py input.svg output.png --width 512
    python3 svg_convert.py input.svg output.jpg --width 1024 --quality 90
    python3 svg_convert.py input.svg output.webp --width 800
    python3 svg_convert.py input.png output.svg    # Raster -> SVG (embedded)
    python3 svg_convert.py *.svg --output-dir ./png --format png --width 256

SVG -> Raster: requires cairosvg (pip install cairosvg)
Raster -> SVG: creates embedded image SVG wrapper (not vector tracing)
"""

import argparse
import io
import sys
from pathlib import Path

# Cross-platform native library setup
sys.path.insert(0, str(Path(__file__).parent))
from platform_utils import setup_native_lib_paths
setup_native_lib_paths()

try:
    import cairosvg
    CAIRO_AVAILABLE = True
except (ImportError, OSError):
    CAIRO_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

RASTER_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}


def svg_to_raster(input_path, output_path, width=None, height=None, quality=85):
    """Convert SVG to any raster format via PNG intermediary."""
    if not CAIRO_AVAILABLE:
        print("Error: cairosvg required. Install: pip install cairosvg")
        print("  macOS: brew install cairo")
        print("  Linux: apt install libcairo2-dev")
        sys.exit(1)

    out_ext = output_path.suffix.lower()
    kwargs = {}
    if width:
        kwargs['output_width'] = width
    if height:
        kwargs['output_height'] = height

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Always render to PNG first, then convert to target format
    png_data = cairosvg.svg2png(url=str(input_path.resolve()), **kwargs)

    if out_ext == '.png':
        output_path.write_bytes(png_data)
    else:
        if not PIL_AVAILABLE:
            print(f"Error: Pillow required for {out_ext} output. Install: pip install Pillow")
            sys.exit(1)
        with Image.open(io.BytesIO(png_data)) as img:
            if out_ext in ('.jpg', '.jpeg', '.bmp'):
                if img.mode in ('RGBA', 'LA'):
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

            save_kwargs = {}
            if out_ext in ('.jpg', '.jpeg', '.webp'):
                save_kwargs['quality'] = quality
            if out_ext == '.webp':
                save_kwargs['method'] = 4

            img.save(str(output_path), **save_kwargs)

    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({out_size:,}B)")


def raster_to_svg(input_path, output_path, width=None, height=None):
    """Wrap raster image in SVG (embedded, not traced)."""
    if not PIL_AVAILABLE:
        print("Error: Pillow required. Install: pip install Pillow")
        sys.exit(1)

    import base64
    import mimetypes

    with Image.open(input_path) as img:
        img_w, img_h = img.size

    if width and not height:
        height = int(img_h * (width / img_w))
    elif height and not width:
        width = int(img_w * (height / img_h))
    elif not width and not height:
        width, height = img_w, img_h

    mime = mimetypes.guess_type(str(input_path))[0] or 'image/png'
    b64 = base64.b64encode(input_path.read_bytes()).decode('ascii')

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <image width="{width}" height="{height}" href="data:{mime};base64,{b64}"/>
</svg>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding='utf-8')

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def main():
    parser = argparse.ArgumentParser(description='SVG converter')
    parser.add_argument('input', nargs='+', help='Input file(s)')
    parser.add_argument('output', nargs='?', help='Output file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--format', '-f', help='Output format (batch)')
    parser.add_argument('--width', '-W', type=int, help='Output width')
    parser.add_argument('--height', '-H', type=int, help='Output height')
    parser.add_argument('--quality', '-q', type=int, default=85, help='JPG/WEBP quality')
    args = parser.parse_args()

    # Batch mode
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        fmt = args.format or 'png'
        if not fmt.startswith('.'):
            fmt = f'.{fmt}'

        for p in args.input:
            f = Path(p)
            if not f.is_file():
                continue
            out_path = out_dir / f"{f.stem}{fmt}"
            try:
                if f.suffix.lower() == '.svg':
                    svg_to_raster(f, out_path, args.width, args.height, args.quality)
                else:
                    raster_to_svg(f, out_path, args.width, args.height)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(130)
            except Exception as e:
                print(f"  Error: {f.name}: {e}")
        print("Done.")
        return

    # Single mode
    if not args.output:
        if len(args.input) >= 2:
            args.output = args.input.pop()
        else:
            print("Error: provide output file or use --output-dir for batch mode")
            sys.exit(1)

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    if input_path.suffix.lower() == '.svg':
        svg_to_raster(input_path, output_path, args.width, args.height, args.quality)
    else:
        raster_to_svg(input_path, output_path, args.width, args.height)
    print("Done.")


if __name__ == '__main__':
    main()
