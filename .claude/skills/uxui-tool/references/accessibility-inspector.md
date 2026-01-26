# Accessibility Inspector (WCAG 2.2)

Comprehensive accessibility audit covering WCAG 2.2 AA/AAA criteria, keyboard navigation, and screen reader compatibility.

## Quick Audit Checklist

### Perceivable

| Criterion | Check | Test Method |
|-----------|-------|-------------|
| **1.1.1** Non-text Content | Images have alt text | Inspect `alt` attributes |
| **1.3.1** Info and Relationships | Semantic HTML structure | Check heading hierarchy |
| **1.3.2** Meaningful Sequence | Logical DOM order | Tab through page |
| **1.3.3** Sensory Characteristics | Not shape/location only | Review instructions |
| **1.4.1** Use of Color | Color not only indicator | Grayscale test |
| **1.4.3** Contrast (Minimum) | 4.5:1 text, 3:1 large | Contrast checker |
| **1.4.4** Resize Text | Works at 200% zoom | Browser zoom |
| **1.4.5** Images of Text | Avoid text as images | Inspect images |
| **1.4.10** Reflow | No horizontal scroll 320px | Resize viewport |
| **1.4.11** Non-text Contrast | 3:1 UI components | Check borders, icons |
| **1.4.12** Text Spacing | Survives spacing changes | Apply test CSS |
| **1.4.13** Content on Hover | Dismissible, hoverable | Hover test |

### Operable

| Criterion | Check | Test Method |
|-----------|-------|-------------|
| **2.1.1** Keyboard | All functions via keyboard | Tab/Enter/Space |
| **2.1.2** No Keyboard Trap | Can escape all components | Tab through all |
| **2.1.4** Character Key Shortcuts | Can disable/remap | Check shortcuts |
| **2.4.1** Bypass Blocks | Skip to main content | Check skip link |
| **2.4.2** Page Titled | Descriptive titles | Check `<title>` |
| **2.4.3** Focus Order | Logical focus sequence | Tab through page |
| **2.4.4** Link Purpose | Links describe destination | Review link text |
| **2.4.6** Headings and Labels | Descriptive headings | Review all H tags |
| **2.4.7** Focus Visible | Clear focus indicators | Tab and observe |
| **2.4.11** Focus Not Obscured (Min) | Focus visible | Check sticky elements |
| **2.5.3** Label in Name | Visible = accessible name | Compare visual to a11y |
| **2.5.7** Dragging Movements | Single-pointer alternative | Test drag actions |
| **2.5.8** Target Size (Minimum) | 24×24px minimum | Measure targets |

### Understandable

| Criterion | Check | Test Method |
|-----------|-------|-------------|
| **3.1.1** Language of Page | `lang` attribute present | Inspect `<html>` |
| **3.1.2** Language of Parts | Parts in different lang marked | Check `lang` attrs |
| **3.2.1** On Focus | No unexpected changes | Focus each element |
| **3.2.2** On Input | No unexpected changes | Interact with inputs |
| **3.2.6** Consistent Help | Help in same location | Compare pages |
| **3.3.1** Error Identification | Errors clearly described | Trigger validation |
| **3.3.2** Labels or Instructions | Inputs have labels | Check form fields |
| **3.3.3** Error Suggestion | Helpful error messages | Review error states |
| **3.3.7** Redundant Entry | Don't re-ask same info | Check multi-step forms |
| **3.3.8** Accessible Authentication | No cognitive tests | Check login flow |

### Robust

| Criterion | Check | Test Method |
|-----------|-------|-------------|
| **4.1.2** Name, Role, Value | ARIA properly used | Screen reader test |
| **4.1.3** Status Messages | Announced without focus | Test notifications |

---

## WCAG 2.2 New Criteria (Oct 2023)

| Criterion | Level | Summary |
|-----------|-------|---------|
| **2.4.11** Focus Not Obscured (Min) | AA | Focus not fully hidden |
| **2.4.12** Focus Not Obscured (Enhanced) | AAA | Focus not partially hidden |
| **2.4.13** Focus Appearance | AAA | Focus indicator 2px, 3:1 contrast |
| **2.5.7** Dragging Movements | AA | Single-pointer alternative |
| **2.5.8** Target Size (Minimum) | AA | 24×24px with spacing |
| **3.2.6** Consistent Help | A | Help in same location |
| **3.3.7** Redundant Entry | A | Don't re-ask info |
| **3.3.8** Accessible Authentication | AA | No cognitive tests for login |
| **3.3.9** Accessible Authentication (Enhanced) | AAA | No object recognition tests |

---

## Contrast Requirements

### Text Contrast

| Text Type | AA | AAA |
|-----------|-----|-----|
| Normal (<18pt) | 4.5:1 | 7:1 |
| Large (≥18pt / ≥14pt bold) | 3:1 | 4.5:1 |

### Non-Text Contrast (AA)

| Element | Minimum |
|---------|---------|
| UI component boundaries | 3:1 |
| Icons (informational) | 3:1 |
| Focus indicators | 3:1 |
| State changes | 3:1 |
| Graphical objects | 3:1 |

---

## Keyboard Navigation

### Required Key Support

| Key | Expected Behavior |
|-----|-------------------|
| Tab | Move to next focusable |
| Shift+Tab | Move to previous |
| Enter | Activate button/link |
| Space | Activate button, toggle checkbox |
| Arrow keys | Navigate within widgets |
| Escape | Close modal, dismiss popup |
| Home/End | Jump to first/last item |

### Focus Management

**Focus Indicators Must**:
- Be visible (2px+ solid recommended)
- Have 3:1 contrast ratio minimum
- Not rely solely on color change
- Not be obscured by other elements

**Modal Focus**:
- Trap focus within modal
- Return focus to trigger on close
- First focusable element receives focus

---

## Touch Target Sizing

| Standard | Minimum | Recommended |
|----------|---------|-------------|
| WCAG 2.2 AA | 24×24px | 44×44px |
| Apple HIG | 44×44pt | — |
| Material Design | 48×48dp | — |

**Spacing**: 24px targets need adequate spacing; 44px+ preferred

---

## Screen Reader Testing

### Essential Tests

```
□ Page title announces correctly
□ Headings hierarchy logical (h1→h2→h3)
□ All images have appropriate alt text
□ Form fields have accessible labels
□ Error messages announced
□ Dynamic content updates announced
□ Modals properly announced
□ Navigation landmarks present
```

### Semantic HTML Checklist

```html
<!-- Required landmarks -->
<header> or role="banner"
<nav> or role="navigation"  
<main> or role="main"
<footer> or role="contentinfo"

<!-- Proper structure -->
<h1> (one per page)
  <h2> (sections)
    <h3> (subsections)

<!-- Forms -->
<label for="id">
<input id="id" aria-describedby="help">
<span id="help">Help text</span>
```

### Common ARIA Patterns

| Widget | Key ARIA |
|--------|----------|
| Modal | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Tabs | `role="tablist/tab/tabpanel"`, `aria-selected` |
| Menu | `role="menu/menuitem"`, `aria-expanded` |
| Alert | `role="alert"` or `aria-live="assertive"` |
| Status | `role="status"` or `aria-live="polite"` |

---

## Color Blindness

### Common Types

| Type | Affected | Population |
|------|----------|------------|
| Deuteranopia | Red-Green | ~6% males |
| Protanopia | Red-Green | ~2% males |
| Tritanopia | Blue-Yellow | <1% |

### Safe Practices

✅ **Do**:
- Use icons + color
- Add text labels
- Use patterns in charts
- Test with simulators

❌ **Don't**:
- Red/green only differentiation
- Color-only status indicators
- Rely on hue alone for meaning

---

## Testing Methodology

### Automated (Catches ~30%)

1. Run axe DevTools
2. Run WAVE extension
3. Run Lighthouse a11y audit
4. Validate HTML

### Manual (Catches ~70%)

1. **Keyboard-only**: Complete all tasks without mouse
2. **Screen reader**: Navigate with NVDA/VoiceOver
3. **Zoom test**: 200% browser, 400% text
4. **Color test**: Grayscale filter
5. **Motion test**: `prefers-reduced-motion`

---

## Severity Classification

| Level | Impact | Examples |
|-------|--------|----------|
| 🔴 Critical | Blocks access | No keyboard nav, missing alt on functional images |
| 🔴 Critical | Legal risk | Form without labels, no focus indicators |
| 🟠 Major | Significant difficulty | Poor contrast, confusing focus order |
| 🟡 Minor | Inconvenience | Suboptimal heading hierarchy |

---

## Quick A11Y Audit Template

```markdown
## Accessibility Audit: [Page/Component]

### Automated Results
- axe-core: [X] issues
- Lighthouse: [X]/100

### Manual Testing

| Test | Pass | Notes |
|------|------|-------|
| Keyboard navigation | ✅/❌ | |
| Focus visibility | ✅/❌ | |
| Screen reader | ✅/❌ | |
| Color contrast | ✅/❌ | |
| 200% zoom | ✅/❌ | |
| Touch targets | ✅/❌ | |

### Issues Found

| WCAG | Issue | Severity | Effort |
|------|-------|----------|--------|
| X.X.X | [Description] | 🔴/🟠/🟡 | L/M/H |

### WCAG Level: [A/AA/AAA achievable?]
```