#!/usr/bin/env python3
"""
Color Contrast Analyzer — CLI utility
WCAG 2.1/2.2 Contrast Analysis with Color Blindness Simulation

Usage:
  python3 contrast_check.py "#333333" "#ffffff"
  python3 contrast_check.py "#333333" "#ffffff" "#6b7280" "#f3f4f6"
  python3 contrast_check.py --cvd "#e53e3e" "#38a169"
  python3 contrast_check.py --json "#333333" "#ffffff"

Accepts pairs of (text_color, background_color) as hex values.
Outputs contrast ratio, WCAG compliance, fixes, and color blindness analysis.
"""

import sys
import re
import json
import math
import colorsys

# ═══════════════════════════════════════════════════════════════
# Named CSS Colors
# ═══════════════════════════════════════════════════════════════

NAMED_COLORS = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000",
    "green": "#008000", "blue": "#0000ff", "yellow": "#ffff00",
    "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0",
    "orange": "#ffa500", "purple": "#800080", "navy": "#000080",
    "teal": "#008080", "maroon": "#800000", "olive": "#808000",
    "aqua": "#00ffff", "fuchsia": "#ff00ff", "lime": "#00ff00",
    "coral": "#ff7f50", "salmon": "#fa8072", "tomato": "#ff6347",
    "gold": "#ffd700", "khaki": "#f0e68c", "plum": "#dda0dd",
    "ivory": "#fffff0", "linen": "#faf0e6", "beige": "#f5f5dc",
    "lavender": "#e6e6fa", "slategray": "#708090", "dimgray": "#696969",
    "darkgray": "#a9a9a9", "lightgray": "#d3d3d3",
    "gainsboro": "#dcdcdc", "whitesmoke": "#f5f5f5",
}

# ═══════════════════════════════════════════════════════════════
# Color Blindness Simulation Matrices (Brettel/Viénot/Mollon)
# ═══════════════════════════════════════════════════════════════

CVD_MATRICES = {
    "protanopia": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [0.003882, -0.048116, 1.044234],
    ],
    "deuteranopia": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritanopia": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
    "protanomaly": [
        [0.458064, 0.679578, -0.137642],
        [0.092785, 0.846313, 0.060902],
        [-0.007494, -0.016807, 1.024301],
    ],
    "deuteranomaly": [
        [0.547494, 0.607765, -0.155259],
        [0.181692, 0.781742, 0.036566],
        [-0.010410, 0.027275, 0.983136],
    ],
}


# ═══════════════════════════════════════════════════════════════
# Color Conversion Utilities
# ═══════════════════════════════════════════════════════════════

def normalize_hex(color: str) -> str:
    """Convert a color string to 6-digit hex."""
    color = color.strip().lower()
    if color in NAMED_COLORS:
        color = NAMED_COLORS[color]
    color = color.lstrip("#")
    if len(color) == 3:
        color = color[0] * 2 + color[1] * 2 + color[2] * 2
    if len(color) == 8:  # strip alpha
        color = color[:6]
    if len(color) != 6 or not re.match(r"^[0-9a-f]{6}$", color):
        raise ValueError(f"Invalid color: #{color}")
    return f"#{color}"


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_hsl(hex_color: str) -> tuple:
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360, s * 100, l * 100)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return rgb_to_hex(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def srgb_to_linear(c: float) -> float:
    """Convert sRGB channel (0-1) to linear."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    """Convert linear channel to sRGB (0-1)."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1 / 2.4)) - 0.055


# ═══════════════════════════════════════════════════════════════
# WCAG Luminance & Contrast
# ═══════════════════════════════════════════════════════════════

def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.x."""
    rs = srgb_to_linear(r / 255)
    gs = srgb_to_linear(g / 255)
    bs = srgb_to_linear(b / 255)
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    r1, g1, b1 = hex_to_rgb(normalize_hex(color1))
    r2, g2, b2 = hex_to_rgb(normalize_hex(color2))
    l1 = relative_luminance(r1, g1, b1)
    l2 = relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_rating(ratio: float) -> dict:
    return {
        "ratio": round(ratio, 2),
        "aa_body_text": ratio >= 4.5,
        "aa_large_text": ratio >= 3.0,
        "aaa_body_text": ratio >= 7.0,
        "aaa_large_text": ratio >= 4.5,
    }


# ═══════════════════════════════════════════════════════════════
# The Fixer — HSL-based Binary Search
# ═══════════════════════════════════════════════════════════════

def find_fixed_color(failing_hex: str, anchor_hex: str, target_ratio: float = 4.5) -> str:
    """
    Find the nearest color to failing_hex that achieves target_ratio
    against anchor_hex by adjusting only lightness (preserving hue & saturation).
    """
    h, s, l = hex_to_hsl(failing_hex)
    anchor_rgb = hex_to_rgb(normalize_hex(anchor_hex))
    anchor_lum = relative_luminance(*anchor_rgb)

    original_l = l

    # Try darkening first (more common need)
    best_dark = _binary_search_lightness(h, s, original_l, 0, anchor_hex, target_ratio)
    # Try lightening
    best_light = _binary_search_lightness(h, s, original_l, 100, anchor_hex, target_ratio)

    # Pick the one closest to the original lightness
    candidates = []
    if best_dark:
        dark_h, dark_s, dark_l = hex_to_hsl(best_dark)
        candidates.append((abs(dark_l - original_l), best_dark))
    if best_light:
        light_h, light_s, light_l = hex_to_hsl(best_light)
        candidates.append((abs(light_l - original_l), best_light))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # Fallback: black or white
    ratio_black = contrast_ratio("#000000", anchor_hex)
    ratio_white = contrast_ratio("#ffffff", anchor_hex)
    return "#000000" if ratio_black >= ratio_white else "#ffffff"


def _binary_search_lightness(h, s, start_l, end_l, anchor_hex, target_ratio):
    """Binary search on lightness to find a passing color."""
    low = min(start_l, end_l)
    high = max(start_l, end_l)

    # Check if a solution exists in this range
    candidate_hex = hsl_to_hex(h, s, end_l)
    if contrast_ratio(candidate_hex, anchor_hex) < target_ratio:
        return None

    for _ in range(50):  # max iterations
        mid = (low + high) / 2
        candidate = hsl_to_hex(h, s, mid)
        ratio = contrast_ratio(candidate, anchor_hex)

        if abs(ratio - target_ratio) < 0.05:
            return candidate

        if ratio >= target_ratio:
            # Move closer to original
            if end_l < start_l:
                low = mid
            else:
                high = mid
        else:
            # Move further from original
            if end_l < start_l:
                high = mid
            else:
                low = mid

    return hsl_to_hex(h, s, (low + high) / 2)


# ═══════════════════════════════════════════════════════════════
# Color Blindness Simulation
# ═══════════════════════════════════════════════════════════════

def simulate_cvd(hex_color: str, cvd_type: str) -> str:
    """Simulate how a color appears with a given color vision deficiency."""
    r, g, b = hex_to_rgb(normalize_hex(hex_color))
    # Convert to linear RGB
    rl = srgb_to_linear(r / 255)
    gl = srgb_to_linear(g / 255)
    bl = srgb_to_linear(b / 255)

    matrix = CVD_MATRICES[cvd_type]
    sr = matrix[0][0] * rl + matrix[0][1] * gl + matrix[0][2] * bl
    sg = matrix[1][0] * rl + matrix[1][1] * gl + matrix[1][2] * bl
    sb = matrix[2][0] * rl + matrix[2][1] * gl + matrix[2][2] * bl

    # Clamp and convert back to sRGB
    sr = max(0, min(1, sr))
    sg = max(0, min(1, sg))
    sb = max(0, min(1, sb))

    return rgb_to_hex(
        int(round(linear_to_srgb(sr) * 255)),
        int(round(linear_to_srgb(sg) * 255)),
        int(round(linear_to_srgb(sb) * 255)),
    )


def rgb_to_lab(r: int, g: int, b: int) -> tuple:
    """Convert RGB to CIELAB for perceptual difference calculation."""
    # RGB -> XYZ (D65)
    rl = srgb_to_linear(r / 255)
    gl = srgb_to_linear(g / 255)
    bl = srgb_to_linear(b / 255)

    x = 0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl
    y = 0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl
    z = 0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl

    # XYZ -> Lab (D65 reference white)
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t):
        if t > 0.008856:
            return t ** (1 / 3)
        return 7.787 * t + 16 / 116

    L = 116 * f(y / yn) - 16
    a = 500 * (f(x / xn) - f(y / yn))
    b_val = 200 * (f(y / yn) - f(z / zn))
    return (L, a, b_val)


def delta_e(hex1: str, hex2: str) -> float:
    """Calculate CIE76 ΔE between two colors."""
    lab1 = rgb_to_lab(*hex_to_rgb(normalize_hex(hex1)))
    lab2 = rgb_to_lab(*hex_to_rgb(normalize_hex(hex2)))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def cvd_analysis(text_hex: str, bg_hex: str) -> list:
    """Analyze color pair under all CVD types."""
    original_ratio = contrast_ratio(text_hex, bg_hex)
    results = []

    for cvd_type in ["protanopia", "deuteranopia", "tritanopia"]:
        sim_text = simulate_cvd(text_hex, cvd_type)
        sim_bg = simulate_cvd(bg_hex, cvd_type)
        sim_ratio = contrast_ratio(sim_text, sim_bg)
        de = delta_e(sim_text, sim_bg)

        if de < 3:
            risk = "critical"
        elif de < 10:
            risk = "high"
        elif sim_ratio < 3.0:
            risk = "high"
        elif sim_ratio < 4.5 and original_ratio >= 4.5:
            risk = "warning"
        else:
            risk = "ok"

        results.append({
            "type": cvd_type,
            "simulated_text": sim_text,
            "simulated_bg": sim_bg,
            "simulated_ratio": round(sim_ratio, 2),
            "delta_e": round(de, 1),
            "risk": risk,
        })

    return results


def check_risky_hues(text_hex: str, bg_hex: str) -> list:
    """Check for known high-risk hue combinations for CVD."""
    warnings = []
    th, ts, tl = hex_to_hsl(text_hex)
    bh, bs, bl = hex_to_hsl(bg_hex)

    def is_red(h, s):
        return (h < 20 or h > 340) and s > 30

    def is_green(h, s):
        return 80 < h < 170 and s > 30

    def is_blue(h, s):
        return 200 < h < 260 and s > 30

    def is_purple(h, s):
        return 260 < h < 320 and s > 30

    def is_yellow(h, s):
        return 40 < h < 70 and s > 30

    def is_brown(h, s, l):
        return (h < 40 or h > 350) and s > 15 and l < 50

    if (is_red(th, ts) and is_green(bh, bs)) or (is_green(th, ts) and is_red(bh, bs)):
        warnings.append("RED-GREEN combination — critical risk for Protanopia & Deuteranopia (~6% of men)")
    if (is_red(th, ts) and is_brown(bh, bs, bl)) or (is_brown(th, ts, tl) and is_red(bh, bs)):
        warnings.append("RED-BROWN combination — high risk for Protanopia & Deuteranopia")
    if (is_blue(th, ts) and is_purple(bh, bs)) or (is_purple(th, ts) and is_blue(bh, bs)):
        warnings.append("BLUE-PURPLE combination — high risk for Tritanopia")
    if (is_green(th, ts) and is_yellow(bh, bs)) or (is_yellow(th, ts) and is_green(bh, bs)):
        warnings.append("GREEN-YELLOW combination — high risk for Deuteranopia")

    return warnings


# ═══════════════════════════════════════════════════════════════
# Full Pair Analysis
# ═══════════════════════════════════════════════════════════════

def analyze_pair(text_color: str, bg_color: str, include_cvd: bool = False) -> dict:
    text_hex = normalize_hex(text_color)
    bg_hex = normalize_hex(bg_color)
    ratio = contrast_ratio(text_hex, bg_hex)
    rating = wcag_rating(ratio)

    result = {
        "text_color": text_hex,
        "background_color": bg_hex,
        **rating,
    }

    # The Fixer
    if not rating["aa_body_text"]:
        result["fix_aa"] = find_fixed_color(text_hex, bg_hex, 4.5)
        result["fix_aa_ratio"] = round(contrast_ratio(result["fix_aa"], bg_hex), 2)
    if not rating["aaa_body_text"]:
        result["fix_aaa"] = find_fixed_color(text_hex, bg_hex, 7.0)
        result["fix_aaa_ratio"] = round(contrast_ratio(result["fix_aaa"], bg_hex), 2)

    # Color blindness analysis
    if include_cvd:
        result["cvd"] = cvd_analysis(text_hex, bg_hex)
        result["hue_warnings"] = check_risky_hues(text_hex, bg_hex)

    return result


# ═══════════════════════════════════════════════════════════════
# CLI Output
# ═══════════════════════════════════════════════════════════════

def print_pair(i: int, r: dict):
    print(f"\n{'━' * 50}")
    print(f"  PAIR {i}")
    print(f"{'━' * 50}")

    if "error" in r:
        print(f"  Error: {r['error']}")
        return

    print(f"  Text:       {r['text_color']}")
    print(f"  Background: {r['background_color']}")
    print(f"  Contrast:   {r['ratio']}:1")
    print()
    print(f"  WCAG Compliance:")
    print(f"    AA  Body Text  (4.5:1): {'✅ Pass' if r['aa_body_text'] else '❌ Fail'}")
    print(f"    AA  Large Text (3.0:1): {'✅ Pass' if r['aa_large_text'] else '❌ Fail'}")
    print(f"    AAA Body Text  (7.0:1): {'✅ Pass' if r['aaa_body_text'] else '❌ Fail'}")
    print(f"    AAA Large Text (4.5:1): {'✅ Pass' if r['aaa_large_text'] else '❌ Fail'}")

    if "fix_aa" in r:
        print()
        print(f"  Fixes:")
        print(f"    → For AA:  change text to {r['fix_aa']} (ratio {r['fix_aa_ratio']}:1)")
    if "fix_aaa" in r:
        print(f"    → For AAA: change text to {r['fix_aaa']} (ratio {r['fix_aaa_ratio']}:1)")

    if "cvd" in r:
        print()
        print(f"  Color Blindness Impact:")
        icons = {"protanopia": "🔴", "deuteranopia": "🟢", "tritanopia": "🔵"}
        risk_labels = {
            "critical": "❌ CRITICAL — colors nearly indistinguishable",
            "high": "⚠️  HIGH RISK — significant contrast loss",
            "warning": "⚠️  WARNING — drops below AA body text threshold",
            "ok": "✅ OK",
        }
        for cvd in r["cvd"]:
            icon = icons.get(cvd["type"], "•")
            label = risk_labels.get(cvd["risk"], cvd["risk"])
            print(f"    {icon} {cvd['type']:15s} {cvd['simulated_ratio']:5.2f}:1  ΔE={cvd['delta_e']:5.1f}  {label}")

    if r.get("hue_warnings"):
        print()
        print(f"  Hue Warnings:")
        for w in r["hue_warnings"]:
            print(f"    ⚠️  {w}")


def main():
    args = sys.argv[1:]

    # Parse flags
    include_cvd = "--cvd" in args
    output_json = "--json" in args
    args = [a for a in args if a not in ("--cvd", "--json")]

    if len(args) < 2 or len(args) % 2 != 0:
        print("Usage: python3 contrast_check.py [--cvd] [--json] <text> <bg> [<text2> <bg2> ...]")
        print()
        print("Flags:")
        print("  --cvd   Include color blindness simulation (Protanopia, Deuteranopia, Tritanopia)")
        print("  --json  Output results as JSON")
        print()
        print("Examples:")
        print("  python3 contrast_check.py '#333' '#fff'")
        print("  python3 contrast_check.py --cvd '#e53e3e' '#38a169'")
        print("  python3 contrast_check.py --cvd --json '#9ca3af' '#f3f4f6' '#1a1a1a' '#ffffff'")
        sys.exit(1)

    results = []
    for i in range(0, len(args), 2):
        try:
            result = analyze_pair(args[i], args[i + 1], include_cvd=include_cvd)
            results.append(result)
        except ValueError as e:
            results.append({"error": str(e), "text_input": args[i], "bg_input": args[i + 1]})

    if output_json:
        print(json.dumps(results, indent=2))
    else:
        for i, r in enumerate(results, 1):
            print_pair(i, r)
        print()


if __name__ == "__main__":
    main()
