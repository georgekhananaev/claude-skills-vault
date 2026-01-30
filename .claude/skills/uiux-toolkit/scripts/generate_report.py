#!/usr/bin/env python3
"""
UX Audit Report Generator
Compiles findings into formatted reports (Markdown, JSON, CSV).
"""

import argparse
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Optional


# Severity emoji mapping
SEVERITY_ICONS = {
    'critical': '🔴',
    'major': '🟠',
    'minor': '🟡',
    'enhancement': '🟢'
}

SEVERITY_ORDER = ['critical', 'major', 'minor', 'enhancement']


def create_sample_findings() -> List[Dict]:
    """Generate sample findings for demonstration."""
    return [
        {
            "id": "VIS-001",
            "domain": "Visual Design",
            "title": "Low contrast on secondary text",
            "description": "Gray text (#999) on white background fails WCAG AA",
            "severity": "critical",
            "effort": "low",
            "wcag": "1.4.3",
            "location": "Global - paragraph text",
            "recommendation": "Change to #595959 for 7:1 ratio"
        },
        {
            "id": "A11Y-001",
            "domain": "Accessibility",
            "title": "Missing form labels",
            "description": "Email and password inputs lack associated labels",
            "severity": "critical",
            "effort": "low",
            "wcag": "1.3.1",
            "location": "Login page",
            "recommendation": "Add <label> elements with for attribute"
        },
        {
            "id": "FLOW-001",
            "domain": "User Flow",
            "title": "No error recovery on payment failure",
            "description": "Payment errors clear the form, losing user data",
            "severity": "major",
            "effort": "medium",
            "wcag": None,
            "location": "Checkout flow",
            "recommendation": "Preserve form data on error, show inline validation"
        }
    ]


def generate_markdown_report(
    findings: List[Dict],
    title: str = "UX Audit Report",
    scope: str = "Full audit"
) -> str:
    """Generate Markdown formatted report."""

    # Group by severity
    by_severity = {s: [] for s in SEVERITY_ORDER}
    for f in findings:
        sev = f.get('severity', 'minor').lower()
        if sev in by_severity:
            by_severity[sev].append(f)

    # Count by domain
    domains = {}
    for f in findings:
        domain = f.get('domain', 'Other')
        domains[domain] = domains.get(domain, 0) + 1

    report = f"""# {title}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Scope**: {scope}

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {len(by_severity['critical'])} |
| 🟠 Major | {len(by_severity['major'])} |
| 🟡 Minor | {len(by_severity['minor'])} |
| 🟢 Enhancement | {len(by_severity['enhancement'])} |
| **Total** | **{len(findings)}** |

### Issues by Domain

| Domain | Count |
|--------|-------|
"""

    for domain, count in sorted(domains.items()):
        report += f"| {domain} | {count} |\n"

    report += "\n---\n\n"

    # Findings by severity
    for severity in SEVERITY_ORDER:
        items = by_severity[severity]
        if not items:
            continue

        icon = SEVERITY_ICONS[severity]
        report += f"## {icon} {severity.title()} Issues ({len(items)})\n\n"

        for f in items:
            wcag = f" (WCAG {f['wcag']})" if f.get('wcag') else ""
            report += f"""### {f['id']}: {f['title']}{wcag}

**Domain**: {f.get('domain', 'N/A')} | **Effort**: {f.get('effort', 'N/A').title()} | **Location**: {f.get('location', 'N/A')}

{f.get('description', '')}

**Recommendation**: {f.get('recommendation', 'N/A')}

---

"""

    # Priority action items
    critical_and_major = by_severity['critical'] + by_severity['major']
    if critical_and_major:
        report += "## Priority Action Items\n\n"
        for i, f in enumerate(critical_and_major[:5], 1):
            report += f"{i}. **{f['id']}**: {f['title']} ({f['effort']} effort)\n"

    return report


def generate_json_report(findings: List[Dict], title: str = "UX Audit") -> str:
    """Generate JSON formatted report."""

    summary = {
        'critical': 0,
        'major': 0,
        'minor': 0,
        'enhancement': 0
    }

    for f in findings:
        sev = f.get('severity', 'minor').lower()
        if sev in summary:
            summary[sev] += 1

    report = {
        'title': title,
        'generated': datetime.now().isoformat(),
        'summary': summary,
        'total_issues': len(findings),
        'findings': findings
    }

    return json.dumps(report, indent=2)


def generate_csv_report(findings: List[Dict]) -> str:
    """Generate CSV formatted report."""

    output = io.StringIO()

    fieldnames = [
        'id', 'domain', 'title', 'description', 'severity',
        'effort', 'wcag', 'location', 'recommendation'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for f in findings:
        writer.writerow(f)

    return output.getvalue()


def load_findings(filepath: str) -> List[Dict]:
    """Load findings from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Support both direct array and object with 'findings' key
    if isinstance(data, list):
        return data
    return data.get('findings', [])


def main():
    parser = argparse.ArgumentParser(
        description='Generate UX audit reports from findings'
    )
    parser.add_argument(
        '--input', '-i',
        help='JSON file with findings (or use --demo for sample)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['md', 'json', 'csv'],
        default='md',
        help='Output format (default: md)'
    )
    parser.add_argument(
        '--title', '-t',
        default='UX Audit Report',
        help='Report title'
    )
    parser.add_argument(
        '--type',
        choices=['full', 'heuristic', 'a11y', 'visual', 'flow', 'responsive', 'interaction'],
        default='full',
        help='Audit type for scope description'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Use sample findings for demonstration'
    )

    args = parser.parse_args()

    # Load or generate findings
    if args.demo:
        findings = create_sample_findings()
    elif args.input:
        findings = load_findings(args.input)
    else:
        print("Error: Provide --input file or use --demo")
        return 1

    # Scope description
    scope_map = {
        'full': 'Full UX Audit (all domains)',
        'heuristic': 'Heuristic Evaluation (Nielsen\'s 10)',
        'a11y': 'Accessibility Audit (WCAG 2.2)',
        'visual': 'Visual Design Review',
        'flow': 'User Flow Analysis',
        'responsive': 'Responsive Behavior Audit',
        'interaction': 'Interaction Review'
    }
    scope = scope_map.get(args.type, 'UX Audit')

    # Generate report
    if args.format == 'md':
        report = generate_markdown_report(findings, args.title, scope)
    elif args.format == 'json':
        report = generate_json_report(findings, args.title)
    elif args.format == 'csv':
        report = generate_csv_report(findings)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

    return 0


if __name__ == '__main__':
    exit(main())