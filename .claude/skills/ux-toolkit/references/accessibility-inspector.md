# Accessibility (A11Y) Inspector

WCAG 2.1 compliance & inclusive design review.

## WCAG 2.1 Compliance Levels

| Level | Requirement | Target |
|-------|-------------|--------|
| A | Minimum accessibility | Baseline |
| AA | Acceptable accessibility | **Standard target** |
| AAA | Enhanced accessibility | Ideal for specific audiences |

---

## Perceivable (WCAG 1.x)

### 1.1 Text Alternatives

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Images have alt text | Descriptive, not "image of" | A | axe-core |
| Decorative images | `alt=""` or CSS background | A | Manual |
| Complex images | Long description available | A | Manual |
| Icons w/ meaning | Accessible name provided | A | axe-core |
| Form inputs | Labels or aria-label | A | axe-core |

### 1.2 Time-Based Media

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Video captions | Synchronized captions | A | Manual |
| Audio description | For visual-only content | A | Manual |
| Transcript | Text alternative available | A | Manual |
| No auto-play audio | Or mute control visible | A | Manual |

### 1.3 Adaptable

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Semantic HTML | Proper heading hierarchy | A | axe-core |
| Reading order | Logical DOM order | A | Manual |
| Landmark regions | header, nav, main, footer | A | axe-core |
| Tables | Headers w/ `<th>` scope | A | axe-core |
| Lists | Proper `<ul>`, `<ol>`, `<dl>` | A | axe-core |

### 1.4 Distinguishable

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Color contrast (text) | 4.5:1 normal, 3:1 large | AA | Contrast checker |
| Color contrast (UI) | 3:1 for controls | AA | Contrast checker |
| Color not sole indicator | Shape/text also used | A | Manual |
| Text resize | 200% w/o loss | AA | Browser zoom |
| Text spacing | Adjustable w/o breaking | AA | Manual |
| Reflow | No horiz scroll at 320px | AA | Responsive test |

---

## Operable (WCAG 2.x)

### 2.1 Keyboard Accessible

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| All functionality | Operable via keyboard | A | Manual |
| No keyboard trap | Can Tab away from all elements | A | Manual |
| Visible focus | Clear focus indicator | AA | Manual |
| Focus order | Logical tab sequence | A | Manual |
| Skip links | Skip to main content | A | Manual |
| Shortcut keys | Documented, not conflicting | A | Manual |

**Keyboard Navigation Protocol:**
```
1. Tab through entire page
2. Verify focus visible on each element
3. Test Enter/Space activation
4. Test Escape for overlays
5. Test Arrow keys in menus
6. Verify no dead ends
```

### 2.2 Enough Time

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Session timeout | Warning + extend option | A | Manual |
| Moving content | Pause, stop, hide controls | A | Manual |
| Auto-updating | User-controlled refresh | A | Manual |
| No time limits | Or adjustable + warned | A | Manual |

### 2.3 Seizures & Physical

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| No flashing >3Hz | Avoid seizure triggers | A | Manual |
| Reduced motion | `prefers-reduced-motion` | AAA | Code review |
| Animation toggle | User can disable | AAA | Manual |

### 2.4 Navigable

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Page titles | Descriptive `<title>` | A | axe-core |
| Focus order | Logical sequence | A | Manual |
| Link purpose | Clear from text | A | Manual |
| Multiple ways | Search, nav, sitemap | AA | Manual |
| Headings | Descriptive, hierarchical | AA | axe-core |
| Focus visible | 2px+ visible indicator | AA | Manual |

### 2.5 Input Modalities

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Touch target size | Min 44×44px | AAA | Manual |
| Pointer gestures | Single-point alternative | A | Manual |
| Pointer cancellation | Undo/abort on release | A | Manual |
| Motion actuation | Non-motion alternative | A | Manual |

---

## Understandable (WCAG 3.x)

### 3.1 Readable

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Page language | `lang` attr on `<html>` | A | axe-core |
| Part language | `lang` on foreign text | AA | Manual |
| Unusual words | Glossary available | AAA | Manual |
| Abbreviations | Expanded on first use | AAA | Manual |

### 3.2 Predictable

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| No focus change | Focus doesn't auto-move | A | Manual |
| No input change | Changing input = no submission | A | Manual |
| Consistent nav | Same order across pages | AA | Manual |
| Consistent ID | Same components = same name | AA | Manual |

### 3.3 Input Assistance

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Error identification | Errors described in text | A | Manual |
| Labels/instructions | Present before input | A | axe-core |
| Error suggestion | How to fix described | AA | Manual |
| Error prevention | Confirm destructive actions | AA | Manual |

---

## Robust (WCAG 4.x)

### 4.1 Compatible

| Check | Criteria | Level | Tool |
|-------|----------|-------|------|
| Valid HTML | No major parsing errors | A | W3C validator |
| Name, role, value | ARIA properly applied | A | axe-core |
| Status messages | `aria-live` for dynamic | AA | Manual |

---

## Screen Reader Compatibility

### ARIA Implementation

| Pattern | Required ARIA | Example |
|---------|---------------|---------|
| Button (non-`<button>`) | `role="button"` + keyboard | `<div role="button" tabindex="0">` |
| Modal dialog | `role="dialog"` + `aria-modal="true"` + focus trap | Dialog component |
| Tab panel | `role="tablist"`, `role="tab"`, `role="tabpanel"` | Tabs component |
| Dropdown menu | `aria-expanded`, `aria-haspopup` | Menu button |
| Live region | `aria-live="polite"` or `"assertive"` | Notifications |
| Loading state | `aria-busy="true"` | Skeleton loader |

### Screen Reader Testing

```
1. Enable screen reader (NVDA/JAWS/VoiceOver)
2. Navigate via headings (H key)
3. Navigate via landmarks (D key)
4. Navigate via links (K key)
5. Fill forms, verify label reading
6. Test dynamic content updates
7. Verify error announcements
```

---

## Color Contrast Requirements

| Content Type | AA Ratio | AAA Ratio |
|--------------|----------|-----------|
| Normal text (<18pt/14pt bold) | 4.5:1 | 7:1 |
| Large text (≥18pt/14pt bold) | 3:1 | 4.5:1 |
| UI components & graphics | 3:1 | 3:1 |
| Decorative/logos | No req | No req |

### Contrast Checker Script

```bash
python3 scripts/check_contrast.py --fg "#333333" --bg "#FFFFFF"
# Output: Ratio 12.63:1 ✅ Passes AA & AAA
```

---

## Focus Management

### Focus States Checklist

| State | Requirement |
|-------|-------------|
| Visible | 2px+ outline or equivalent |
| High contrast | 3:1 against adjacent |
| Consistent | Same style across UI |
| No outline removal | Never `outline: none` w/o replacement |
| Focus ring | `:focus-visible` for keyboard only |

### Focus Trap Pattern (Modals)

```javascript
// Required for modal dialogs
1. Move focus to modal on open
2. Trap Tab within modal
3. Return focus to trigger on close
4. Close on Escape key
```

---

## Form Accessibility

### Label Requirements

| Input Type | Labeling Method |
|------------|-----------------|
| Text fields | `<label for="">` or `aria-labelledby` |
| Radio/checkbox groups | `<fieldset>` + `<legend>` |
| Required fields | `aria-required="true"` or `required` |
| Error states | `aria-invalid="true"` + `aria-describedby` |

### Error Announcement

```html
<input aria-invalid="true" aria-describedby="error-msg">
<div id="error-msg" role="alert">Password must be 8+ chars</div>
```

---

## Tools Integration

| Tool | Purpose | Usage |
|------|---------|-------|
| axe-core | Automated testing | `npm run axe` or browser extension |
| Lighthouse | A11y audit | Chrome DevTools → Audits |
| WAVE | Visual overlay | Browser extension |
| NVDA | Screen reader (Windows) | Free download |
| VoiceOver | Screen reader (Mac) | Cmd+F5 |
| Contrast Checker | Color ratios | `scripts/check_contrast.py` |

---

## Audit Report Template

```markdown
# A11Y Audit Report

**Product:** [Name]
**WCAG Target:** AA
**Date:** [Date]

## Summary

| Principle | Pass | Fail | N/A |
|-----------|------|------|-----|
| Perceivable | X | X | X |
| Operable | X | X | X |
| Understandable | X | X | X |
| Robust | X | X | X |

## Critical Issues (Must Fix)

| Issue | WCAG | Location | Fix |
|-------|------|----------|-----|
| [desc] | [criterion] | [page/component] | [solution] |

## Recommendations

1. [Priority fix]
2. [Enhancement]
```
