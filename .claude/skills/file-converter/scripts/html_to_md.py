#!/usr/bin/env python3
"""
HTML -> Markdown converter.

Usage:
    python3 html_to_md.py input.html output.md
    python3 html_to_md.py *.html --output-dir ./markdown
    python3 html_to_md.py ./site/ --output-dir ./docs
    python3 html_to_md.py input.html output.md --strip script style nav
    python3 html_to_md.py input.html output.md --keep-all

Requirements: pip install beautifulsoup4 markdownify
"""

import argparse
import sys
from pathlib import Path

try:
    from markdownify import markdownify as md_convert
except ImportError:
    print("Error: markdownify required. Install: pip install markdownify beautifulsoup4")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from platform_utils import read_text_safe

# Default tags to strip (safe defaults - removes scripts/styles/nav)
DEFAULT_STRIP = ['script', 'style', 'noscript']


def safe_code_language(el):
    """Safely extract code language from class attribute."""
    classes = el.get('class', [])
    if isinstance(classes, str):
        classes = classes.split()
    for cls in classes:
        if cls.startswith('language-'):
            return cls[len('language-'):]
    return ''


def convert_file(input_path, output_path, strip_tags):
    """Convert a single HTML file to Markdown."""
    text, _enc = read_text_safe(input_path)

    result = md_convert(
        text,
        heading_style='atx',
        bullets='-',
        code_language_callback=safe_code_language,
        strip=strip_tags,
    )

    # Clean up excessive blank lines
    lines = result.split('\n')
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                cleaned.append(line)
        else:
            blank_count = 0
            cleaned.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(cleaned), encoding='utf-8')

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def resolve_html_files(paths):
    """Resolve paths to list of .html files."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(path.glob('**/*.html'))
            files.extend(path.glob('**/*.htm'))
        elif path.is_file() and path.suffix.lower() in ('.html', '.htm'):
            files.append(path)
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description='Convert HTML to Markdown')
    parser.add_argument('input', nargs='+', help='Input .html file(s) or directory')
    parser.add_argument('output', nargs='?', help='Output .md file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--strip', nargs='*', default=None,
                        help='HTML tags to strip (def: script style noscript). Use --keep-all to disable.')
    parser.add_argument('--keep-all', action='store_true', help='Keep all HTML tags (no stripping)')
    args = parser.parse_args()

    # Determine strip tags
    if args.keep_all:
        strip_tags = []
    elif args.strip is not None:
        strip_tags = args.strip if args.strip else DEFAULT_STRIP
    else:
        strip_tags = DEFAULT_STRIP

    # Batch mode
    if args.output_dir:
        files = resolve_html_files(args.input)
        if not files:
            print("No .html files found.")
            sys.exit(1)

        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Converting {len(files)} file(s) -> {out_dir}/")

        for f in files:
            out_path = out_dir / f"{f.stem}.md"
            try:
                convert_file(f, out_path, strip_tags)
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
            args.output = str(Path(args.input[0]).with_suffix('.md'))

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_file(input_path, output_path, strip_tags)
    print("Done.")


if __name__ == '__main__':
    main()
