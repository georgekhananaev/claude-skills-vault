#!/usr/bin/env python3
"""Check color contrast ratios for WCAG compliance.

Usage:
    python3 check_contrast.py --fg "#333333" --bg "#FFFFFF"
    python3 check_contrast.py --fg "rgb(51, 51, 51)" --bg "rgb(255, 255, 255)"
    python3 check_contrast.py --fg "#333" --bg "#FFF" --verbose
"""

import argparse
import re
import sys
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')

    # Handle 3-digit hex
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")

    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_string_to_tuple(rgb_str: str) -> Tuple[int, int, int]:
    """Parse rgb(r, g, b) string to tuple."""
    match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str)
    if not match:
        raise ValueError(f"Invalid rgb format: {rgb_str}")
    return tuple(int(x) for x in match.groups())


def parse_color(color: str) -> Tuple[int, int, int]:
    """Parse color string (hex or rgb) to RGB tuple."""
    color = color.strip()

    if color.startswith('#'):
        return hex_to_rgb(color)
    elif color.lower().startswith('rgb'):
        return rgb_string_to_tuple(color)
    else:
        # Try as hex without #
        return hex_to_rgb(color)


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1."""
    def transform(c: int) -> float:
        c_srgb = c / 255
        if c_srgb <= 0.03928:
            return c_srgb / 12.92
        return ((c_srgb + 0.055) / 1.055) ** 2.4

    return 0.2126 * transform(r) + 0.7152 * transform(g) + 0.0722 * transform(b)


def contrast_ratio(fg: Tuple[int, int, int], bg: Tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two colors."""
    l1 = relative_luminance(*fg)
    l2 = relative_luminance(*bg)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def check_wcag(ratio: float) -> dict:
    """Check WCAG compliance levels."""
    return {
        'aa_normal': ratio >= 4.5,      # Normal text AA
        'aa_large': ratio >= 3.0,        # Large text AA
        'aaa_normal': ratio >= 7.0,      # Normal text AAA
        'aaa_large': ratio >= 4.5,       # Large text AAA
        'ui_components': ratio >= 3.0,   # UI components & graphics
    }


def main():
    parser = argparse.ArgumentParser(description="Check color contrast ratio for WCAG")
    parser.add_argument("--fg", required=True, help="Foreground color (hex or rgb)")
    parser.add_argument("--bg", required=True, help="Background color (hex or rgb)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed results")

    args = parser.parse_args()

    try:
        fg = parse_color(args.fg)
        bg = parse_color(args.bg)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    ratio = contrast_ratio(fg, bg)
    compliance = check_wcag(ratio)

    # Determine overall status
    if compliance['aaa_normal']:
        status = "✅ Passes AA & AAA (all text sizes)"
        exit_code = 0
    elif compliance['aa_normal']:
        status = "✅ Passes AA (all text sizes)"
        exit_code = 0
    elif compliance['aa_large']:
        status = "⚠️  Passes AA for large text only (≥18pt or ≥14pt bold)"
        exit_code = 0
    else:
        status = "❌ Fails WCAG contrast requirements"
        exit_code = 1

    print(f"\nContrast Ratio: {ratio:.2f}:1")
    print(f"Status: {status}")

    if args.verbose:
        print(f"\nColors:")
        print(f"  Foreground: rgb{fg} → #{fg[0]:02x}{fg[1]:02x}{fg[2]:02x}")
        print(f"  Background: rgb{bg} → #{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}")
        print(f"\nWCAG Compliance:")
        print(f"  AA Normal Text (4.5:1):  {'✅ Pass' if compliance['aa_normal'] else '❌ Fail'}")
        print(f"  AA Large Text (3.0:1):   {'✅ Pass' if compliance['aa_large'] else '❌ Fail'}")
        print(f"  AAA Normal Text (7.0:1): {'✅ Pass' if compliance['aaa_normal'] else '❌ Fail'}")
        print(f"  AAA Large Text (4.5:1):  {'✅ Pass' if compliance['aaa_large'] else '❌ Fail'}")
        print(f"  UI Components (3.0:1):   {'✅ Pass' if compliance['ui_components'] else '❌ Fail'}")
        print(f"\nThresholds:")
        print(f"  Normal text: <18pt regular, <14pt bold")
        print(f"  Large text:  ≥18pt regular, ≥14pt bold")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
