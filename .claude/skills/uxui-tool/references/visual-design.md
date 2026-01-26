# Visual Design Evaluation

Evaluate visual design using established design theory: hierarchy, typography, color, spacing, and Gestalt principles.

## 1. Visual Hierarchy

### Evaluation Criteria

| Principle | Check | Common Issues |
|-----------|-------|---------------|
| **Size contrast** | Primary elements 1.5-2x secondary | Everything same size |
| **Color weight** | High-impact uses bolder colors | Flat, equal emphasis |
| **Whitespace** | Important elements have breathing room | Cramped layouts |
| **Position** | Key content in F/Z pattern hotspots | Buried below fold |
| **Typography weight** | Headlines visually dominant | No clear hierarchy |

### Quick Tests

**Squint Test**: Blur vision—does the most important element still stand out?

**5-Second Test**: What do users remember after 5 seconds?

**Hierarchy Checklist**:
```
□ Primary CTA is most prominent element
□ Clear visual path guides the eye
□ Secondary actions visually subordinate
□ Information density appropriate for context
□ Above-fold content establishes purpose
```

### Severity Guide

| Issue | Severity |
|-------|----------|
| No clear visual hierarchy | 🟠 Major |
| Primary CTA not prominent | 🟠 Major |
| Competing focal points | 🟡 Minor |
| Suboptimal F/Z alignment | 🟡 Minor |

---

## 2. Typography

### Type Scale Systems

| Scale | Ratio | Use Case |
|-------|-------|----------|
| Minor Third | 1.200 | Compact UIs |
| **Major Third** | **1.250** | **Recommended default** |
| Perfect Fourth | 1.333 | Clear hierarchy |
| Perfect Fifth | 1.500 | Dramatic hierarchy |

**Example Scale (1.25 ratio, 16px base)**:
```
12px  - Caption, labels
14px  - Secondary text
16px  - Body (base)
20px  - H4 / Lead
25px  - H3
31px  - H2
39px  - H1
49px  - Display
```

### Typography Checklist

| Aspect | Standard | Red Flags |
|--------|----------|-----------|
| **Scale** | Modular ratio (1.25-1.5) | Random sizes |
| **Line height** | Body: 1.4-1.6, Headings: 1.1-1.3 | Too tight/loose |
| **Line length** | 45-75 characters | Full-width text |
| **Font pairing** | Max 2-3 families | 4+ fonts |
| **Weight contrast** | Min 200 weight difference | Subtle differences |
| **Body minimum** | 16px desktop, 14px mobile | Tiny text |

### Line Height Formula

```
line-height = 1.5 - (0.25 × (font-size - 16) / 16)
```

### Severity Guide

| Issue | Severity |
|-------|----------|
| Body text <14px | 🔴 Critical |
| No type hierarchy | 🟠 Major |
| Line length >80 chars | 🟠 Major |
| Line height <1.2 | 🟠 Major |
| 4+ font families | 🟡 Minor |

---

## 3. Color Theory

### 60-30-10 Rule

| Proportion | Role | Application |
|------------|------|-------------|
| 60% | Dominant | Background, large areas |
| 30% | Secondary | Cards, containers |
| 10% | Accent | CTAs, highlights |

### Semantic Colors

| Color | Meaning | Use Cases |
|-------|---------|-----------|
| 🔴 Red | Error, danger | Validation, destructive actions |
| 🟢 Green | Success, positive | Confirmations, available |
| 🟡 Yellow/Amber | Warning | Alerts, pending |
| 🔵 Blue | Information | Links, primary actions |
| ⚫ Gray | Disabled | Inactive, secondary |

### Contrast Requirements (WCAG 2.2)

| Content | AA | AAA |
|---------|-----|-----|
| Normal text | 4.5:1 | 7:1 |
| Large text (18pt+) | 3:1 | 4.5:1 |
| UI components | 3:1 | — |
| Focus indicators | 3:1 | — |

### Saturation Guidelines

| Element | Saturation |
|---------|------------|
| Backgrounds | 0-15% |
| Cards/surfaces | 0-20% |
| UI components | 30-60% |
| Accents/CTAs | 70-100% |

### Color Checklist

```
□ 60-30-10 distribution followed
□ Semantic colors correct (red=error, green=success)
□ Text meets contrast (4.5:1 normal, 3:1 large)
□ UI components meet 3:1 contrast
□ Works in grayscale (color blindness)
□ Accent reserved for important actions
□ Dark mode properly adapted (if applicable)
```

### Severity Guide

| Issue | Severity |
|-------|----------|
| Text fails contrast | 🔴 Critical |
| Wrong semantic color | 🔴 Critical |
| Color-only differentiation | 🟠 Major |
| Competing accent colors | 🟠 Major |
| Oversaturated UI | 🟡 Minor |

---

## 4. Spacing & Layout

### 8-Point Grid System

```
Base unit: 8px
Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128
```

### Spacing Standards

| Element | Recommended |
|---------|-------------|
| Component padding | 16-24px |
| Element gaps | 8-16px |
| Section spacing | 48-64px |
| Touch targets | Min 44×44px |

### Spacing Checklist

```
□ Consistent spacing scale used
□ Related items closer than unrelated
□ Adequate padding in clickable areas
□ Section spacing creates visual breaks
□ No orphaned elements
□ Grid alignment maintained
```

### Severity Guide

| Issue | Severity |
|-------|----------|
| Touch targets <44px | 🔴 Critical |
| Inconsistent spacing | 🟡 Minor |
| Cramped layouts | 🟡 Minor |
| Grid misalignment | 🟡 Minor |

---

## 5. Gestalt Principles

### Principle Checklist

| Principle | Application | Violation Signs |
|-----------|-------------|-----------------|
| **Proximity** | Related items close together | Unrelated items touching |
| **Similarity** | Same function = same style | Inconsistent treatments |
| **Continuity** | Elements align on visual lines | Jagged layouts |
| **Closure** | Brain completes shapes | Confusing incomplete forms |
| **Figure-ground** | Clear foreground/background | Ambiguous layers |
| **Common region** | Containers group related items | Missing boundaries |

### Gestalt Audit

```
□ Related items grouped by proximity
□ Similar functions have similar appearance
□ Visual flow follows natural reading pattern
□ Containers clearly define groups
□ Figure-ground relationship clear
□ Alignment creates visual continuity
```

### Severity Guide

| Issue | Severity |
|-------|----------|
| Unrelated items appear grouped | 🟠 Major |
| Similar items look different | 🟠 Major |
| Ambiguous grouping | 🟡 Minor |
| Broken visual continuity | 🟡 Minor |

---

## 6. Visual Polish Indicators

### Professional Quality Markers

```
□ Consistent border radii
□ Consistent shadow depths
□ Icon style unified (outline vs filled)
□ Image aspect ratios maintained
□ Loading states designed
□ Empty states designed
□ Error states designed
□ Hover/active states defined
□ Transitions smooth (200-300ms)
```

### Common Polish Issues

| Issue | Severity |
|-------|----------|
| Mixed icon styles | 🟡 Minor |
| Inconsistent border radii | 🟡 Minor |
| Missing hover states | 🟡 Minor |
| Stretched images | 🟠 Major |
| No loading indicators | 🟠 Major |

---

## Quick Visual Audit Template

```markdown
## Visual Design Audit: [Component/Page]

### Hierarchy
- [ ] Pass / [ ] Fail — Primary element prominence
- [ ] Pass / [ ] Fail — Clear visual path
- Notes:

### Typography
- [ ] Pass / [ ] Fail — Consistent scale
- [ ] Pass / [ ] Fail — Readable sizes (≥14px)
- [ ] Pass / [ ] Fail — Appropriate line length
- Notes:

### Color
- [ ] Pass / [ ] Fail — Contrast compliance
- [ ] Pass / [ ] Fail — Semantic correctness
- [ ] Pass / [ ] Fail — Color-blind safe
- Notes:

### Spacing
- [ ] Pass / [ ] Fail — Consistent grid
- [ ] Pass / [ ] Fail — Adequate touch targets
- Notes:

### Gestalt
- [ ] Pass / [ ] Fail — Logical grouping
- [ ] Pass / [ ] Fail — Visual continuity
- Notes:

### Overall Grade: [A-F]
```