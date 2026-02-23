#!/usr/bin/env python3
"""
Markdown -> PDF converter w/ styling & TOC.

Usage:
    python3 md_to_pdf.py input.md output.pdf
    python3 md_to_pdf.py input.md output.pdf --theme report
    python3 md_to_pdf.py *.md --output-dir ./pdfs
    python3 md_to_pdf.py ./docs/ --output-dir ./pdfs --theme report

Themes: default, report, minimal

Strategy: md -> HTML -> PDF (via weasyprint or falls back to pdfkit/wkhtmltopdf)

Requirements (one of):
    pip install weasyprint          # Preferred (macOS: brew install pango)
    pip install pdfkit              # Requires wkhtmltopdf installed
    pip install markdown            # Required for both
"""

import argparse
import html
import sys
from pathlib import Path

# Cross-platform native library setup (must run before importing weasyprint/cairo)
sys.path.insert(0, str(Path(__file__).parent))
from platform_utils import setup_native_lib_paths, read_text_safe
setup_native_lib_paths()

try:
    import markdown
except ImportError:
    print("Error: markdown required. Install: pip install markdown")
    sys.exit(1)

PDF_ENGINE = None

try:
    from weasyprint import HTML as WeasyHTML
    PDF_ENGINE = 'weasyprint'
except (ImportError, OSError):
    pass

if not PDF_ENGINE:
    try:
        import pdfkit
        # Verify wkhtmltopdf is actually available
        try:
            pdfkit.configuration()
            PDF_ENGINE = 'pdfkit'
        except OSError:
            pass
    except ImportError:
        pass

if not PDF_ENGINE:
    print("Error: Need weasyprint or pdfkit. Install one:")
    print("  pip install weasyprint   (recommended, macOS: brew install pango)")
    print("  pip install pdfkit       (requires wkhtmltopdf)")
    sys.exit(1)

THEMES = {
    'default': """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #24292e; font-size: 14px; }
        h1 { font-size: 28px; border-bottom: 2px solid #eaecef; padding-bottom: 8px; }
        h2 { font-size: 22px; border-bottom: 1px solid #eaecef; padding-bottom: 6px; }
        h3 { font-size: 18px; }
        code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-size: 85%; }
        pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
        pre code { background: none; padding: 0; }
        blockquote { border-left: 4px solid #dfe2e5; padding: 0 16px; color: #6a737d; }
        table { border-collapse: collapse; width: 100%; margin: 16px 0; }
        th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
        th { background: #f6f8fa; }
        img { max-width: 100%; }
        @page { margin: 2cm; size: A4; }
    """,
    'report': """
        body { font-family: 'Times New Roman', Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #000; font-size: 12pt; }
        h1 { font-size: 24pt; text-align: center; margin-top: 2cm; margin-bottom: 1cm; }
        h2 { font-size: 18pt; margin-top: 1.5cm; border-bottom: 1px solid #000; }
        h3 { font-size: 14pt; margin-top: 1cm; }
        code { font-family: 'Courier New', monospace; font-size: 10pt; background: #f5f5f5; padding: 1px 4px; }
        pre { background: #f5f5f5; padding: 12px; border: 1px solid #ddd; font-size: 10pt; }
        pre code { background: none; }
        blockquote { border-left: 3px solid #999; padding-left: 16px; font-style: italic; }
        table { border-collapse: collapse; width: 100%; margin: 12pt 0; }
        th, td { border: 1px solid #000; padding: 4px 8px; font-size: 11pt; }
        th { background: #e8e8e8; font-weight: bold; }
        img { max-width: 100%; }
        @page { margin: 2.5cm; size: A4; }
    """,
    'minimal': """
        body { font-family: Helvetica, Arial, sans-serif; max-width: 750px; margin: 0 auto; padding: 20px; line-height: 1.5; color: #333; font-size: 11pt; }
        h1, h2, h3 { font-weight: 500; }
        code { font-size: 90%; background: #f0f0f0; padding: 1px 3px; }
        pre { background: #f0f0f0; padding: 12px; font-size: 10pt; }
        pre code { background: none; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 4px 8px; }
        img { max-width: 100%; }
        @page { margin: 1.5cm; size: A4; }
    """,
}


def md_to_html(md_text, title, theme):
    """Convert markdown to styled HTML string."""
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.sane_lists',
    ]
    html_body = markdown.markdown(md_text, extensions=extensions)
    css = THEMES.get(theme, THEMES['default'])
    safe_title = html.escape(title, quote=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{safe_title}</title>
    <style>{css}</style>
</head>
<body>
{html_body}
</body>
</html>"""


def html_to_pdf_weasyprint(html_str, output_path, base_url=None):
    """Convert HTML string to PDF using weasyprint."""
    WeasyHTML(string=html_str, base_url=base_url).write_pdf(str(output_path))


def html_to_pdf_pdfkit(html_str, output_path):
    """Convert HTML string to PDF using pdfkit."""
    pdfkit.from_string(html_str, str(output_path), options={
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'margin-right': '20mm',
    })


def convert_file(input_path, output_path, theme):
    """Convert a single .md file to PDF."""
    md_text, _enc = read_text_safe(input_path)
    title = input_path.stem.replace('-', ' ').replace('_', ' ').title()
    html_str = md_to_html(md_text, title, theme)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if PDF_ENGINE == 'weasyprint':
        base_url = str(input_path.parent.resolve())
        html_to_pdf_weasyprint(html_str, output_path, base_url=base_url)
    else:
        html_to_pdf_pdfkit(html_str, output_path)

    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({out_size:,}B)")


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
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF')
    parser.add_argument('input', nargs='+', help='Input .md file(s) or directory')
    parser.add_argument('output', nargs='?', help='Output .pdf file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--theme', '-t', choices=THEMES.keys(), default='default', help='PDF theme')
    args = parser.parse_args()

    print(f"Using PDF engine: {PDF_ENGINE}")

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
            out_path = out_dir / f"{f.stem}.pdf"
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
            args.output = str(Path(args.input[0]).with_suffix('.pdf'))

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_file(input_path, output_path, args.theme)
    print("Done.")


if __name__ == '__main__':
    main()
