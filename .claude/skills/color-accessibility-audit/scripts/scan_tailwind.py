#!/usr/bin/env python3
"""
Tailwind CSS className Scanner
Scans JSX/TSX files for Tailwind utility classes (text-*, bg-*) and
analyzes text/background contrast pairs against WCAG 2.1/2.2 standards.

Usage:
  python3 scan_tailwind.py src/components/Button.tsx
  python3 scan_tailwind.py src/ --recursive
  python3 scan_tailwind.py src/ --recursive --cvd
  python3 scan_tailwind.py src/ -r --json > report.json
  python3 scan_tailwind.py src/ -r --fix   (outputs suggested class replacements)

Detects:
  - className="text-gray-400 bg-white"
  - className={`text-${color} bg-slate-100`}
  - clsx('text-red-500', 'bg-green-200')
  - cn('text-muted-foreground', 'bg-card')
  - tw`text-blue-400 bg-white`
  - Conditional: isActive ? 'text-white bg-blue-600' : 'text-gray-500 bg-gray-100'
  - Dark mode: dark:text-gray-300 dark:bg-slate-900
  - Hover/focus: hover:text-blue-300 hover:bg-blue-50
"""

import sys
import re
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from contrast_check import (
    normalize_hex,
    contrast_ratio,
    wcag_rating,
    find_fixed_color,
    cvd_analysis,
    check_risky_hues,
)

# ═══════════════════════════════════════════════════════════════
# Tailwind v3 Default Color Palette → Hex
# ═══════════════════════════════════════════════════════════════

TAILWIND_COLORS = {
    # Special
    "white": "#ffffff", "black": "#000000", "transparent": None, "current": None,

    # Gray
    "gray-50": "#f9fafb", "gray-100": "#f3f4f6", "gray-200": "#e5e7eb",
    "gray-300": "#d1d5db", "gray-400": "#9ca3af", "gray-500": "#6b7280",
    "gray-600": "#4b5563", "gray-700": "#374151", "gray-800": "#1f2937",
    "gray-900": "#111827", "gray-950": "#030712",

    # Slate
    "slate-50": "#f8fafc", "slate-100": "#f1f5f9", "slate-200": "#e2e8f0",
    "slate-300": "#cbd5e1", "slate-400": "#94a3b8", "slate-500": "#64748b",
    "slate-600": "#475569", "slate-700": "#334155", "slate-800": "#1e293b",
    "slate-900": "#0f172a", "slate-950": "#020617",

    # Zinc
    "zinc-50": "#fafafa", "zinc-100": "#f4f4f5", "zinc-200": "#e4e4e7",
    "zinc-300": "#d4d4d8", "zinc-400": "#a1a1aa", "zinc-500": "#71717a",
    "zinc-600": "#52525b", "zinc-700": "#3f3f46", "zinc-800": "#27272a",
    "zinc-900": "#18181b", "zinc-950": "#09090b",

    # Neutral
    "neutral-50": "#fafafa", "neutral-100": "#f5f5f5", "neutral-200": "#e5e5e5",
    "neutral-300": "#d4d4d4", "neutral-400": "#a3a3a3", "neutral-500": "#737373",
    "neutral-600": "#525252", "neutral-700": "#404040", "neutral-800": "#262626",
    "neutral-900": "#171717", "neutral-950": "#0a0a0a",

    # Stone
    "stone-50": "#fafaf9", "stone-100": "#f5f5f4", "stone-200": "#e7e5e4",
    "stone-300": "#d6d3d1", "stone-400": "#a8a29e", "stone-500": "#78716c",
    "stone-600": "#57534e", "stone-700": "#44403c", "stone-800": "#292524",
    "stone-900": "#1c1917", "stone-950": "#0c0a09",

    # Red
    "red-50": "#fef2f2", "red-100": "#fee2e2", "red-200": "#fecaca",
    "red-300": "#fca5a5", "red-400": "#f87171", "red-500": "#ef4444",
    "red-600": "#dc2626", "red-700": "#b91c1c", "red-800": "#991b1b",
    "red-900": "#7f1d1d", "red-950": "#450a0a",

    # Orange
    "orange-50": "#fff7ed", "orange-100": "#ffedd5", "orange-200": "#fed7aa",
    "orange-300": "#fdba74", "orange-400": "#fb923c", "orange-500": "#f97316",
    "orange-600": "#ea580c", "orange-700": "#c2410c", "orange-800": "#9a3412",
    "orange-900": "#7c2d12", "orange-950": "#431407",

    # Amber
    "amber-50": "#fffbeb", "amber-100": "#fef3c7", "amber-200": "#fde68a",
    "amber-300": "#fcd34d", "amber-400": "#fbbf24", "amber-500": "#f59e0b",
    "amber-600": "#d97706", "amber-700": "#b45309", "amber-800": "#92400e",
    "amber-900": "#78350f", "amber-950": "#451a03",

    # Yellow
    "yellow-50": "#fefce8", "yellow-100": "#fef9c3", "yellow-200": "#fef08a",
    "yellow-300": "#fde047", "yellow-400": "#facc15", "yellow-500": "#eab308",
    "yellow-600": "#ca8a04", "yellow-700": "#a16207", "yellow-800": "#854d0e",
    "yellow-900": "#713f12", "yellow-950": "#422006",

    # Lime
    "lime-50": "#f7fee7", "lime-100": "#ecfccb", "lime-200": "#d9f99d",
    "lime-300": "#bef264", "lime-400": "#a3e635", "lime-500": "#84cc16",
    "lime-600": "#65a30d", "lime-700": "#4d7c0f", "lime-800": "#3f6212",
    "lime-900": "#365314", "lime-950": "#1a2e05",

    # Green
    "green-50": "#f0fdf4", "green-100": "#dcfce7", "green-200": "#bbf7d0",
    "green-300": "#86efac", "green-400": "#4ade80", "green-500": "#22c55e",
    "green-600": "#16a34a", "green-700": "#15803d", "green-800": "#166534",
    "green-900": "#14532d", "green-950": "#052e16",

    # Emerald
    "emerald-50": "#ecfdf5", "emerald-100": "#d1fae5", "emerald-200": "#a7f3d0",
    "emerald-300": "#6ee7b7", "emerald-400": "#34d399", "emerald-500": "#10b981",
    "emerald-600": "#059669", "emerald-700": "#047857", "emerald-800": "#065f46",
    "emerald-900": "#064e3b", "emerald-950": "#022c22",

    # Teal
    "teal-50": "#f0fdfa", "teal-100": "#ccfbf1", "teal-200": "#99f6e4",
    "teal-300": "#5eead4", "teal-400": "#2dd4bf", "teal-500": "#14b8a6",
    "teal-600": "#0d9488", "teal-700": "#0f766e", "teal-800": "#115e59",
    "teal-900": "#134e4a", "teal-950": "#042f2e",

    # Cyan
    "cyan-50": "#ecfeff", "cyan-100": "#cffafe", "cyan-200": "#a5f3fc",
    "cyan-300": "#67e8f9", "cyan-400": "#22d3ee", "cyan-500": "#06b6d4",
    "cyan-600": "#0891b2", "cyan-700": "#0e7490", "cyan-800": "#155e75",
    "cyan-900": "#164e63", "cyan-950": "#083344",

    # Sky
    "sky-50": "#f0f9ff", "sky-100": "#e0f2fe", "sky-200": "#bae6fd",
    "sky-300": "#7dd3fc", "sky-400": "#38bdf8", "sky-500": "#0ea5e9",
    "sky-600": "#0284c7", "sky-700": "#0369a1", "sky-800": "#075985",
    "sky-900": "#0c4a6e", "sky-950": "#082f49",

    # Blue
    "blue-50": "#eff6ff", "blue-100": "#dbeafe", "blue-200": "#bfdbfe",
    "blue-300": "#93c5fd", "blue-400": "#60a5fa", "blue-500": "#3b82f6",
    "blue-600": "#2563eb", "blue-700": "#1d4ed8", "blue-800": "#1e40af",
    "blue-900": "#1e3a8a", "blue-950": "#172554",

    # Indigo
    "indigo-50": "#eef2ff", "indigo-100": "#e0e7ff", "indigo-200": "#c7d2fe",
    "indigo-300": "#a5b4fc", "indigo-400": "#818cf8", "indigo-500": "#6366f1",
    "indigo-600": "#4f46e5", "indigo-700": "#4338ca", "indigo-800": "#3730a3",
    "indigo-900": "#312e81", "indigo-950": "#1e1b4b",

    # Violet
    "violet-50": "#f5f3ff", "violet-100": "#ede9fe", "violet-200": "#ddd6fe",
    "violet-300": "#c4b5fd", "violet-400": "#a78bfa", "violet-500": "#8b5cf6",
    "violet-600": "#7c3aed", "violet-700": "#6d28d9", "violet-800": "#5b21b6",
    "violet-900": "#4c1d95", "violet-950": "#2e1065",

    # Purple
    "purple-50": "#faf5ff", "purple-100": "#f3e8ff", "purple-200": "#e9d5ff",
    "purple-300": "#d8b4fe", "purple-400": "#c084fc", "purple-500": "#a855f7",
    "purple-600": "#9333ea", "purple-700": "#7e22ce", "purple-800": "#6b21a8",
    "purple-900": "#581c87", "purple-950": "#3b0764",

    # Fuchsia
    "fuchsia-50": "#fdf4ff", "fuchsia-100": "#fae8ff", "fuchsia-200": "#f5d0fe",
    "fuchsia-300": "#f0abfc", "fuchsia-400": "#e879f9", "fuchsia-500": "#d946ef",
    "fuchsia-600": "#c026d3", "fuchsia-700": "#a21caf", "fuchsia-800": "#86198f",
    "fuchsia-900": "#701a75", "fuchsia-950": "#4a044e",

    # Pink
    "pink-50": "#fdf2f8", "pink-100": "#fce7f3", "pink-200": "#fbcfe8",
    "pink-300": "#f9a8d4", "pink-400": "#f472b6", "pink-500": "#ec4899",
    "pink-600": "#db2777", "pink-700": "#be185d", "pink-800": "#9d174d",
    "pink-900": "#831843", "pink-950": "#500724",

    # Rose
    "rose-50": "#fff1f2", "rose-100": "#ffe4e6", "rose-200": "#fecdd3",
    "rose-300": "#fda4af", "rose-400": "#fb7185", "rose-500": "#f43f5e",
    "rose-600": "#e11d48", "rose-700": "#be123c", "rose-800": "#9f1239",
    "rose-900": "#881337", "rose-950": "#4c0519",
}


def resolve_tw_color(class_suffix):
    """Resolve a Tailwind color suffix to hex. Returns hex or None."""
    suffix = class_suffix.lower()
    if suffix in TAILWIND_COLORS:
        return TAILWIND_COLORS[suffix]
    return None


# ═══════════════════════════════════════════════════════════════
# Tailwind Class Extraction from JSX/TSX
# ═══════════════════════════════════════════════════════════════

# Matches any string literal content (single, double, backtick)
STRING_CONTENT_RE = re.compile(
    r"""(?:className|class)\s*=\s*(?:"""
    r"""(?:\{[^}]*\})|"""              # className={...}
    r"""(?:"[^"]*")|"""                # className="..."
    r"""(?:'[^']*'))""",               # className='...'
    re.DOTALL,
)

# Also match clsx(), cn(), twMerge(), classNames(), cva() etc.
UTILITY_FN_RE = re.compile(
    r"""(?:clsx|cn|twMerge|classNames|cva|tw)\s*\(([^)]{0,2000})\)""",
    re.DOTALL,
)

# Match tw`` tagged template literals
TW_TEMPLATE_RE = re.compile(
    r"""tw\s*`([^`]*)`""",
    re.DOTALL,
)

# Extract text-* and bg-* classes (with optional variant prefixes like dark:, hover:, etc.)
TEXT_CLASS_RE = re.compile(
    r"""(?:^|\s|'|"|`)"""
    r"""((?:(?:dark|hover|focus|active|group-hover|disabled|placeholder|sm|md|lg|xl|2xl):)*"""
    r"""text-([\w]+-\d+|white|black|inherit|transparent|current))"""
    r"""(?=\s|'|"|`|$)"""
)

BG_CLASS_RE = re.compile(
    r"""(?:^|\s|'|"|`)"""
    r"""((?:(?:dark|hover|focus|active|group-hover|disabled|placeholder|sm|md|lg|xl|2xl):)*"""
    r"""bg-([\w]+-\d+|white|black|inherit|transparent|current))"""
    r"""(?=\s|'|"|`|$)"""
)

BORDER_CLASS_RE = re.compile(
    r"""(?:^|\s|'|"|`)"""
    r"""((?:(?:dark|hover|focus|active|group-hover|disabled|sm|md|lg|xl|2xl):)*"""
    r"""border-([\w]+-\d+|white|black|inherit|transparent|current))"""
    r"""(?=\s|'|"|`|$)"""
)


def extract_class_strings(code):
    """Extract all string content from className attributes and utility functions."""
    strings = []

    # className="..." or className={'...'} or className={`...`}
    for m in STRING_CONTENT_RE.finditer(code):
        content = m.group(0)
        line = code[:m.start()].count("\n") + 1
        # Extract string contents from within
        for s in re.findall(r"""['"`]([^'"`]+)['"`]""", content):
            strings.append((s, line))

    # clsx(), cn(), twMerge(), etc.
    for m in UTILITY_FN_RE.finditer(code):
        content = m.group(1)
        line = code[:m.start()].count("\n") + 1
        for s in re.findall(r"""['"`]([^'"`]+)['"`]""", content):
            strings.append((s, line))

    # tw`...` tagged template literals
    for m in TW_TEMPLATE_RE.finditer(code):
        content = m.group(1)
        line = code[:m.start()].count("\n") + 1
        strings.append((content, line))

    # Also catch ternary patterns: condition ? 'classes' : 'classes'
    ternary_re = re.compile(r"""[?:]\s*['"`]([^'"`]+)['"`]""")
    for m in ternary_re.finditer(code):
        content = m.group(1)
        line = code[:m.start()].count("\n") + 1
        strings.append((content, line))

    return strings


def extract_tw_pairs(class_strings):
    """
    From a list of (class_string, line) tuples, extract text/bg color pairs.
    Groups text-* and bg-* classes that appear in the same string (same element).
    """
    raw_pairs = []

    for class_str, line in class_strings:
        # Separate by variant prefix (base, dark, hover, etc.)
        variant_groups = {}

        for m in TEXT_CLASS_RE.finditer(class_str):
            full_class = m.group(1)
            color_suffix = m.group(2)
            # Determine variant
            variant = "base"
            if "dark:" in full_class:
                variant = "dark"
            elif "hover:" in full_class:
                variant = "hover"
            elif "focus:" in full_class:
                variant = "focus"

            if variant not in variant_groups:
                variant_groups[variant] = {"text": [], "bg": [], "border": []}
            hex_color = resolve_tw_color(color_suffix)
            if hex_color:
                variant_groups[variant]["text"].append((full_class, hex_color))

        for m in BG_CLASS_RE.finditer(class_str):
            full_class = m.group(1)
            color_suffix = m.group(2)
            variant = "base"
            if "dark:" in full_class:
                variant = "dark"
            elif "hover:" in full_class:
                variant = "hover"
            elif "focus:" in full_class:
                variant = "focus"

            if variant not in variant_groups:
                variant_groups[variant] = {"text": [], "bg": [], "border": []}
            hex_color = resolve_tw_color(color_suffix)
            if hex_color:
                variant_groups[variant]["bg"].append((full_class, hex_color))

        for m in BORDER_CLASS_RE.finditer(class_str):
            full_class = m.group(1)
            color_suffix = m.group(2)
            variant = "base"
            if "dark:" in full_class:
                variant = "dark"
            elif "hover:" in full_class:
                variant = "hover"

            if variant not in variant_groups:
                variant_groups[variant] = {"text": [], "bg": [], "border": []}
            hex_color = resolve_tw_color(color_suffix)
            if hex_color:
                variant_groups[variant]["border"].append((full_class, hex_color))

        # Pair within each variant group
        for variant, group in variant_groups.items():
            texts = group["text"]
            bgs = group["bg"]
            borders = group["border"]

            # If no bg in this variant, check if base variant has one
            if not bgs and variant != "base" and "base" in variant_groups:
                bgs = variant_groups["base"]["bg"]

            # Default bg if none specified
            default_bg = "#ffffff" if variant != "dark" else "#0f172a"

            for text_class, text_hex in texts:
                if bgs:
                    for bg_class, bg_hex in bgs:
                        raw_pairs.append({
                            "text_color": text_hex,
                            "bg_color": bg_hex,
                            "text_class": text_class,
                            "bg_class": bg_class,
                            "variant": variant,
                            "line": line,
                            "class_string": class_str.strip()[:80],
                        })
                else:
                    raw_pairs.append({
                        "text_color": text_hex,
                        "bg_color": default_bg,
                        "text_class": text_class,
                        "bg_class": f"(default: {default_bg})",
                        "variant": variant,
                        "line": line,
                        "class_string": class_str.strip()[:80],
                    })

            # Border vs bg (SC 1.4.11)
            for border_class, border_hex in borders:
                bg_hex = bgs[0][1] if bgs else default_bg
                bg_class = bgs[0][0] if bgs else f"(default: {default_bg})"
                raw_pairs.append({
                    "text_color": border_hex,
                    "bg_color": bg_hex,
                    "text_class": border_class,
                    "bg_class": bg_class,
                    "variant": variant,
                    "line": line,
                    "class_string": class_str.strip()[:80],
                    "is_border": True,
                })

    return raw_pairs


# ═══════════════════════════════════════════════════════════════
# Fix Suggestion — Tailwind Class Replacement
# ═══════════════════════════════════════════════════════════════

def find_nearest_tw_class(target_hex, prefix, color_family):
    """Find the Tailwind class closest to a target hex value."""
    best = None
    best_diff = float("inf")

    for tw_name, tw_hex in TAILWIND_COLORS.items():
        if tw_hex is None:
            continue
        # Filter to same color family if specified
        if color_family and not tw_name.startswith(color_family):
            continue
        try:
            from contrast_check import hex_to_rgb, relative_luminance
            tr, tg, tb = hex_to_rgb(target_hex)
            cr, cg, cb = hex_to_rgb(tw_hex)
            # Simple RGB distance
            diff = abs(tr-cr) + abs(tg-cg) + abs(tb-cb)
            if diff < best_diff:
                best_diff = diff
                best = tw_name
        except Exception:
            continue

    return f"{prefix}-{best}" if best else None


# ═══════════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════════

def analyze_pairs(pairs, include_cvd=False, suggest_fix_classes=False):
    """Run full contrast analysis on each pair."""
    results = []
    seen = set()

    for pair in pairs:
        dedup_key = (pair["text_color"], pair["bg_color"], pair.get("variant", ""))
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
            "text_class": pair["text_class"],
            "bg_class": pair["bg_class"],
            "variant": pair.get("variant", "base"),
            "line": pair["line"],
            "class_string": pair.get("class_string", ""),
            "is_border": pair.get("is_border", False),
            **rating,
        }

        if not rating["aa_body_text"]:
            fix_hex = find_fixed_color(text_hex, bg_hex, 4.5)
            result["fix_aa_hex"] = fix_hex
            result["fix_aa_ratio"] = round(contrast_ratio(fix_hex, bg_hex), 2)
            if suggest_fix_classes:
                # Determine color family from original class
                original_suffix = pair["text_class"].split("text-")[-1] if "text-" in pair["text_class"] else ""
                family = original_suffix.rsplit("-", 1)[0] if "-" in original_suffix else ""
                fix_class = find_nearest_tw_class(fix_hex, "text", family)
                if fix_class:
                    result["fix_aa_class"] = fix_class

        if not rating["aaa_body_text"]:
            fix_hex = find_fixed_color(text_hex, bg_hex, 7.0)
            result["fix_aaa_hex"] = fix_hex
            result["fix_aaa_ratio"] = round(contrast_ratio(fix_hex, bg_hex), 2)
            if suggest_fix_classes:
                original_suffix = pair["text_class"].split("text-")[-1] if "text-" in pair["text_class"] else ""
                family = original_suffix.rsplit("-", 1)[0] if "-" in original_suffix else ""
                fix_class = find_nearest_tw_class(fix_hex, "text", family)
                if fix_class:
                    result["fix_aaa_class"] = fix_class

        if include_cvd:
            result["cvd"] = cvd_analysis(text_hex, bg_hex)
            result["hue_warnings"] = check_risky_hues(text_hex, bg_hex)

        results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════
# Report Output
# ═══════════════════════════════════════════════════════════════

def print_report(results, filepaths):
    issues = [r for r in results if not r.get("aa_body_text", True)]
    warnings = [r for r in results if r.get("aa_body_text", False) and not r.get("aaa_body_text", True)]
    passing = [r for r in results if r.get("aaa_body_text", False)]
    errors = [r for r in results if "error" in r]
    total = len(results) - len(errors)

    files_str = ", ".join(filepaths) if len(filepaths) <= 3 else f"{len(filepaths)} files"

    print()
    print(f"{'═' * 60}")
    print(f"  TAILWIND CLASS CONTRAST SCAN REPORT")
    print(f"  Source: {files_str}")
    print(f"{'═' * 60}")
    print()
    print(f"  Found {total} color pairs from Tailwind classes")
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
            variant_tag = f" [{r['variant']}]" if r["variant"] != "base" else ""
            print(f"    {r['text_class']} on {r['bg_class']}{variant_tag}  →  {r['ratio']}:1 ✅")
        print()

    print(f"{'═' * 60}")
    if not issues:
        print(f"  ✅ All Tailwind color pairs pass WCAG AA!")
    else:
        print(f"  ❌ {len(issues)} pair(s) need fixing.")
        print(f"     Replace the Tailwind classes with the suggested alternatives above.")
    print(f"{'═' * 60}")
    print()


def _print_issue(r):
    variant_tag = f" [{r['variant']}]" if r["variant"] != "base" else ""
    source_type = "border vs bg (SC 1.4.11)" if r.get("is_border") else "text on bg"

    print()
    print(f"    L{r['line']}  {source_type}{variant_tag}")
    print(f"    Classes: {r['text_class']}  +  {r['bg_class']}")
    print(f"    Hex:     {r['text_color']} on {r['background_color']}")
    print(f"    Ratio:   {r['ratio']}:1")
    print(f"    AA Body: {'✅' if r['aa_body_text'] else '❌'}  "
          f"AA Large: {'✅' if r['aa_large_text'] else '❌'}  "
          f"AAA Body: {'✅' if r['aaa_body_text'] else '❌'}  "
          f"AAA Large: {'✅' if r['aaa_large_text'] else '❌'}")

    if "fix_aa_hex" in r:
        fix_class = f"  →  use {r['fix_aa_class']}" if "fix_aa_class" in r else ""
        print(f"    Fix AA:  {r['fix_aa_hex']} ({r['fix_aa_ratio']}:1){fix_class}")
    if "fix_aaa_hex" in r:
        fix_class = f"  →  use {r['fix_aaa_class']}" if "fix_aaa_class" in r else ""
        print(f"    Fix AAA: {r['fix_aaa_hex']} ({r['fix_aaa_ratio']}:1){fix_class}")

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

SUPPORTED_EXTENSIONS = {".jsx", ".tsx", ".js", ".ts"}


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
                    if os.path.splitext(f)[1] in SUPPORTED_EXTENSIONS:
                        files.append(os.path.join(root, f))
        else:
            for f in os.listdir(path):
                if os.path.splitext(f)[1] in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(path, f))
        return sorted(files)
    return []


def main():
    args = sys.argv[1:]
    include_cvd = "--cvd" in args
    output_json = "--json" in args
    recursive = "--recursive" in args or "-r" in args
    suggest_fix = "--fix" in args
    args = [a for a in args if a not in ("--cvd", "--json", "--recursive", "-r", "--fix")]

    if not args:
        print("Usage: python3 scan_tailwind.py <path> [--cvd] [--json] [--recursive] [--fix]")
        print()
        print("Scans JSX/TSX files for Tailwind color classes and checks contrast.")
        print()
        print("Options:")
        print("  --cvd        Color blindness simulation")
        print("  --json       JSON output")
        print("  --recursive  Scan directories recursively (alias: -r)")
        print("  --fix        Suggest replacement Tailwind classes for failing pairs")
        print()
        print("Examples:")
        print("  python3 scan_tailwind.py src/components/Button.tsx")
        print("  python3 scan_tailwind.py src/ -r --cvd --fix")
        print("  python3 scan_tailwind.py src/ -r --json > report.json")
        sys.exit(1)

    all_files = []
    for path in args:
        all_files.extend(collect_files(path, recursive))

    if not all_files:
        print("No JSX/TSX/JS/TS files found.")
        sys.exit(1)

    all_pairs = []
    for filepath in all_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except IOError as e:
            print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
            continue

        class_strings = extract_class_strings(code)
        if class_strings:
            pairs = extract_tw_pairs(class_strings)
            for p in pairs:
                p["file"] = filepath
            all_pairs.extend(pairs)

    if not all_pairs:
        print(f"No Tailwind text/bg color pairs found in {len(all_files)} file(s).")
        if not recursive:
            print("Tip: Try --recursive to scan subdirectories.")
        sys.exit(0)

    results = analyze_pairs(all_pairs, include_cvd=include_cvd, suggest_fix_classes=suggest_fix)

    if output_json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, all_files)


if __name__ == "__main__":
    main()
