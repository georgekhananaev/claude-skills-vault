#!/usr/bin/env python3
"""
Text encoding converter (UTF-8, Latin-1, ASCII, UTF-16, etc.) w/ detection.

Usage:
    python3 text_encoding.py detect file.txt
    python3 text_encoding.py convert file.txt --to utf-8
    python3 text_encoding.py convert file.txt --from latin-1 --to utf-8 -o output.txt
    python3 text_encoding.py convert *.txt --to utf-8 --output-dir ./utf8

Requirements: pip install chardet (for auto-detection)
"""

import argparse
import codecs
import sys
from pathlib import Path

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def validate_encoding(name):
    """Validate encoding name. Returns normalized name or exits."""
    try:
        info = codecs.lookup(name)
        return info.name
    except LookupError:
        print(f"Error: unknown encoding '{name}'")
        print("Common encodings: utf-8, latin-1, ascii, utf-16, cp1252, iso-8859-1, shift_jis, euc-kr, gb2312")
        sys.exit(1)


def detect_encoding(path):
    """Detect file encoding."""
    data = Path(path).read_bytes()

    if CHARDET_AVAILABLE:
        result = chardet.detect(data)
        enc = result['encoding']
        conf = result['confidence']
        # chardet can return None for empty/undetectable files
        if not enc:
            return 'utf-8', 0.0
        return enc, conf

    # Fallback heuristics
    if data[:3] == b'\xef\xbb\xbf':
        return 'utf-8-sig', 1.0
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return 'utf-16', 1.0
    try:
        data.decode('utf-8')
        return 'utf-8', 0.9
    except UnicodeDecodeError:
        try:
            data.decode('latin-1')
            return 'latin-1', 0.5
        except UnicodeDecodeError:
            return 'unknown', 0.0


def convert_encoding(input_path, output_path, from_enc, to_enc, errors='strict'):
    """Convert file encoding."""
    if not from_enc:
        from_enc, conf = detect_encoding(input_path)
        print(f"  Detected: {from_enc} (confidence: {conf:.0%})")

    data = Path(input_path).read_bytes()
    try:
        text = data.decode(from_enc)
    except UnicodeDecodeError as e:
        print(f"  Error decoding {Path(input_path).name} as {from_enc}: {e}")
        if errors == 'strict':
            print("  Hint: use --errors replace or --errors ignore to handle unmappable chars")
        sys.exit(1)

    try:
        encoded = text.encode(to_enc, errors=errors)
    except UnicodeEncodeError as e:
        print(f"  Error encoding to {to_enc}: {e}")
        if errors == 'strict':
            print("  Hint: use --errors replace or --errors ignore to handle unmappable chars")
        sys.exit(1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encoded)

    in_size = Path(input_path).stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {Path(input_path).name} ({from_enc}) -> {output_path.name} ({to_enc})  ({in_size:,}B -> {out_size:,}B)")


def main():
    parser = argparse.ArgumentParser(description='Text encoding converter')
    sub = parser.add_subparsers(dest='action', required=True)

    # detect
    det = sub.add_parser('detect', help='Detect file encoding')
    det.add_argument('input', nargs='+', help='Input file(s)')

    # convert
    conv = sub.add_parser('convert', help='Convert encoding')
    conv.add_argument('input', nargs='+', help='Input file(s)')
    conv.add_argument('-o', '--output', help='Output file (single mode, required w/o --output-dir)')
    conv.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    conv.add_argument('--from', dest='from_enc', help='Source encoding (auto-detect if omitted)')
    conv.add_argument('--to', dest='to_enc', default='utf-8', help='Target encoding (def: utf-8)')
    conv.add_argument('--errors', choices=['strict', 'replace', 'ignore'], default='strict',
                       help='How to handle unmappable chars (def: strict)')

    args = parser.parse_args()

    if args.action == 'detect':
        for p in args.input:
            path = Path(p)
            if not path.is_file():
                continue
            enc, conf = detect_encoding(path)
            size = path.stat().st_size
            print(f"  {path.name}: {enc} (confidence: {conf:.0%}, {size:,}B)")
        return

    # Validate encoding names
    to_enc = validate_encoding(args.to_enc)
    from_enc = validate_encoding(args.from_enc) if args.from_enc else None

    # Convert - Batch mode
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in args.input:
            f = Path(p)
            if not f.is_file():
                continue
            out_path = out_dir / f.name
            try:
                convert_encoding(f, out_path, from_enc, to_enc, args.errors)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(130)
            except SystemExit:
                continue
            except Exception as e:
                print(f"  Error: {f.name}: {e}")
        print("Done.")
        return

    # Convert - Single mode (require explicit output to prevent accidental overwrite)
    input_path = Path(args.input[0])
    if not args.output:
        print("Error: --output/-o required in single mode (to prevent accidental overwrite)")
        print(f"  Example: text_encoding.py convert {input_path} --to {to_enc} -o output.txt")
        sys.exit(1)

    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_encoding(input_path, output_path, from_enc, to_enc, args.errors)
    print("Done.")


if __name__ == '__main__':
    main()
