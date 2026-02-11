#!/usr/bin/env python3
"""
Markdown -> HTML converter w/ syntax highlighting & custom CSS.

Usage:
    python3 md_to_html.py input.md output.html
    python3 md_to_html.py input.md output.html --theme github
    python3 md_to_html.py *.md --output-dir ./html
    python3 md_to_html.py ./docs/ --output-dir ./site --theme dark
    cat input.md | python3 md_to_html.py - output.html

Themes: github (def), dark, minimal, print

Requirements: pip install markdown pygments
"""

import argparse
import html
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: markdown required. Install: pip install markdown pygments")
    sys.exit(1)

# Import shared utils for encoding fallback
sys.path.insert(0, str(Path(__file__).parent))
from platform_utils import read_text_safe

THEMES = {
    'github': """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #24292e; }
        h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
        h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
        code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-size: 85%; }
        pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; }
        pre code { background: none; padding: 0; }
        blockquote { border-left: 4px solid #dfe2e5; padding: 0 16px; color: #6a737d; margin: 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
        th { background: #f6f8fa; font-weight: 600; }
        img { max-width: 100%; }
        a { color: #0366d6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        hr { border: none; border-top: 1px solid #eaecef; }
    """,
    'dark': """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #c9d1d9; background: #0d1117; }
        h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; color: #e6edf3; }
        h1 { font-size: 2em; border-bottom: 1px solid #21262d; padding-bottom: .3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #21262d; padding-bottom: .3em; }
        code { background: #161b22; padding: 2px 6px; border-radius: 3px; font-size: 85%; color: #e6edf3; }
        pre { background: #161b22; padding: 16px; border-radius: 6px; overflow-x: auto; }
        pre code { background: none; padding: 0; }
        blockquote { border-left: 4px solid #30363d; padding: 0 16px; color: #8b949e; margin: 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #30363d; padding: 6px 13px; }
        th { background: #161b22; font-weight: 600; }
        img { max-width: 100%; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        hr { border: none; border-top: 1px solid #21262d; }
    """,
    'minimal': """
        body { font-family: Georgia, serif; max-width: 700px; margin: 60px auto; padding: 0 20px; line-height: 1.8; color: #333; }
        h1, h2, h3 { font-weight: normal; }
        code { background: #f5f5f5; padding: 2px 4px; font-size: 90%; }
        pre { background: #f5f5f5; padding: 16px; overflow-x: auto; }
        pre code { background: none; }
        blockquote { border-left: 3px solid #ccc; padding-left: 16px; color: #666; font-style: italic; }
        a { color: #111; }
        img { max-width: 100%; }
    """,
    'print': """
        body { font-family: 'Times New Roman', serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #000; }
        h1 { font-size: 24pt; text-align: center; }
        h2 { font-size: 18pt; margin-top: 24pt; }
        h3 { font-size: 14pt; }
        code { font-family: 'Courier New', monospace; font-size: 10pt; }
        pre { border: 1px solid #ccc; padding: 12px; font-size: 10pt; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #000; padding: 4px 8px; }
        a { color: #000; }
        @media print { body { margin: 0; } }
    """,
}


def md_to_html(md_text, title='Document', theme='github'):
    """Convert markdown text to complete HTML doc."""
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
    ]
    ext_configs = {
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'guess_lang': True,
        },
        'markdown.extensions.toc': {
            'permalink': True,
        },
    }

    html_body = markdown.markdown(md_text, extensions=extensions, extension_configs=ext_configs)
    css = THEMES.get(theme, THEMES['github'])
    safe_title = html.escape(title, quote=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>{css}</style>
</head>
<body>
{html_body}
</body>
</html>"""


def convert_file(input_path, output_path, theme):
    """Convert a single md file to HTML."""
    md_text, _enc = read_text_safe(input_path)
    title = input_path.stem.replace('-', ' ').replace('_', ' ').title()
    result = md_to_html(md_text, title=title, theme=theme)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding='utf-8')

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def resolve_md_files(paths):
    """Resolve paths to list of .md files."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(path.glob('**/*.md'))
        elif path.is_file() and path.suffix.lower() == '.md':
            files.append(path)
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to HTML')
    parser.add_argument('input', nargs='+', help='Input .md file(s), directory, or - for stdin')
    parser.add_argument('output', nargs='?', help='Output .html file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--theme', '-t', choices=THEMES.keys(), default='github', help='CSS theme')
    args = parser.parse_args()

    # Stdin mode
    if args.input == ['-']:
        md_text = sys.stdin.read()
        result = md_to_html(md_text, title='Document', theme=args.theme)
        if args.output:
            Path(args.output).write_text(result, encoding='utf-8')
        else:
            print(result)
        return

    # Batch mode
    if args.output_dir:
        files = resolve_md_files(args.input)
        if not files:
            print("No .md files found.")
            sys.exit(1)

        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Converting {len(files)} file(s) -> {out_dir}/")

        for f in files:
            out_path = out_dir / f"{f.stem}.html"
            try:
                convert_file(f, out_path, args.theme)
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
            args.output = str(Path(args.input[0]).with_suffix('.html'))

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_file(input_path, output_path, args.theme)
    print("Done.")


if __name__ == '__main__':
    main()
