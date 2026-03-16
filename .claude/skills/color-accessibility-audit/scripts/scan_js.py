#!/usr/bin/env python3
"""
JS/TS Color Contrast Scanner
Scans JavaScript and TypeScript files for color definitions and analyzes
text/background contrast pairs against WCAG 2.1/2.2 standards.

Usage:
  python3 scan_js.py path/to/theme.ts
  python3 scan_js.py path/to/theme.ts --cvd
  python3 scan_js.py path/to/tokens.js --json
  python3 scan_js.py src/ --recursive
  python3 scan_js.py src/ --recursive --json > report.json

Supported patterns:
  - Theme objects (MUI, Chakra, Mantine, custom)
  - Design token files (Style Dictionary, Tokens Studio, etc.)
  - Tailwind config (tailwind.config.js/ts)
  - Styled-components / Emotion CSS-in-JS
  - Inline styles in React/JSX/TSX
  - CSS module objects
  - Constants/enums with color values
  - Next.js / Nuxt theme files
"""

import sys
import re
import json
import os
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from contrast_check import (
    normalize_hex,
    contrast_ratio,
    wcag_rating,
    find_fixed_color,
    cvd_analysis,
    check_risky_hues,
    NAMED_COLORS,
)

# ═══════════════════════════════════════════════════════════════
# Color Extraction Patterns
# ═══════════════════════════════════════════════════════════════

# Hex colors in strings: '#fff', "#3b82f6", '#3b82f6cc'
HEX_IN_STRING_RE = re.compile(
    r"""(['"`])(\#(?:[0-9a-fA-F]{3,4}){1,2})\1"""
)

# Hex colors assigned to variables/properties
HEX_ASSIGN_RE = re.compile(
    r"""(\#(?:[0-9a-fA-F]{3,4}){1,2})(?=\s*[,;}\])\n]|$)"""
)

# rgb()/rgba() in strings or template literals
RGB_RE = re.compile(
    r"""rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*[\d.]+\s*)?\)"""
)

# hsl()/hsla()
HSL_RE = re.compile(
    r"""hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*(?:,\s*[\d.]+\s*)?\)"""
)

# ═══════════════════════════════════════════════════════════════
# Semantic Key Detection
# ═══════════════════════════════════════════════════════════════

# Keys that indicate TEXT color
TEXT_KEYS = re.compile(
    r"""(?:^|[._-])(?:"""
    r"""color|text|foreground|fg|font[_-]?color|text[_-]?color|"""
    r"""label[_-]?color|title[_-]?color|heading[_-]?color|"""
    r"""body[_-]?color|caption[_-]?color|subtitle[_-]?color|"""
    r"""placeholder[_-]?color|hint[_-]?color|link[_-]?color|"""
    r"""icon[_-]?color|on[_-]?(?:primary|secondary|surface|background|error|success|warning)"""
    r""")(?:[._-]|$)""",
    re.IGNORECASE,
)

# Keys that indicate BACKGROUND color
BG_KEYS = re.compile(
    r"""(?:^|[._-])(?:"""
    r"""background|bg|surface|backdrop|fill|canvas|"""
    r"""bg[_-]?color|background[_-]?color|"""
    r"""card[_-]?(?:bg|background)|page[_-]?(?:bg|background)|"""
    r"""container[_-]?(?:bg|background)|panel[_-]?(?:bg|background)|"""
    r"""primary|secondary|accent|base"""
    r""")(?:[._-]|$)""",
    re.IGNORECASE,
)

# Keys that indicate BORDER color (non-text contrast)
BORDER_KEYS = re.compile(
    r"""(?:^|[._-])(?:"""
    r"""border|outline|divider|separator|stroke|ring"""
    r""")(?:[._-]|$)""",
    re.IGNORECASE,
)

# Keys that indicate a color pair context (e.g., a theme group)
CONTEXT_KEYS = re.compile(
    r"""(?:^|[._-])(?:"""
    r"""primary|secondary|accent|success|error|warning|info|danger|"""
    r"""neutral|muted|disabled|active|hover|focus|dark|light|"""
    r"""header|footer|sidebar|card|button|badge|alert|toast|"""
    r"""nav|menu|modal|dialog|input|form"""
    r""")(?:[._-]|$)""",
    re.IGNORECASE,
)


def classify_key(key):
    """Classify a key as text, background, border, or unknown."""
    if TEXT_KEYS.search(key):
        return "text"
    if BG_KEYS.search(key):
        return "background"
    if BORDER_KEYS.search(key):
        return "border"
    return "unknown"


# ═══════════════════════════════════════════════════════════════
# Color Value Extraction
# ═══════════════════════════════════════════════════════════════

def rgb_to_hex_str(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def hsl_to_hex_str(h, s, l):
    import colorsys
    r, g, b = colorsys.hls_to_rgb(float(h) / 360, float(l) / 100, float(s) / 100)
    return rgb_to_hex_str(r * 255, g * 255, b * 255)


def extract_color_from_value(value_str):
    """Try to extract a hex color from a JS value string."""
    value_str = value_str.strip().strip("'\"`,;")

    # HSL
    hsl_match = HSL_RE.search(value_str)
    if hsl_match:
        try:
            return normalize_hex(hsl_to_hex_str(
                hsl_match.group(1), hsl_match.group(2), hsl_match.group(3)
            ))
        except ValueError:
            pass

    # RGB
    rgb_match = RGB_RE.search(value_str)
    if rgb_match:
        try:
            return normalize_hex(rgb_to_hex_str(
                int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
            ))
        except ValueError:
            pass

    # Hex
    hex_match = HEX_ASSIGN_RE.search(value_str)
    if hex_match:
        try:
            return normalize_hex(hex_match.group(1))
        except ValueError:
            pass

    # Named colors (only exact matches from common ones)
    lower = value_str.lower().strip("'\"` ")
    if lower in NAMED_COLORS:
        return normalize_hex(NAMED_COLORS[lower])

    return None


# ═══════════════════════════════════════════════════════════════
# JS/TS File Parsing
# ═══════════════════════════════════════════════════════════════

def strip_comments(code):
    """Remove JS/TS single-line and multi-line comments."""
    # Multi-line comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    # Single-line comments (but not inside strings — simplified approach)
    code = re.sub(r"(?<!['\"`:\\])//.*?$", "", code, flags=re.MULTILINE)
    return code


def extract_key_value_pairs(code):
    """
    Extract key-value pairs where values are color-like strings.
    Handles multiple patterns:
      - key: '#color'
      - key: "rgb(...)"
      - key = '#color'
      - color: '#hex', backgroundColor: '#hex'
      - { text: '#hex', bg: '#hex' }
    """
    entries = []

    # Pattern 1: Object property — key: 'value' or key: "value"
    # Matches:  color: '#fff',  backgroundColor: "rgb(0,0,0)",  primary: '#3b82f6'
    obj_prop_re = re.compile(
        r"""(?:^|[{,;\n])\s*"""
        r"""['"]?([\w.$-]+)['"]?\s*:\s*"""
        r"""['"`]([^'"`\n]+)['"`]""",
        re.MULTILINE,
    )
    for m in obj_prop_re.finditer(code):
        key = m.group(1).strip()
        value = m.group(2).strip()
        color = extract_color_from_value(value)
        if color:
            entries.append((key, color, m.start(), "object_property"))

    # Pattern 2: Variable assignment — const/let/var name = 'color'
    var_assign_re = re.compile(
        r"""(?:const|let|var|export\s+(?:const|let))\s+"""
        r"""([\w$]+)\s*(?::\s*\w+\s*)?=\s*['"`]([^'"`\n]+)['"`]""",
        re.MULTILINE,
    )
    for m in var_assign_re.finditer(code):
        key = m.group(1).strip()
        value = m.group(2).strip()
        color = extract_color_from_value(value)
        if color:
            entries.append((key, color, m.start(), "variable"))

    # Pattern 3: Inline style JSX — style={{ color: '#hex', backgroundColor: '#hex' }}
    inline_style_re = re.compile(
        r"""(color|backgroundColor|borderColor|background)\s*:\s*['"`]([^'"`\n]+)['"`]""",
    )
    for m in inline_style_re.finditer(code):
        key = m.group(1).strip()
        value = m.group(2).strip()
        color = extract_color_from_value(value)
        if color:
            entries.append((key, color, m.start(), "inline_style"))

    # Pattern 4: Template literal color — `${something}` patterns with hex
    # e.g., color: `#${hex}` or simpler cases
    template_hex_re = re.compile(
        r"""(?:color|background|bg|fill|stroke)\s*[:=]\s*[`'](\#[0-9a-fA-F]{3,8})[`']"""
    )
    for m in template_hex_re.finditer(code):
        color = extract_color_from_value(m.group(1))
        if color:
            entries.append(("template_color", color, m.start(), "template"))

    # Pattern 5: Tailwind config theme.extend.colors
    tw_color_re = re.compile(
        r"""['"]?([\w-]+)['"]?\s*:\s*['"](\#[0-9a-fA-F]{3,8})['"]""",
    )
    for m in tw_color_re.finditer(code):
        key = m.group(1)
        value = m.group(2)
        color = extract_color_from_value(value)
        if color:
            # Avoid re-adding if already found
            entries.append((key, color, m.start(), "config"))

    return entries


def get_line_number(code, pos):
    """Get the line number for a character position."""
    return code[:pos].count("\n") + 1


def build_context_path(code, pos):
    """
    Try to determine the nesting context for a position in the code.
    Returns a path like 'theme.colors.primary' or 'dark.text'.
    """
    # Look backwards from pos to find enclosing keys
    before = code[:pos]
    # Find recent key assignments at lower indent levels
    parts = []
    lines = before.split("\n")
    current_indent = len(lines[-1]) - len(lines[-1].lstrip()) if lines else 0

    for line in reversed(lines[:-1]):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent < current_indent:
            # Try to extract a key from this line
            key_match = re.match(r"""['"]?([\w.$-]+)['"]?\s*[:={]""", stripped)
            if key_match:
                parts.insert(0, key_match.group(1))
                current_indent = indent
        if indent == 0 and parts:
            break

    return ".".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════════
# Pair Matching Logic
# ═══════════════════════════════════════════════════════════════

def find_color_pairs(entries, code):
    """
    Match text/background color pairs from extracted entries.
    Uses semantic key classification and context grouping.
    """
    pairs = []

    # Group entries by their nesting context
    contexts = {}
    for key, color, pos, source in entries:
        ctx = build_context_path(code, pos)
        full_path = f"{ctx}.{key}" if ctx else key
        role = classify_key(full_path)
        line = get_line_number(code, pos)

        entry = {
            "key": key,
            "full_path": full_path,
            "color": color,
            "role": role,
            "line": line,
            "source": source,
            "context": ctx,
        }

        if ctx not in contexts:
            contexts[ctx] = []
        contexts[ctx].append(entry)

    # Within each context group, pair text colors with background colors
    for ctx, group in contexts.items():
        text_entries = [e for e in group if e["role"] == "text"]
        bg_entries = [e for e in group if e["role"] == "background"]
        border_entries = [e for e in group if e["role"] == "border"]

        # Default background fallback
        default_bg = "#ffffff"

        # If context is "dark" or contains "dark", assume dark background
        if "dark" in ctx.lower():
            default_bg = "#1a1a2e"

        for te in text_entries:
            if bg_entries:
                for be in bg_entries:
                    pairs.append({
                        "text_color": te["color"],
                        "bg_color": be["color"],
                        "text_key": te["full_path"],
                        "bg_key": be["full_path"],
                        "text_line": te["line"],
                        "bg_line": be["line"],
                        "context": ctx,
                        "source": f"{te['source']}: {te['key']} + {be['key']}",
                    })
            else:
                # No explicit background in this context — use default
                pairs.append({
                    "text_color": te["color"],
                    "bg_color": default_bg,
                    "text_key": te["full_path"],
                    "bg_key": f"(default: {default_bg})",
                    "text_line": te["line"],
                    "bg_line": None,
                    "context": ctx,
                    "source": f"{te['source']}: {te['key']} (no explicit background)",
                })

        # Border vs background (SC 1.4.11)
        for boe in border_entries:
            bg = bg_entries[0]["color"] if bg_entries else default_bg
            bg_key = bg_entries[0]["full_path"] if bg_entries else f"(default: {default_bg})"
            pairs.append({
                "text_color": boe["color"],
                "bg_color": bg,
                "text_key": boe["full_path"],
                "bg_key": bg_key,
                "text_line": boe["line"],
                "bg_line": bg_entries[0]["line"] if bg_entries else None,
                "context": ctx,
                "source": f"border vs background (SC 1.4.11): {boe['key']}",
            })

    # Also try to pair any unmatched "unknown" colors that appear adjacent
    # in theme-like structures (e.g., primary: '#blue', onPrimary: '#white')
    for ctx, group in contexts.items():
        unknowns = [e for e in group if e["role"] == "unknown"]
        for e in unknowns:
            key_lower = e["key"].lower()
            # Check for "on" prefix pattern: onPrimary, onSurface, etc.
            on_match = re.match(r"on[_-]?(\w+)", key_lower)
            if on_match:
                base_name = on_match.group(1)
                # Find the corresponding base color in the same context
                for other in group:
                    if other["key"].lower() == base_name or other["key"].lower().endswith(base_name):
                        pairs.append({
                            "text_color": e["color"],
                            "bg_color": other["color"],
                            "text_key": e["full_path"],
                            "bg_key": other["full_path"],
                            "text_line": e["line"],
                            "bg_line": other["line"],
                            "context": ctx,
                            "source": f"onX/X pattern: {e['key']} on {other['key']}",
                        })

    return pairs


# ═══════════════════════════════════════════════════════════════
# Analysis & Reporting
# ═══════════════════════════════════════════════════════════════

def analyze_pairs(pairs, include_cvd=False):
    """Run full contrast analysis on each pair."""
    results = []
    seen = set()

    for pair in pairs:
        # Deduplicate
        dedup_key = (pair["text_color"], pair["bg_color"])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        try:
            text_hex = normalize_hex(pair["text_color"])
            bg_hex = normalize_hex(pair["bg_color"])
        except ValueError as e:
            results.append({"error": str(e), **pair})
            continue

        ratio = contrast_ratio(text_hex, bg_hex)
        rating = wcag_rating(ratio)

        result = {
            "text_color": text_hex,
            "background_color": bg_hex,
            "text_key": pair["text_key"],
            "bg_key": pair["bg_key"],
            "text_line": pair["text_line"],
            "bg_line": pair["bg_line"],
            "context": pair["context"],
            "source": pair["source"],
            **rating,
        }

        if not rating["aa_body_text"]:
            fix = find_fixed_color(text_hex, bg_hex, 4.5)
            result["fix_aa"] = fix
            result["fix_aa_ratio"] = round(contrast_ratio(fix, bg_hex), 2)
        if not rating["aaa_body_text"]:
            fix = find_fixed_color(text_hex, bg_hex, 7.0)
            result["fix_aaa"] = fix
            result["fix_aaa_ratio"] = round(contrast_ratio(fix, bg_hex), 2)

        if include_cvd:
            result["cvd"] = cvd_analysis(text_hex, bg_hex)
            result["hue_warnings"] = check_risky_hues(text_hex, bg_hex)

        results.append(result)

    return results


def print_report(results, filepaths):
    """Print a human-readable report."""
    issues = [r for r in results if not r.get("aa_body_text", True)]
    warnings = [r for r in results if r.get("aa_body_text", False) and not r.get("aaa_body_text", True)]
    passing = [r for r in results if r.get("aaa_body_text", False)]
    errors = [r for r in results if "error" in r]
    total = len(results) - len(errors)

    files_str = ", ".join(filepaths) if len(filepaths) <= 3 else f"{len(filepaths)} files"

    print()
    print(f"{'═' * 60}")
    print(f"  JS/TS COLOR CONTRAST SCAN REPORT")
    print(f"  Source: {files_str}")
    print(f"{'═' * 60}")
    print()
    print(f"  Found {total} color pairs")
    print()
    print(f"  ❌ FAIL AA:         {len(issues)} pairs")
    print(f"  ⚠️  Pass AA only:   {len(warnings)} pairs")
    print(f"  ✅ Pass AAA:        {len(passing)} pairs")
    if errors:
        print(f"  ⛔ Parse errors:    {len(errors)}")
    print()

    if issues:
        print(f"{'─' * 60}")
        print(f"  ❌ FAILING PAIRS (below AA 4.5:1)")
        print(f"{'─' * 60}")
        for r in issues:
            _print_issue(r)

    if warnings:
        print(f"{'─' * 60}")
        print(f"  ⚠️  AA ONLY (pass AA but fail AAA 7:1)")
        print(f"{'─' * 60}")
        for r in warnings:
            _print_issue(r)

    if passing:
        print(f"{'─' * 60}")
        print(f"  ✅ PASSING AAA")
        print(f"{'─' * 60}")
        for r in passing:
            loc = f"L{r['text_line']}" if r.get("text_line") else ""
            print(f"    {r['text_key']} on {r['bg_key']}  {loc}")
            print(f"      {r['text_color']} on {r['background_color']}  →  {r['ratio']}:1 ✅")
            print()

    if errors:
        print(f"{'─' * 60}")
        print(f"  ⛔ ERRORS")
        print(f"{'─' * 60}")
        for r in errors:
            print(f"    {r.get('text_key', '?')}: {r['error']}")
        print()

    print(f"{'═' * 60}")
    if not issues:
        print(f"  ✅ All color pairs pass WCAG AA!")
        if not warnings:
            print(f"  ✅ All color pairs also pass WCAG AAA!")
    else:
        print(f"  ❌ {len(issues)} pair(s) need fixing to meet WCAG AA.")
        print(f"     See suggested fix hex codes above.")
    print(f"{'═' * 60}")
    print()


def _print_issue(r):
    """Print a single issue."""
    loc_parts = []
    if r.get("text_line"):
        loc_parts.append(f"text L{r['text_line']}")
    if r.get("bg_line"):
        loc_parts.append(f"bg L{r['bg_line']}")
    loc = f"  ({', '.join(loc_parts)})" if loc_parts else ""

    print()
    print(f"    Context:     {r.get('context', '-') or '(root)'}")
    print(f"    Source:      {r['source']}")
    print(f"    Text:        {r['text_color']}  ← {r['text_key']}{loc}")
    print(f"    Background:  {r['background_color']}  ← {r['bg_key']}")
    print(f"    Contrast:    {r['ratio']}:1")
    print(f"    AA Body:     {'✅' if r['aa_body_text'] else '❌'}  "
          f"AA Large: {'✅' if r['aa_large_text'] else '❌'}  "
          f"AAA Body: {'✅' if r['aaa_body_text'] else '❌'}  "
          f"AAA Large: {'✅' if r['aaa_large_text'] else '❌'}")

    if "fix_aa" in r:
        print(f"    Fix for AA:  {r['fix_aa']}  →  {r['fix_aa_ratio']}:1")
    if "fix_aaa" in r:
        print(f"    Fix for AAA: {r['fix_aaa']}  →  {r['fix_aaa_ratio']}:1")

    if r.get("cvd"):
        icons = {"protanopia": "🔴", "deuteranopia": "🟢", "tritanopia": "🔵"}
        risk_str = {"critical": "❌ CRITICAL", "high": "⚠️  HIGH", "warning": "⚠️  WARN", "ok": "✅ OK"}
        for cvd in r["cvd"]:
            icon = icons.get(cvd["type"], "•")
            print(f"    {icon} {cvd['type']:15s} {cvd['simulated_ratio']:5.2f}:1  "
                  f"ΔE={cvd['delta_e']:5.1f}  {risk_str.get(cvd['risk'], cvd['risk'])}")

    if r.get("hue_warnings"):
        for w in r["hue_warnings"]:
            print(f"    ⚠️  {w}")

    print()


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

SUPPORTED_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def collect_files(path, recursive=False):
    """Collect all supported files from a path."""
    if os.path.isfile(path):
        return [path]

    if os.path.isdir(path):
        files = []
        if recursive:
            for root, dirs, filenames in os.walk(path):
                # Skip node_modules, .next, dist, build
                dirs[:] = [d for d in dirs if d not in (
                    "node_modules", ".next", "dist", "build", ".git",
                    "__pycache__", ".turbo", ".cache", "coverage"
                )]
                for f in filenames:
                    if os.path.splitext(f)[1] in SUPPORTED_EXTENSIONS:
                        files.append(os.path.join(root, f))
        else:
            for f in os.listdir(path):
                if os.path.splitext(f)[1] in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(path, f))
        return sorted(files)

    # Glob pattern
    return sorted(glob.glob(path))


def main():
    args = sys.argv[1:]

    include_cvd = "--cvd" in args
    output_json = "--json" in args
    recursive = "--recursive" in args or "-r" in args
    args = [a for a in args if a not in ("--cvd", "--json", "--recursive", "-r")]

    if not args:
        print("Usage: python3 scan_js.py <path> [--cvd] [--json] [--recursive]")
        print()
        print("Scans JS/TS files for color contrast issues against WCAG 2.1/2.2.")
        print()
        print("Paths:")
        print("  file.ts              Single file")
        print("  src/theme/           Directory (top-level JS/TS files)")
        print("  src/ --recursive     Directory (all JS/TS files recursively)")
        print()
        print("Options:")
        print("  --cvd        Include color blindness simulation")
        print("  --json       Output structured JSON report")
        print("  --recursive  Scan directories recursively (alias: -r)")
        print()
        print("Supported file types: .js .jsx .ts .tsx .mjs .cjs")
        print()
        print("Examples:")
        print("  python3 scan_js.py theme.ts")
        print("  python3 scan_js.py tailwind.config.js --cvd")
        print("  python3 scan_js.py src/ -r --json > report.json")
        print("  python3 scan_js.py src/styles/ src/theme.ts --cvd")
        sys.exit(1)

    # Collect all files
    all_files = []
    for path in args:
        files = collect_files(path, recursive)
        if not files:
            print(f"Warning: No supported files found at '{path}'", file=sys.stderr)
        all_files.extend(files)

    if not all_files:
        print("Error: No JS/TS files found to scan.")
        sys.exit(1)

    # Parse all files
    all_pairs = []
    for filepath in all_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except IOError as e:
            print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
            continue

        code = strip_comments(code)
        entries = extract_key_value_pairs(code)

        if entries:
            pairs = find_color_pairs(entries, code)
            # Tag pairs with their source file
            for p in pairs:
                p["file"] = filepath
            all_pairs.extend(pairs)

    if not all_pairs:
        msg = f"No text/background color pairs found in {len(all_files)} file(s)."
        if not recursive:
            msg += "\nTip: Try --recursive to scan subdirectories."
        print(msg)
        sys.exit(0)

    # Analyze
    results = analyze_pairs(all_pairs, include_cvd=include_cvd)

    # Output
    if output_json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, all_files)


if __name__ == "__main__":
    main()
