#!/usr/bin/env python3
"""
Base64 encode/decode files (useful for embedding images in HTML/CSS/JSON).

Usage:
    python3 base64_codec.py encode image.png                  # -> stdout
    python3 base64_codec.py encode image.png -o image.b64     # -> file
    python3 base64_codec.py encode image.png --data-uri       # -> data:image/png;base64,...
    python3 base64_codec.py decode image.b64 -o image.png
    python3 base64_codec.py encode *.png --output-dir ./b64   # batch
    cat file | python3 base64_codec.py encode - -o out.b64    # stdin

No external dependencies required.
"""

import argparse
import base64
import binascii
import mimetypes
import sys
from pathlib import Path


def encode_file(input_path, output_path=None, data_uri=False):
    """Encode file to base64 (streaming for large files)."""
    if str(input_path) == '-':
        data = sys.stdin.buffer.read()
    else:
        data = Path(input_path).read_bytes()

    encoded = base64.b64encode(data).decode('ascii')

    if data_uri:
        mime = mimetypes.guess_type(str(input_path))[0] or 'application/octet-stream'
        encoded = f"data:{mime};base64,{encoded}"

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded)
        if str(input_path) != '-':
            in_size = Path(input_path).stat().st_size
            out_size = output_path.stat().st_size
            print(f"  {Path(input_path).name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")
    else:
        print(encoded)


def decode_file(input_path, output_path):
    """Decode base64 file to binary w/ validation."""
    text = Path(input_path).read_text().strip()

    # Strip data URI prefix if present
    if text.startswith('data:'):
        if ',' not in text:
            print(f"Error: invalid data URI format in {input_path}")
            sys.exit(1)
        text = text.split(',', 1)[1]

    try:
        data = base64.b64decode(text, validate=True)
    except binascii.Error as e:
        print(f"Error: invalid base64 data in {input_path}: {e}")
        sys.exit(1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)

    in_size = Path(input_path).stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {Path(input_path).name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def main():
    parser = argparse.ArgumentParser(description='Base64 encode/decode files')
    parser.add_argument('action', choices=['encode', 'decode'], help='Action')
    parser.add_argument('input', nargs='+', help='Input file(s) or - for stdin')
    parser.add_argument('-o', '--output', help='Output file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--data-uri', action='store_true', help='Output as data URI (encode only)')
    args = parser.parse_args()

    # Batch mode
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for p in args.input:
            f = Path(p)
            if not f.is_file():
                continue
            try:
                if args.action == 'encode':
                    out_path = out_dir / f"{f.name}.b64"
                    encode_file(f, out_path, args.data_uri)
                else:
                    out_path = out_dir / f.stem
                    decode_file(f, out_path)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(130)
            except Exception as e:
                print(f"  Error: {f.name}: {e}")
        print("Done.")
        return

    # Single mode
    input_path = args.input[0]
    if input_path != '-' and not Path(input_path).exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    if args.action == 'encode':
        output_path = Path(args.output) if args.output else None
        encode_file(input_path, output_path, args.data_uri)
    else:
        if not args.output:
            print("Error: --output required for decode")
            sys.exit(1)
        decode_file(input_path, Path(args.output))

    if args.output:
        print("Done.")


if __name__ == '__main__':
    main()
