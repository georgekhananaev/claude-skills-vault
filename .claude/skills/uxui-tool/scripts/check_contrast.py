#!/usr/bin/env python3
"""
Color Contrast Checker
Validates WCAG 2.1 contrast ratios for text and UI components.
"""

import argparse
import json
import re
import sys
from typing import Tuple, Dict, List


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1."""
    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate contrast ratio between two colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    l1 = rgb_to_relative_luminance(*rgb1)
    l2 = rgb_to_relative_luminance(*rgb2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_compliance(ratio: float) -> Dict[str, bool]:
    """Check WCAG compliance levels."""
    return {
        'aa_normal_text': ratio >= 4.5,
        'aa_large_text': ratio >= 3.0,
        'aa_ui_components': ratio >= 3.0,
        'aaa_normal_text': ratio >= 7.0,
        'aaa_large_text': ratio >= 4.5,
    }


def analyze_color_pair(fg: str, bg: str) -> Dict:
    """Analyze a foreground/background color pair."""
    ratio = contrast_ratio(fg, bg)
    compliance = check_wcag_compliance(ratio)

    return {
        'foreground': fg,
        'background': bg,
        'ratio': round(ratio, 2),
        'compliance': compliance,
        'pass_aa_text': compliance['aa_normal_text'],
        'pass_aa_large': compliance['aa_large_text'],
        'pass_aaa_text': compliance['aaa_normal_text'],
    }


def format_result(result: Dict) -> str:
    """Format result for display."""
    status_aa = '✅' if result['pass_aa_text'] else '❌'
    status_aaa = '✅' if result['pass_aaa_text'] else '❌'

    return f"""
Color Pair: {result['foreground']} on {result['background']}
Contrast Ratio: {result['ratio']}:1

WCAG Compliance:
  AA Normal Text (4.5:1): {status_aa} {'PASS' if result['pass_aa_text'] else 'FAIL'}
  AA Large Text (3.0:1):  {'✅ PASS' if result['pass_aa_large'] else '❌ FAIL'}
  AAA Normal Text (7.0:1): {status_aaa} {'PASS' if result['pass_aaa_text'] else 'FAIL'}
"""


def analyze_css_file(filepath: str) -> List[Dict]:
    """Extract and analyze color pairs from CSS file."""
    # This is a simplified implementation
    # In production, use a proper CSS parser
    results = []

    with open(filepath, 'r') as f:
        css = f.read()

    # Extract color definitions (simplified)
    hex_pattern = r'#(?:[0-9a-fA-F]{3}){1,2}'
    colors = list(set(re.findall(hex_pattern, css)))

    print(f"Found {len(colors)} unique colors in {filepath}")

    # Analyze common pairs (simplified - real implementation would parse selectors)
    if len(colors) >= 2:
        # Check first color against all others
        for i, bg in enumerate(colors[1:], 1):
            result = analyze_color_pair(colors[0], bg)
            results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Check color contrast ratios for WCAG compliance'
    )
    parser.add_argument(
        '--fg', '-f',
        help='Foreground color (hex, e.g., #333333)'
    )
    parser.add_argument(
        '--bg', '-b',
        help='Background color (hex, e.g., #ffffff)'
    )
    parser.add_argument(
        '--css',
        help='CSS file to analyze'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    if args.css:
        results = analyze_css_file(args.css)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                print(format_result(result))

    elif args.fg and args.bg:
        result = analyze_color_pair(args.fg, args.bg)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_result(result))

    else:
        # Interactive mode
        print("Color Contrast Checker")
        print("-" * 40)
        fg = input("Foreground color (hex): ").strip()
        bg = input("Background color (hex): ").strip()
        result = analyze_color_pair(fg, bg)
        print(format_result(result))


if __name__ == '__main__':
    main()