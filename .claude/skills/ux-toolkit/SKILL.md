---
name: ux-toolkit
description: Comprehensive UX evaluation meta-skill. Use when conducting UI/UX audits, accessibility reviews, user flow analysis, responsive testing, or interaction design evaluation.
---

# UX Toolkit

Meta-skill for systematic UX evaluation across 5 domains.

## When to Use

Invoke for:
- UI/UX heuristic evaluations
- Accessibility (WCAG) compliance audits
- User flow & friction analysis
- Responsive/cross-device testing
- Interaction & micro-interaction review

## Sub-Workflows

| Domain | Reference | Purpose |
|--------|-----------|---------|
| Heuristic Audit | `references/heuristic-audit.md` | Nielsen's 10 heuristics, severity ratings |
| A11Y Inspector | `references/accessibility-inspector.md` | WCAG 2.1 AA/AAA, keyboard nav, screen readers |
| Flow Analysis | `references/user-flow-analysis.md` | Task paths, friction points, cognitive load |
| Responsive | `references/responsive-behavior.md` | Breakpoints, touch targets, RTL/LTR |
| Interactions | `references/interaction-review.md` | Micro-interactions, animations, feedback |

## Quick Start

### 1. Select Audit Type

```
Full Audit    → Load all 5 references
Focused Audit → Load specific reference(s)
```

### 2. Execute Workflow

Each reference contains:
- Checklist items w/ pass/fail criteria
- Severity classification
- Remediation guidance
- Tool recommendations

### 3. Generate Report

Use `scripts/generate_report.py` to compile findings:

```bash
python3 scripts/generate_report.py --type [full|heuristic|a11y|flow|responsive|interaction] --output report.md
```

## Severity Levels

| Level | Impact | Action |
|-------|--------|--------|
| 🔴 Critical | Blocks task completion | Fix immediately |
| 🟠 Major | Significant friction | Fix before release |
| 🟡 Minor | Reduced efficiency | Fix in next sprint |
| ⚪ Cosmetic | Polish issue | Backlog |

## Process Overview

```
1. Scope Definition    → Define screens/flows to audit
2. Reference Loading   → Load relevant sub-workflow(s)
3. Systematic Review   → Execute checklist items
4. Finding Capture     → Document issues w/ severity
5. Report Generation   → Compile actionable report
```

## Integration Points

| Tool | Purpose | Usage |
|------|---------|-------|
| axe-core | Automated a11y | `scripts/run_axe.js` |
| Lighthouse | Performance + a11y | Chrome DevTools |
| Contrast Checker | Color ratios | `scripts/check_contrast.py` |

---

Ref: Load specific `references/*.md` for detailed checklists & workflows.
