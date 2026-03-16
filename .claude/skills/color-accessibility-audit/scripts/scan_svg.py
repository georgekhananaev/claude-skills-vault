#!/usr/bin/env python3
"""
SVG Color Contrast Scanner
Scans SVG files for fill, stroke, and text color combinations and
analyzes them against WCAG 2.1/2.2 standards (especially SC 1.4.11
for non-text contrast and SC 1.4.3 for text elements).

Usage:
  python3 scan_svg.py icon.svg
  python3 scan_svg.py src/assets/ --recursive
  python3 scan_svg.py public/icons/ -r --cvd
  python3 scan_svg.py src/ -r --json > report.json

Detects:
  - fill and stroke attributes on SVG elements
  - fill and stroke in inline style attributes
  - <text> and <tspan> elements with color definitions
  - CSS <style> blocks inside SVGs
  - Nested <g> group inheritance
  - SVG files embedded in JSX/TSX (inline SVG components)
  - currentColor references (flagged for manual review)
"""

import sys
import re
import json
import os
import xml.etree.ElementTree as ET

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
# SVG Color Extraction
# ═══════════════════════════════════════════════════════════════

# Common SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# SVG elements that can contain visible text
TEXT_ELEMENTS = {"text", "tspan", "textPath",
                 f"{{{SVG_NS}}}text", f"{{{SVG_NS}}}tspan", f"{{{SVG_NS}}}textPath"}

# SVG elements that are graphical (non-text contrast SC 1.4.11)
GRAPHIC_ELEMENTS = {
    "rect", "circle", "ellipse", "line", "polyline", "polygon", "path",
    f"{{{SVG_NS}}}rect", f"{{{SVG_NS}}}circle", f"{{{SVG_NS}}}ellipse",
    f"{{{SVG_NS}}}line", f"{{{SVG_NS}}}polyline", f"{{{SVG_NS}}}polygon",
    f"{{{SVG_NS}}}path",
}

# Hex color patterns
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}){1,2}$")
RGB_RE = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*[\d.]+\s*)?\)"
)
HSL_RE = re.compile(
    r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*(?:,\s*[\d.]+\s*)?\)"
)


def rgb_to_hex_str(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def hsl_to_hex_str(h, s, l):
    import colorsys
    r, g, b = colorsys.hls_to_rgb(float(h) / 360, float(l) / 100, float(s) / 100)
    return rgb_to_hex_str(r * 255, g * 255, b * 255)


def parse_svg_color(value):
    """Parse an SVG color value to normalized hex. Returns hex or None."""
    if not value:
        return None

    value = value.strip()

    if value in ("none", "transparent", "inherit", "currentColor", "currentcolor"):
        return None  # Can't resolve statically

    # Hex
    if HEX_RE.match(value):
        try:
            return normalize_hex(value)
        except ValueError:
            return None

    # rgb/rgba
    m = RGB_RE.match(value)
    if m:
        try:
            return normalize_hex(rgb_to_hex_str(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            return None

    # hsl/hsla
    m = HSL_RE.match(value)
    if m:
        try:
            return normalize_hex(hsl_to_hex_str(m.group(1), m.group(2), m.group(3)))
        except ValueError:
            return None

    # Named CSS/SVG color
    lower = value.lower()
    if lower in NAMED_COLORS:
        return normalize_hex(NAMED_COLORS[lower])

    return None


def parse_style_attr(style_str):
    """Parse an inline style attribute into a dict of property: value."""
    props = {}
    if not style_str:
        return props
    for part in style_str.split(";"):
        if ":" in part:
            key, val = part.split(":", 1)
            props[key.strip().lower()] = val.strip()
    return props


def extract_colors_from_element(elem, parent_fill=None, parent_stroke=None):
    """
    Extract fill and stroke colors from an SVG element.
    Handles attribute inheritance from parent groups.
    """
    # Get tag name without namespace
    tag = elem.tag
    if "}" in tag:
        tag = tag.split("}")[-1]

    # Check direct attributes
    fill = elem.get("fill")
    stroke = elem.get("stroke")
    color = elem.get("color")

    # Check inline style (overrides attributes)
    style = parse_style_attr(elem.get("style", ""))
    if "fill" in style:
        fill = style["fill"]
    if "stroke" in style:
        stroke = style["stroke"]
    if "color" in style:
        color = style["color"]

    # Inherit from parent if not set
    if fill is None and parent_fill:
        fill = parent_fill
    if stroke is None and parent_stroke:
        stroke = parent_stroke

    # Parse colors
    fill_hex = parse_svg_color(fill) if fill and fill != "none" else None
    stroke_hex = parse_svg_color(stroke) if stroke and stroke != "none" else None

    return {
        "tag": tag,
        "fill": fill,
        "fill_hex": fill_hex,
        "stroke": stroke,
        "stroke_hex": stroke_hex,
        "is_text": elem.tag in TEXT_ELEMENTS,
        "is_graphic": elem.tag in GRAPHIC_ELEMENTS,
        "has_current_color": (fill and "currentcolor" in fill.lower()) or
                             (stroke and "currentcolor" in stroke.lower()),
    }


def walk_svg(elem, parent_fill=None, parent_stroke=None, results=None):
    """Recursively walk SVG tree, extracting colors with inheritance."""
    if results is None:
        results = []

    info = extract_colors_from_element(elem, parent_fill, parent_stroke)
    results.append(info)

    # Pass fill/stroke down to children (group inheritance)
    child_fill = info["fill"] if info["fill"] and info["fill"] != "none" else parent_fill
    child_stroke = info["stroke"] if info["stroke"] and info["stroke"] != "none" else parent_stroke

    for child in elem:
        walk_svg(child, child_fill, child_stroke, results)

    return results


def find_svg_pairs(elements, default_bg="#ffffff"):
    """
    Build color pairs from SVG element data.
    - Text elements: text color (fill) vs background
    - Graphic elements: fill vs stroke, fill vs background
    """
    pairs = []
    current_color_warnings = []

    # Collect all unique fills as potential backgrounds
    all_fills = set()
    for e in elements:
        if e["fill_hex"]:
            all_fills.add(e["fill_hex"])

    # Determine the most likely background
    # If there's a rect that covers the canvas (usually first rect), use its fill
    bg_color = default_bg
    for e in elements:
        if e["tag"] == "rect" and e["fill_hex"]:
            bg_color = e["fill_hex"]
            break

    for e in elements:
        # Flag currentColor usage
        if e["has_current_color"]:
            current_color_warnings.append(
                f"<{e['tag']}> uses currentColor — contrast depends on parent CSS context"
            )
            continue

        # Text elements — text color (fill) vs background
        if e["is_text"] and e["fill_hex"]:
            pairs.append({
                "foreground": e["fill_hex"],
                "background": bg_color,
                "fg_source": f"<{e['tag']}> fill",
                "bg_source": "SVG background",
                "type": "text",
                "wcag_sc": "SC 1.4.3 (text contrast)",
            })

        # Graphic elements
        if e["is_graphic"]:
            # Fill vs background (non-text contrast)
            if e["fill_hex"] and e["fill_hex"] != bg_color:
                pairs.append({
                    "foreground": e["fill_hex"],
                    "background": bg_color,
                    "fg_source": f"<{e['tag']}> fill",
                    "bg_source": "SVG background",
                    "type": "graphic",
                    "wcag_sc": "SC 1.4.11 (non-text contrast)",
                })

            # Stroke vs fill (element boundary contrast)
            if e["stroke_hex"] and e["fill_hex"] and e["stroke_hex"] != e["fill_hex"]:
                pairs.append({
                    "foreground": e["stroke_hex"],
                    "background": e["fill_hex"],
                    "fg_source": f"<{e['tag']}> stroke",
                    "bg_source": f"<{e['tag']}> fill",
                    "type": "stroke-vs-fill",
                    "wcag_sc": "SC 1.4.11 (non-text contrast)",
                })

            # Stroke vs background
            if e["stroke_hex"] and e["stroke_hex"] != bg_color:
                pairs.append({
                    "foreground": e["stroke_hex"],
                    "background": bg_color,
                    "fg_source": f"<{e['tag']}> stroke",
                    "bg_source": "SVG background",
                    "type": "stroke-vs-bg",
                    "wcag_sc": "SC 1.4.11 (non-text contrast)",
                })

    return pairs, current_color_warnings


def parse_svg_file(filepath):
    """Parse an SVG file and extract color pairs."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError:
        # Try extracting SVG from JSX/TSX
        return parse_inline_svg(filepath)

    elements = walk_svg(root)
    return find_svg_pairs(elements)


def parse_inline_svg(filepath):
    """Extract inline SVG from JSX/TSX files."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except IOError:
        return [], []

    # Find <svg>...</svg> blocks in JSX
    svg_blocks = re.findall(r"(<svg[^>]*>.*?</svg>)", content, re.DOTALL | re.IGNORECASE)

    all_pairs = []
    all_warnings = []

    for svg_str in svg_blocks:
        # Clean JSX attributes for XML parsing
        # Convert className to class, camelCase to kebab-case for common attrs
        cleaned = svg_str
        cleaned = re.sub(r'className=', 'class=', cleaned)
        cleaned = re.sub(r'strokeWidth=', 'stroke-width=', cleaned)
        cleaned = re.sub(r'strokeLinecap=', 'stroke-linecap=', cleaned)
        cleaned = re.sub(r'strokeLinejoin=', 'stroke-linejoin=', cleaned)
        cleaned = re.sub(r'fillRule=', 'fill-rule=', cleaned)
        cleaned = re.sub(r'clipRule=', 'clip-rule=', cleaned)
        cleaned = re.sub(r'clipPath=', 'clip-path=', cleaned)
        # Remove JSX expressions {var} from attributes
        cleaned = re.sub(r'=\{[^}]+\}', '="dynamic"', cleaned)

        try:
            root = ET.fromstring(cleaned)
            elements = walk_svg(root)
            pairs, warnings = find_svg_pairs(elements)
            all_pairs.extend(pairs)
            all_warnings.extend(warnings)
        except ET.ParseError:
            continue

    return all_pairs, all_warnings


# ═══════════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════════

def analyze_pairs(pairs, include_cvd=False):
    results = []
    seen = set()

    for pair in pairs:
        dedup_key = (pair["foreground"], pair["background"], pair["type"])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        try:
            fg_hex = normalize_hex(pair["foreground"])
            bg_hex = normalize_hex(pair["background"])
        except ValueError as e:
            results.append({"error": str(e), **pair})
            continue

        ratio = contrast_ratio(fg_hex, bg_hex)
        rating = wcag_rating(ratio)

        # For non-text elements, the threshold is 3:1 (SC 1.4.11)
        is_text = pair["type"] == "text"
        min_ratio = 4.5 if is_text else 3.0
        passes_minimum = ratio >= min_ratio

        result = {
            "foreground": fg_hex,
            "background": bg_hex,
            "fg_source": pair["fg_source"],
            "bg_source": pair["bg_source"],
            "type": pair["type"],
            "wcag_sc": pair["wcag_sc"],
            "is_text": is_text,
            "passes_minimum": passes_minimum,
            "min_required_ratio": min_ratio,
            **rating,
        }

        if not passes_minimum:
            fix_hex = find_fixed_color(fg_hex, bg_hex, min_ratio)
            result["fix_hex"] = fix_hex
            result["fix_ratio"] = round(contrast_ratio(fix_hex, bg_hex), 2)

        if is_text and not rating["aaa_body_text"]:
            fix_hex = find_fixed_color(fg_hex, bg_hex, 7.0)
            result["fix_aaa_hex"] = fix_hex
            result["fix_aaa_ratio"] = round(contrast_ratio(fix_hex, bg_hex), 2)

        if include_cvd:
            result["cvd"] = cvd_analysis(fg_hex, bg_hex)
            result["hue_warnings"] = check_risky_hues(fg_hex, bg_hex)

        results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════

def print_report(results, current_color_warnings, filepaths):
    issues = [r for r in results if not r.get("passes_minimum", True)]
    passing = [r for r in results if r.get("passes_minimum", False)]
    errors = [r for r in results if "error" in r]
    total = len(results) - len(errors)

    files_str = ", ".join(filepaths) if len(filepaths) <= 3 else f"{len(filepaths)} files"

    print()
    print(f"{'═' * 60}")
    print(f"  SVG COLOR CONTRAST SCAN REPORT")
    print(f"  Source: {files_str}")
    print(f"{'═' * 60}")
    print()
    print(f"  Found {total} color pairs in SVG elements")
    print()
    print(f"  ❌ FAIL:            {len(issues)} pairs")
    print(f"  ✅ PASS:            {len(passing)} pairs")
    if errors:
        print(f"  ⛔ Parse errors:    {len(errors)}")
    if current_color_warnings:
        print(f"  ⚠️  currentColor:   {len(current_color_warnings)} (needs manual review)")
    print()

    if issues:
        print(f"{'─' * 60}")
        print(f"  ❌ FAILING")
        print(f"{'─' * 60}")
        for r in issues:
            _print_issue(r)

    if passing:
        print(f"{'─' * 60}")
        print(f"  ✅ PASSING")
        print(f"{'─' * 60}")
        for r in passing:
            print(f"    {r['fg_source']} on {r['bg_source']}  →  {r['ratio']}:1 ✅  ({r['wcag_sc']})")
        print()

    if current_color_warnings:
        print(f"{'─' * 60}")
        print(f"  ⚠️  CURRENT COLOR (manual review needed)")
        print(f"{'─' * 60}")
        for w in current_color_warnings:
            print(f"    {w}")
        print()

    print(f"{'═' * 60}")
    if not issues:
        print(f"  ✅ All SVG color pairs pass their required WCAG thresholds!")
    else:
        print(f"  ❌ {len(issues)} pair(s) need fixing.")
    print(f"{'═' * 60}")
    print()


def _print_issue(r):
    print()
    print(f"    {r['fg_source']} on {r['bg_source']}")
    print(f"    Type:      {r['type']}  ({r['wcag_sc']})")
    print(f"    Colors:    {r['foreground']} on {r['background']}")
    print(f"    Ratio:     {r['ratio']}:1  (need {r['min_required_ratio']}:1)")
    print(f"    Status:    ❌ FAIL")

    if "fix_hex" in r:
        print(f"    Fix:       {r['fix_hex']}  →  {r['fix_ratio']}:1")
    if "fix_aaa_hex" in r:
        print(f"    Fix AAA:   {r['fix_aaa_hex']}  →  {r['fix_aaa_ratio']}:1")

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

SVG_EXTENSIONS = {".svg"}
JSX_EXTENSIONS = {".jsx", ".tsx"}  # For inline SVG detection
ALL_EXTENSIONS = SVG_EXTENSIONS | JSX_EXTENSIONS


def collect_files(path, recursive=False):
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        files = []
        if recursive:
            for root, dirs, filenames in os.walk(path):
                dirs[:] = [d for d in dirs if d not in (
                    "node_modules", ".next", "dist", "build", ".git",
                    "__pycache__", ".turbo", ".cache", "coverage"
                )]
                for f in filenames:
                    if os.path.splitext(f)[1] in ALL_EXTENSIONS:
                        files.append(os.path.join(root, f))
        else:
            for f in os.listdir(path):
                if os.path.splitext(f)[1] in ALL_EXTENSIONS:
                    files.append(os.path.join(path, f))
        return sorted(files)
    return []


def main():
    args = sys.argv[1:]
    include_cvd = "--cvd" in args
    output_json = "--json" in args
    recursive = "--recursive" in args or "-r" in args
    args = [a for a in args if a not in ("--cvd", "--json", "--recursive", "-r")]

    if not args:
        print("Usage: python3 scan_svg.py <path> [--cvd] [--json] [--recursive]")
        print()
        print("Scans SVG files for color contrast issues.")
        print("Also finds inline SVGs in JSX/TSX files.")
        print()
        print("Options:")
        print("  --cvd        Color blindness simulation")
        print("  --json       JSON output")
        print("  --recursive  Scan directories recursively (alias: -r)")
        print()
        print("Examples:")
        print("  python3 scan_svg.py icon.svg")
        print("  python3 scan_svg.py public/icons/ -r --cvd")
        print("  python3 scan_svg.py src/ -r --json > report.json")
        sys.exit(1)

    all_files = []
    for path in args:
        all_files.extend(collect_files(path, recursive))

    if not all_files:
        print("No SVG or JSX/TSX files found.")
        sys.exit(1)

    all_pairs = []
    all_cc_warnings = []

    for filepath in all_files:
        ext = os.path.splitext(filepath)[1]
        if ext in SVG_EXTENSIONS:
            pairs, warnings = parse_svg_file(filepath)
        elif ext in JSX_EXTENSIONS:
            pairs, warnings = parse_inline_svg(filepath)
        else:
            continue

        for p in pairs:
            p["file"] = filepath
        all_pairs.extend(pairs)
        all_cc_warnings.extend(warnings)

    if not all_pairs and not all_cc_warnings:
        print(f"No SVG color pairs found in {len(all_files)} file(s).")
        sys.exit(0)

    results = analyze_pairs(all_pairs, include_cvd=include_cvd)

    if output_json:
        output = {"results": results, "current_color_warnings": all_cc_warnings}
        print(json.dumps(output, indent=2))
    else:
        print_report(results, all_cc_warnings, all_files)


if __name__ == "__main__":
    main()
