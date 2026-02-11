#!/usr/bin/env python3
"""
Image converter & resizer - supports PNG, JPG, WEBP, BMP, TIFF, GIF, ICO, AVIF, HEIC.

Usage:
    python3 convert_image.py <input> <output> [--width W] [--height H] [--quality Q] [--fit MODE]
    python3 convert_image.py input.png output.webp --width 800 --quality 85
    python3 convert_image.py input.jpg output.png --width 200 --height 200 --fit cover
    python3 convert_image.py *.png --output-dir ./converted --format webp --width 1200

Batch mode:
    python3 convert_image.py *.png --output-dir ./out --format webp
    python3 convert_image.py ./photos/ --output-dir ./thumbs --format jpg --width 300 --height 300 --fit cover

Fit modes: contain (default), cover, fill, inside, outside

Requirements: pip install Pillow
Optional: pip install pillow-heif (for HEIC/HEIF support)
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Error: Pillow required. Install: pip install Pillow")
    sys.exit(1)

# Guard against decompression bombs (default 178M pixels, raise to 300M)
Image.MAX_IMAGE_PIXELS = 300_000_000

# Optional HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

SUPPORTED = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif'}
if HEIC_SUPPORTED:
    SUPPORTED.update({'.heic', '.heif'})

FIT_MODES = ('contain', 'cover', 'fill', 'inside', 'outside')


def positive_int(value):
    """Argparse type: positive integer."""
    ival = int(value)
    if ival <= 0:
        raise argparse.ArgumentTypeError(f"must be positive, got {value}")
    return ival


def resolve_inputs(paths):
    """Resolve file paths & directories to list of image files (case-insensitive)."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(f for f in path.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED)
        elif path.is_file() and path.suffix.lower() in SUPPORTED:
            files.append(path)
        else:
            print(f"Warning: skipping unsupported file: {p}")
    return sorted(set(files))


def resize_image(img, width, height, fit):
    """Resize image w/ given fit mode. Returns new image (never mutates input)."""
    orig_w, orig_h = img.size

    if not width and not height:
        return img

    if not width:
        width = int(orig_w * (height / orig_h))
    if not height:
        height = int(orig_h * (width / orig_w))

    if fit == 'fill':
        return img.resize((width, height), Image.Resampling.LANCZOS)

    if fit == 'contain':
        result = img.copy()
        result.thumbnail((width, height), Image.Resampling.LANCZOS)
        return result

    if fit == 'cover':
        ratio_w = width / orig_w
        ratio_h = height / orig_h
        ratio = max(ratio_w, ratio_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return resized.crop((left, top, left + width, top + height))

    if fit == 'inside':
        if orig_w <= width and orig_h <= height:
            return img.copy()
        result = img.copy()
        result.thumbnail((width, height), Image.Resampling.LANCZOS)
        return result

    if fit == 'outside':
        ratio_w = width / orig_w
        ratio_h = height / orig_h
        ratio = max(ratio_w, ratio_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return img


def convert_single(input_path, output_path, width, height, quality, fit):
    """Convert a single image file."""
    with Image.open(input_path) as img:
        # Auto-fix EXIF orientation
        img = ImageOps.exif_transpose(img)

        # Handle transparency for formats that don't support it
        out_ext = output_path.suffix.lower()
        if out_ext in ('.jpg', '.jpeg', '.bmp') and img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = bg
        elif out_ext in ('.jpg', '.jpeg', '.bmp') and img.mode != 'RGB':
            img = img.convert('RGB')

        img = resize_image(img, width, height, fit)

        save_kwargs = {}
        if out_ext in ('.jpg', '.jpeg', '.webp', '.avif'):
            save_kwargs['quality'] = max(1, min(100, quality))
        if out_ext == '.webp':
            save_kwargs['method'] = 4
        if out_ext == '.png':
            save_kwargs['optimize'] = True
        if out_ext == '.ico':
            sizes = [(min(img.size[0], 256), min(img.size[1], 256))]
            save_kwargs['sizes'] = sizes

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), **save_kwargs)

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def main():
    parser = argparse.ArgumentParser(description='Convert & resize images')
    parser.add_argument('input', nargs='+', help='Input file(s) or directory')
    parser.add_argument('output', nargs='?', help='Output file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--format', '-f', help='Output format (batch mode)')
    parser.add_argument('--width', '-W', type=positive_int, help='Target width (positive int)')
    parser.add_argument('--height', '-H', type=positive_int, help='Target height (positive int)')
    parser.add_argument('--quality', '-q', type=int, default=85, help='Quality 1-100 (def: 85)')
    parser.add_argument('--fit', choices=FIT_MODES, default='contain', help='Resize fit mode')
    args = parser.parse_args()

    # Validate quality range
    if not 1 <= args.quality <= 100:
        print("Error: quality must be 1-100")
        sys.exit(1)

    # Batch mode
    if args.output_dir or args.format:
        fmt = args.format or 'png'
        if not fmt.startswith('.'):
            fmt = f'.{fmt}'
        if fmt not in SUPPORTED:
            print(f"Error: unsupported format '{fmt}'. Supported: {', '.join(sorted(SUPPORTED))}")
            sys.exit(1)

        files = resolve_inputs(args.input)
        if not files:
            print("No supported image files found.")
            sys.exit(1)

        out_dir = Path(args.output_dir or '.')
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"Converting {len(files)} file(s) -> {out_dir}/ as {fmt}")
        for f in files:
            out_path = out_dir / f"{f.stem}{fmt}"
            try:
                convert_single(f, out_path, args.width, args.height, args.quality, args.fit)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(130)
            except Exception as e:
                print(f"  Error: {f.name}: {e}")
        print("Done.")
        return

    # Single mode
    if not args.output:
        if len(args.input) == 1:
            print("Error: provide output file or use --output-dir for batch mode")
            sys.exit(1)
        output = args.input.pop()
        args.output = output

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_single(input_path, output_path, args.width, args.height, args.quality, args.fit)
    print("Done.")


if __name__ == '__main__':
    main()
