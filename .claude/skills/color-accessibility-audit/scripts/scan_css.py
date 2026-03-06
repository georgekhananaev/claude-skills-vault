#!/usr/bin/env python3
"""
CSS Color Contrast Scanner
Scans a CSS file (e.g., global.css, styles.css, tailwind output) for all
text/background color pairs and reports WCAG contrast issues.

Usage:
  python3 scan_css.py path/to/global.css
  python3 scan_css.py path/to/global.css --cvd
  python3 scan_css.py path/to/global.css --json
  python3 scan_css.py path/to/global.css --json --cvd > report.json

Features:
  - Parses CSS rules and extracts color + background-color pairs per selector
  - Resolves CSS custom properties (--var) defined in :root or other blocks
  - Detects hsl(), rgb(), hex, and named colors
  - Inherits background from parent selectors when possible
  - Flags every pair that fails WCAG AA or AAA
  - Provides auto-fix suggestions (The Fixer)
  - Optional color blindness simulation (--cvd)
"""

import sys
import re
import json
import os

# Import the analysis engine from contrast_check.py
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
# CSS Color Extraction
# ═══════════════════════════════════════════════════════════════

# Match hex colors: #rgb, #rrggbb, #rrggbbaa
HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}){1,2}\b")

# Match rgb/rgba: rgb(R, G, B) or rgba(R, G, B, A)
RGB_RE = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*[\d.]+\s*)?\)"
)

# Match hsl/hsla: hsl(H, S%, L%) or hsla(H, S%, L%, A)
HSL_RE = re.compile(
    r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*(?:,\s*[\d.]+\s*)?\)"
)

# Match CSS custom property usage: var(--name) or var(--name, fallback)
VAR_RE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)")

# Match CSS custom property definition: --name: value
VAR_DEF_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")

# CSS properties that define text color
TEXT_PROPS = {"color"}

# CSS properties that define background color
BG_PROPS = {"background-color", "background"}

# CSS properties for borders (non-text contrast)
BORDER_PROPS = {"border-color", "border", "border-top-color", "border-bottom-color",
                "border-left-color", "border-right-color", "outline-color"}


def rgb_to_hex_str(r, g, b):
    """Convert RGB integers to hex string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def hsl_to_hex_str(h, s, l):
    """Convert HSL values to hex string."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(float(h) / 360, float(l) / 100, float(s) / 100)
    return rgb_to_hex_str(r * 255, g * 255, b * 255)


def extract_color_value(value_str, css_vars=None):
    """
    Extract a single color from a CSS property value string.
    Returns a normalized hex color or None.
    """
    if css_vars is None:
        css_vars = {}

    value_str = value_str.strip()

    # Resolve var() references
    var_match = VAR_RE.search(value_str)
    if var_match:
        var_name = var_match.group(1)
        fallback = var_match.group(2)
        if var_name in css_vars:
            resolved = css_vars[var_name]
            result = extract_color_value(resolved, css_vars)
            if result:
                return result
        if fallback:
            result = extract_color_value(fallback.strip(), css_vars)
            if result:
                return result
        return None

    # Try hsl/hsla
    hsl_match = HSL_RE.search(value_str)
    if hsl_match:
        h, s, l = hsl_match.group(1), hsl_match.group(2), hsl_match.group(3)
        try:
            return normalize_hex(hsl_to_hex_str(h, s, l))
        except ValueError:
            pass

    # Try rgb/rgba
    rgb_match = RGB_RE.search(value_str)
    if rgb_match:
        r, g, b = rgb_match.group(1), rgb_match.group(2), rgb_match.group(3)
        try:
            return normalize_hex(rgb_to_hex_str(int(r), int(g), int(b)))
        except ValueError:
            pass

    # Try hex
    hex_match = HEX_RE.search(value_str)
    if hex_match:
        try:
            return normalize_hex(hex_match.group(0))
        except ValueError:
            pass

    # Try named color
    lower = value_str.lower().strip()
    # Handle compound values like "solid red" by checking each word
    for word in lower.split():
        if word in NAMED_COLORS:
            return normalize_hex(NAMED_COLORS[word])

    # Special cases
    if lower == "transparent" or lower == "inherit" or lower == "initial" or lower == "unset":
        return None

    return None


def strip_comments(css_text):
    """Remove CSS comments."""
    return re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)


def parse_css_blocks(css_text):
    """
    Parse CSS into a list of (selector, properties_dict) tuples.
    Handles nested @media blocks by flattening selectors.
    """
    css_text = strip_comments(css_text)
    blocks = []

    # First, extract CSS variable definitions from :root or *
    var_blocks = re.findall(r"(?::root|html|\*)\s*\{([^}]+)\}", css_text, re.DOTALL)
    css_vars = {}
    for block_body in var_blocks:
        for match in VAR_DEF_RE.finditer(block_body):
            css_vars[match.group(1)] = match.group(2).strip()

    # Flatten @media and @layer blocks — extract inner rules
    # Simple approach: remove the outer @-rule wrapper
    def flatten_at_rules(text):
        result = text
        # Repeatedly extract content from @media, @layer, @supports blocks
        pattern = r"@(?:media|layer|supports)[^{]*\{((?:[^{}]|\{[^{}]*\})*)\}"
        while re.search(pattern, result):
            result = re.sub(pattern, r"\1", result)
        return result

    flat_css = flatten_at_rules(css_text)

    # Parse selector { properties } blocks
    rule_re = re.compile(r"([^{}@]+?)\s*\{([^}]*)\}", re.DOTALL)
    for match in rule_re.finditer(flat_css):
        selector = match.group(1).strip()
        body = match.group(2).strip()

        # Skip @-rules that slipped through
        if selector.startswith("@"):
            continue

        # Also extract any local CSS variable definitions
        for var_match in VAR_DEF_RE.finditer(body):
            css_vars[var_match.group(1)] = var_match.group(2).strip()

        # Parse properties
        props = {}
        for prop_match in re.finditer(r"([\w-]+)\s*:\s*([^;]+);", body):
            prop_name = prop_match.group(1).strip().lower()
            prop_value = prop_match.group(2).strip()
            props[prop_name] = prop_value

        if props:
            blocks.append((selector, props))

    return blocks, css_vars


def find_color_pairs(blocks, css_vars):
    """
    Analyze CSS blocks to find text/background color pairs.
    Returns a list of issue dicts.
    """
    pairs = []

    # Track known backgrounds for common selectors (simple inheritance)
    known_backgrounds = {}
    # Defaults: assume white background for html/body/:root if not specified
    default_bg = "#ffffff"

    for selector, props in blocks:
        text_color = None
        bg_color = None
        border_colors = []

        for prop_name, prop_value in props.items():
            if prop_name in TEXT_PROPS:
                text_color = extract_color_value(prop_value, css_vars)
            elif prop_name in BG_PROPS:
                color = extract_color_value(prop_value, css_vars)
                if color:
                    bg_color = color
            elif prop_name in BORDER_PROPS:
                color = extract_color_value(prop_value, css_vars)
                if color:
                    border_colors.append(color)

        # Store known backgrounds for inheritance
        if bg_color:
            # Normalize selector for matching
            base_sel = selector.split(",")[0].strip().split(":")[0].strip()
            known_backgrounds[base_sel] = bg_color

        # Try to infer background via simple parent matching
        if text_color and not bg_color:
            # Try to find a parent background
            base = selector.split(",")[0].strip()
            parts = re.split(r"[\s>+~]+", base)
            # Walk up the selector chain
            for i in range(len(parts) - 1, -1, -1):
                parent = parts[i].split(":")[0].split(".")[0].split("#")[0].strip()
                if parent in known_backgrounds:
                    bg_color = known_backgrounds[parent]
                    break

        # Fallback to default background
        if text_color and not bg_color:
            bg_color = default_bg

        # Update default background if html/body is explicitly set
        base_element = selector.split(",")[0].strip().split(":")[0].split(".")[0].strip().lower()
        if base_element in ("html", "body", ":root") and bg_color:
            default_bg = bg_color

        # Record the pair if we have a text color
        if text_color:
            pairs.append({
                "selector": selector,
                "text_color": text_color,
                "bg_color": bg_color,
                "source": "color + background-color",
            })

        # Also check border colors against the background (non-text contrast SC 1.4.11)
        if border_colors and bg_color:
            for bc in border_colors:
                pairs.append({
                    "selector": selector,
                    "text_color": bc,
                    "bg_color": bg_color,
                    "source": "border vs background (SC 1.4.11)",
                })

    return pairs


# ═══════════════════════════════════════════════════════════════
# Analysis & Reporting
# ═══════════════════════════════════════════════════════════════

def analyze_css_pairs(pairs, include_cvd=False):
    """Run full contrast analysis on each extracted pair."""
    results = []

    for pair in pairs:
        try:
            text_hex = normalize_hex(pair["text_color"])
            bg_hex = normalize_hex(pair["bg_color"])
        except ValueError as e:
            results.append({
                "selector": pair["selector"],
                "error": str(e),
            })
            continue

        ratio = contrast_ratio(text_hex, bg_hex)
        rating = wcag_rating(ratio)

        result = {
            "selector": pair["selector"],
            "text_color": text_hex,
            "background_color": bg_hex,
            "source": pair["source"],
            **rating,
        }

        # The Fixer
        if not rating["aa_body_text"]:
            fix = find_fixed_color(text_hex, bg_hex, 4.5)
            result["fix_aa"] = fix
            result["fix_aa_ratio"] = round(contrast_ratio(fix, bg_hex), 2)
        if not rating["aaa_body_text"]:
            fix = find_fixed_color(text_hex, bg_hex, 7.0)
            result["fix_aaa"] = fix
            result["fix_aaa_ratio"] = round(contrast_ratio(fix, bg_hex), 2)

        # CVD
        if include_cvd:
            result["cvd"] = cvd_analysis(text_hex, bg_hex)
            result["hue_warnings"] = check_risky_hues(text_hex, bg_hex)

        results.append(result)

    return results


def print_report(results, filepath):
    """Print a human-readable report."""
    issues = [r for r in results if not r.get("aa_body_text", True)]
    warnings = [r for r in results if r.get("aa_body_text", False) and not r.get("aaa_body_text", True)]
    passing = [r for r in results if r.get("aaa_body_text", False)]
    errors = [r for r in results if "error" in r]

    total = len(results) - len(errors)

    print()
    print(f"{'═' * 60}")
    print(f"  COLOR CONTRAST SCAN REPORT")
    print(f"  File: {filepath}")
    print(f"{'═' * 60}")
    print()
    print(f"  Found {total} color pairs across {len(set(r.get('selector','') for r in results))} selectors")
    print()
    print(f"  ❌ FAIL AA:         {len(issues)} pairs")
    print(f"  ⚠️  Pass AA only:   {len(warnings)} pairs")
    print(f"  ✅ Pass AAA:        {len(passing)} pairs")
    if errors:
        print(f"  ⛔ Parse errors:    {len(errors)}")
    print()

    # Show failures first (most important)
    if issues:
        print(f"{'─' * 60}")
        print(f"  ❌ FAILING PAIRS (below AA 4.5:1)")
        print(f"{'─' * 60}")
        for r in issues:
            _print_issue(r)

    # Show AA-only (pass AA but not AAA)
    if warnings:
        print(f"{'─' * 60}")
        print(f"  ⚠️  AA ONLY (pass AA but fail AAA 7:1)")
        print(f"{'─' * 60}")
        for r in warnings:
            _print_issue(r)

    # Show passing (briefly)
    if passing:
        print(f"{'─' * 60}")
        print(f"  ✅ PASSING AAA")
        print(f"{'─' * 60}")
        for r in passing:
            print(f"    {r['selector']}")
            print(f"      {r['text_color']} on {r['background_color']}  →  {r['ratio']}:1 ✅")
            print()

    if errors:
        print(f"{'─' * 60}")
        print(f"  ⛔ ERRORS")
        print(f"{'─' * 60}")
        for r in errors:
            print(f"    {r['selector']}: {r['error']}")
        print()

    # Summary
    print(f"{'═' * 60}")
    if not issues:
        print(f"  ✅ All color pairs pass WCAG AA!")
        if not warnings:
            print(f"  ✅ All color pairs also pass WCAG AAA!")
    else:
        print(f"  ❌ {len(issues)} pair(s) need fixing to meet WCAG AA.")
        print(f"     The suggested fix hex codes above are ready to copy-paste.")
    print(f"{'═' * 60}")
    print()


def _print_issue(r):
    """Print a single issue with full details."""
    print()
    print(f"    Selector:   {r['selector']}")
    print(f"    Source:      {r['source']}")
    print(f"    Text:        {r['text_color']}")
    print(f"    Background:  {r['background_color']}")
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
        for cvd in r["cvd"]:
            icon = icons.get(cvd["type"], "•")
            risk_str = {"critical": "❌ CRITICAL", "high": "⚠️  HIGH", "warning": "⚠️  WARN", "ok": "✅ OK"}
            print(f"    {icon} {cvd['type']:15s} {cvd['simulated_ratio']:5.2f}:1  "
                  f"ΔE={cvd['delta_e']:5.1f}  {risk_str.get(cvd['risk'], cvd['risk'])}")

    if r.get("hue_warnings"):
        for w in r["hue_warnings"]:
            print(f"    ⚠️  {w}")

    print()


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    include_cvd = "--cvd" in args
    output_json = "--json" in args
    args = [a for a in args if a not in ("--cvd", "--json")]

    if not args:
        print("Usage: python3 scan_css.py <path/to/file.css> [--cvd] [--json]")
        print()
        print("Scans a CSS file for color contrast issues against WCAG 2.1/2.2.")
        print()
        print("Options:")
        print("  --cvd   Include color blindness simulation")
        print("  --json  Output structured JSON report")
        print()
        print("Examples:")
        print("  python3 scan_css.py global.css")
        print("  python3 scan_css.py src/styles/global.css --cvd")
        print("  python3 scan_css.py theme.css --json > report.json")
        sys.exit(1)

    filepath = args[0]
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        css_text = f.read()

    # Parse
    blocks, css_vars = parse_css_blocks(css_text)

    if not blocks:
        print(f"No CSS rules found in {filepath}")
        sys.exit(0)

    # Extract pairs
    pairs = find_color_pairs(blocks, css_vars)

    if not pairs:
        print(f"No text/background color pairs found in {filepath}")
        print("This might mean colors are defined via JavaScript, Tailwind utilities, or external stylesheets.")
        sys.exit(0)

    # Deduplicate identical pairs (same colors, different selectors get merged)
    seen = set()
    unique_pairs = []
    for p in pairs:
        key = (p["text_color"], p["bg_color"], p["selector"])
        if key not in seen:
            seen.add(key)
            unique_pairs.append(p)

    # Analyze
    results = analyze_css_pairs(unique_pairs, include_cvd=include_cvd)

    # Output
    if output_json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, filepath)


if __name__ == "__main__":
    main()
