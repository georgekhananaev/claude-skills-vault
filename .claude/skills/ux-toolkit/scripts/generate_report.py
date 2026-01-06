#!/usr/bin/env python3
"""Generate UX audit report from findings.

Usage:
    python3 generate_report.py --type [full|heuristic|a11y|flow|responsive|interaction] --output report.md
    python3 generate_report.py --type full --output ux-audit-report.md
"""

import argparse
from datetime import datetime
from pathlib import Path

REPORT_TEMPLATES = {
    "full": """# UX Audit Report

**Product:** {product}
**Version:** {version}
**Date:** {date}
**Auditor:** {auditor}

---

## Executive Summary

| Domain | Issues | Critical | Major | Minor | Cosmetic |
|--------|--------|----------|-------|-------|----------|
| Heuristic Audit | - | - | - | - | - |
| Accessibility | - | - | - | - | - |
| User Flow | - | - | - | - | - |
| Responsive | - | - | - | - | - |
| Interactions | - | - | - | - | - |
| **Total** | **-** | **-** | **-** | **-** | **-** |

---

## 1. Heuristic Audit Findings

### Critical Issues
| Issue | Heuristic | Location | Recommendation |
|-------|-----------|----------|----------------|
| | | | |

### Major Issues
| Issue | Heuristic | Location | Recommendation |
|-------|-----------|----------|----------------|
| | | | |

---

## 2. Accessibility Findings

### WCAG Compliance Summary
| Principle | Pass | Fail | N/A |
|-----------|------|------|-----|
| Perceivable | | | |
| Operable | | | |
| Understandable | | | |
| Robust | | | |

### Critical Issues
| Issue | WCAG Criterion | Location | Fix |
|-------|----------------|----------|-----|
| | | | |

---

## 3. User Flow Findings

### Flow Metrics
| Flow | Steps | Drop-off | Friction Points |
|------|-------|----------|-----------------|
| | | | |

### Friction Points
| Flow | Step | Issue | Severity | Fix |
|------|------|-------|----------|-----|
| | | | | |

---

## 4. Responsive Behavior Findings

### Breakpoint Status
| Breakpoint | Status | Issues |
|------------|--------|--------|
| 320px | | |
| 768px | | |
| 1024px | | |
| 1440px | | |

### Issues
| Issue | Breakpoint | Severity | Fix |
|-------|------------|----------|-----|
| | | | |

---

## 5. Interaction Findings

### State Audit
| Component | Hover | Focus | Active | Disabled |
|-----------|-------|-------|--------|----------|
| | | | | |

### Animation Issues
| Animation | Issue | Severity | Fix |
|-----------|-------|----------|-----|
| | | | |

---

## Priority Actions

### Immediate (Critical)
1.

### Short-term (Major)
1.

### Medium-term (Minor)
1.

---

*Generated with UX Toolkit*
""",

    "heuristic": """# Heuristic Audit Report

**Product:** {product}
**Date:** {date}
**Auditor:** {auditor}

---

## Summary

| Heuristic | Pass | Issues |
|-----------|------|--------|
| H1: Visibility of System Status | | |
| H2: Match System & Real World | | |
| H3: User Control & Freedom | | |
| H4: Consistency & Standards | | |
| H5: Error Prevention | | |
| H6: Recognition vs Recall | | |
| H7: Flexibility & Efficiency | | |
| H8: Aesthetic & Minimalist Design | | |
| H9: Error Recovery | | |
| H10: Help & Documentation | | |

---

## Findings

### Critical (🔴)
| Issue | Heuristic | Location | Recommendation |
|-------|-----------|----------|----------------|
| | | | |

### Major (🟠)
| Issue | Heuristic | Location | Recommendation |
|-------|-----------|----------|----------------|
| | | | |

### Minor (🟡)
| Issue | Heuristic | Location | Recommendation |
|-------|-----------|----------|----------------|
| | | | |

---

*Generated with UX Toolkit*
""",

    "a11y": """# Accessibility Audit Report

**Product:** {product}
**WCAG Target:** AA
**Date:** {date}
**Auditor:** {auditor}

---

## WCAG Compliance Summary

| Principle | Pass | Fail | N/A |
|-----------|------|------|-----|
| 1. Perceivable | | | |
| 2. Operable | | | |
| 3. Understandable | | | |
| 4. Robust | | | |

---

## Automated Testing Results

| Tool | Issues Found |
|------|--------------|
| axe-core | |
| Lighthouse | |

---

## Manual Testing Results

### Keyboard Navigation
| Test | Pass/Fail | Notes |
|------|-----------|-------|
| Tab through page | | |
| Focus visible | | |
| No traps | | |
| Skip links | | |

### Screen Reader
| Test | Pass/Fail | Notes |
|------|-----------|-------|
| Headings announced | | |
| Links descriptive | | |
| Forms labeled | | |
| Errors announced | | |

---

## Issues

### Critical
| Issue | WCAG | Location | Fix |
|-------|------|----------|-----|
| | | | |

### Major
| Issue | WCAG | Location | Fix |
|-------|------|----------|-----|
| | | | |

---

*Generated with UX Toolkit*
""",

    "flow": """# User Flow Analysis Report

**Product:** {product}
**Date:** {date}
**Analyst:** {auditor}

---

## Flows Analyzed

| Flow | Entry | Steps | Exit |
|------|-------|-------|------|
| | | | |

---

## Flow Metrics

| Flow | Users | Completion Rate | Avg Time | Clicks |
|------|-------|-----------------|----------|--------|
| | | | | |

---

## Friction Points

| Flow | Step | Issue | Severity | Impact | Fix |
|------|------|-------|----------|--------|-----|
| | | | | | |

---

## Edge Cases Tested

| Scenario | Flow | Result | Issue |
|----------|------|--------|-------|
| Empty state | | | |
| Error state | | | |
| Timeout | | | |
| Offline | | | |

---

## Recommendations

1.

---

*Generated with UX Toolkit*
""",

    "responsive": """# Responsive Behavior Report

**Product:** {product}
**Date:** {date}
**Tester:** {auditor}

---

## Breakpoint Testing

| Breakpoint | Status | Issues |
|------------|--------|--------|
| 320px (Mobile S) | | |
| 375px (Mobile M) | | |
| 768px (Tablet) | | |
| 1024px (Laptop) | | |
| 1440px (Desktop) | | |

---

## Component Matrix

| Component | 320px | 768px | 1024px | 1440px |
|-----------|-------|-------|--------|--------|
| Navigation | | | | |
| Header | | | | |
| Content | | | | |
| Forms | | | | |
| Footer | | | | |

---

## Touch Target Audit

| Element | Current | Required | Location |
|---------|---------|----------|----------|
| | | 44px | |

---

## RTL Testing (if applicable)

| Check | Status | Issue |
|-------|--------|-------|
| Layout mirrored | | |
| Text aligned | | |
| Icons flipped | | |

---

## Issues

| Issue | Breakpoint | Severity | Fix |
|-------|------------|----------|-----|
| | | | |

---

*Generated with UX Toolkit*
""",

    "interaction": """# Interaction Review Report

**Product:** {product}
**Date:** {date}
**Reviewer:** {auditor}

---

## State Audit

| Component | Hover | Focus | Active | Disabled | Loading |
|-----------|-------|-------|--------|----------|---------|
| | | | | | |

---

## Loading States

| Location | Type | Duration | Status |
|----------|------|----------|--------|
| | | | |

---

## Animation Audit

| Animation | Purpose | Duration | Easing | Reduced Motion |
|-----------|---------|----------|--------|----------------|
| | | | | |

---

## Toast/Notification Behavior

| Type | Duration | Dismissible | Position | Accessible |
|------|----------|-------------|----------|------------|
| Success | | | | |
| Error | | | | |
| Info | | | | |

---

## Modal Checklist

| Check | Status | Notes |
|-------|--------|-------|
| Focus trapped | | |
| Escape closes | | |
| Focus returns | | |
| ARIA attrs | | |

---

## Issues

| Issue | Location | Severity | Fix |
|-------|----------|----------|-----|
| | | | |

---

*Generated with UX Toolkit*
"""
}


def generate_report(report_type: str, output: str, product: str = "[Product Name]",
                   version: str = "[Version]", auditor: str = "[Auditor Name]") -> None:
    """Generate UX audit report from template."""

    if report_type not in REPORT_TEMPLATES:
        print(f"Error: Unknown report type '{report_type}'")
        print(f"Available types: {', '.join(REPORT_TEMPLATES.keys())}")
        return

    template = REPORT_TEMPLATES[report_type]
    date = datetime.now().strftime("%Y-%m-%d")

    report = template.format(
        product=product,
        version=version,
        date=date,
        auditor=auditor
    )

    output_path = Path(output)
    output_path.write_text(report)
    print(f"✅ Generated {report_type} report: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate UX audit report")
    parser.add_argument("--type", "-t", required=True,
                       choices=list(REPORT_TEMPLATES.keys()),
                       help="Report type to generate")
    parser.add_argument("--output", "-o", required=True,
                       help="Output file path")
    parser.add_argument("--product", "-p", default="[Product Name]",
                       help="Product name")
    parser.add_argument("--version", "-v", default="[Version]",
                       help="Product version")
    parser.add_argument("--auditor", "-a", default="[Auditor Name]",
                       help="Auditor name")

    args = parser.parse_args()
    generate_report(args.type, args.output, args.product, args.version, args.auditor)


if __name__ == "__main__":
    main()
