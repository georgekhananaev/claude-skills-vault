# Design System Audit

Evaluate design token consistency, component library coverage, and pattern adherence.

## Token Audit

### Color Tokens

| Token Category | Check | Common Issues |
|----------------|-------|---------------|
| Primitives | Base palette defined | Missing shades |
| Semantic | Purpose-based naming | Color values hardcoded |
| Component | Component-specific | Inconsistent usage |

### Color Token Checklist

```
□ Primary palette defined (50-900 shades)
□ Secondary/accent colors defined
□ Neutral/gray scale complete
□ Semantic colors (success, error, warning, info)
□ Background tokens (surface, elevated, overlay)
□ Text tokens (primary, secondary, disabled)
□ Border tokens
□ Dark mode variants
□ No hardcoded hex values in components
```

### Typography Tokens

| Token | Expected |
|-------|----------|
| Font families | 1-3 defined |
| Font sizes | Scale (e.g., xs-3xl) |
| Font weights | 3-5 weights |
| Line heights | Matching size scale |
| Letter spacing | Defined for headings/body |

### Typography Token Checklist

```
□ Font families tokenized
□ Font size scale defined
□ Line height scale defined
□ Font weight tokens (regular, medium, bold, etc.)
□ Text styles composed (heading-1, body-large, etc.)
□ Responsive variants where needed
□ No arbitrary font sizes in components
```

### Spacing Tokens

```
Standard scale (8pt grid):
--spacing-0: 0
--spacing-1: 4px
--spacing-2: 8px
--spacing-3: 12px
--spacing-4: 16px
--spacing-5: 20px
--spacing-6: 24px
--spacing-8: 32px
--spacing-10: 40px
--spacing-12: 48px
--spacing-16: 64px
--spacing-20: 80px
--spacing-24: 96px
```

### Spacing Checklist

```
□ Base unit defined (4px or 8px)
□ Scale follows consistent progression
□ Semantic spacing (compact, default, spacious)
□ Component-level spacing consistent
□ No arbitrary pixel values
```

### Other Tokens

| Category | Tokens Needed |
|----------|---------------|
| Border radius | None, sm, md, lg, full |
| Border width | 1px, 2px, etc. |
| Shadows | sm, md, lg, xl |
| Z-index | Layering scale |
| Transitions | Duration, easing |
| Breakpoints | Mobile, tablet, desktop |

---

## Component Audit

### Core Component Checklist

```
Primitives
□ Button (primary, secondary, ghost, destructive)
□ Input (text, textarea, select)
□ Checkbox
□ Radio
□ Toggle/Switch
□ Link

Feedback
□ Alert/Banner
□ Toast/Notification
□ Badge
□ Tooltip
□ Progress (bar, spinner)
□ Skeleton

Layout
□ Card
□ Modal/Dialog
□ Drawer/Sheet
□ Tabs
□ Accordion
□ Divider

Navigation
□ Navbar
□ Sidebar
□ Breadcrumb
□ Pagination
□ Menu/Dropdown

Data Display
□ Table
□ Avatar
□ Tag/Chip
□ Empty state
```

### Component Consistency Checklist

For each component, verify:

```
□ Uses design tokens (no hardcoded values)
□ All states implemented (hover, focus, active, disabled)
□ Accessible (keyboard, screen reader)
□ Responsive behavior defined
□ Dark mode support
□ RTL support (if applicable)
□ Loading state (if async)
□ Error state (if applicable)
□ Documentation complete
□ Props API consistent with system
```

### Component API Consistency

| Pattern | Standard |
|---------|----------|
| Size variants | `size="sm" | "md" | "lg"` |
| Color variants | `variant="primary" | "secondary"` |
| Disabled state | `disabled={boolean}` |
| Loading state | `loading={boolean}` |
| Full width | `fullWidth={boolean}` |
| Icons | `leftIcon`, `rightIcon` |

---

## Pattern Audit

### Common Patterns

| Pattern | Components | Check |
|---------|------------|-------|
| Form | Input, Label, Error, Button | Consistent validation |
| Modal | Overlay, Dialog, Close | Focus trap, escape |
| Dropdown | Trigger, Menu, Items | Keyboard nav |
| Data table | Table, Sort, Filter, Pagination | Consistent behavior |
| Navigation | Nav, Link, Active state | Current indication |
| Search | Input, Results, Empty | Loading, no results |

### Pattern Checklist

```
□ Patterns documented with examples
□ Patterns use system components
□ Edge cases handled (empty, error, loading)
□ Patterns accessible
□ Patterns responsive
□ Patterns consistent across products
```

---

## Inconsistency Detection

### Visual Inconsistencies

| Type | Detection | Severity |
|------|-----------|----------|
| Color mismatch | Different shades for same purpose | 🟡 Minor |
| Spacing variation | Inconsistent gaps | 🟡 Minor |
| Typography drift | Different sizes/weights | 🟡 Minor |
| Border radius mix | Different radii | 🟡 Minor |
| Shadow inconsistency | Different elevation styles | 🟡 Minor |
| Icon style mix | Outline + filled mixed | 🟠 Major |

### Behavioral Inconsistencies

| Type | Detection | Severity |
|------|-----------|----------|
| Different interaction patterns | Same action, different behavior | 🟠 Major |
| Inconsistent feedback | Different confirmation styles | 🟡 Minor |
| Varied error handling | Different error presentations | 🟠 Major |
| Navigation differences | Inconsistent menu behavior | 🟠 Major |

### Detection Checklist

```
□ Audit all instances of each component
□ Compare token usage across pages
□ Check similar flows for consistency
□ Verify same components behave identically
□ Test same actions give same feedback
□ Compare error handling across features
```

---

## Documentation Audit

### Documentation Requirements

| Document | Purpose | Status |
|----------|---------|--------|
| Token reference | All tokens listed | ✅/❌ |
| Component docs | Usage, props, examples | ✅/❌ |
| Pattern library | Common patterns | ✅/❌ |
| Accessibility guide | A11y requirements | ✅/❌ |
| Contribution guide | How to add/modify | ✅/❌ |

### Documentation Checklist

```
□ All tokens documented
□ Components have usage guidelines
□ Props/variants documented
□ Do's and don'ts provided
□ Accessibility notes included
□ Code examples available
□ Figma/design files linked
□ Version changelog maintained
```

---

## Design System Audit Template

```markdown
## Design System Audit: [System Name]

### Token Completeness

| Category | Status | Notes |
|----------|--------|-------|
| Colors | ✅/⚠️/❌ | |
| Typography | ✅/⚠️/❌ | |
| Spacing | ✅/⚠️/❌ | |
| Borders | ✅/⚠️/❌ | |
| Shadows | ✅/⚠️/❌ | |
| Breakpoints | ✅/⚠️/❌ | |

### Component Coverage

| Category | Count | Documented | Accessible |
|----------|-------|------------|------------|
| Primitives | X/Y | ✅/❌ | ✅/❌ |
| Feedback | X/Y | ✅/❌ | ✅/❌ |
| Layout | X/Y | ✅/❌ | ✅/❌ |
| Navigation | X/Y | ✅/❌ | ✅/❌ |
| Data Display | X/Y | ✅/❌ | ✅/❌ |

### Consistency Issues

| Issue | Severity | Effort | Notes |
|-------|----------|--------|-------|
| [Description] | 🔴/🟠/🟡 | L/M/H | |

### Recommendations
1. [Highest priority]
2. [Second priority]
3. [Third priority]
```