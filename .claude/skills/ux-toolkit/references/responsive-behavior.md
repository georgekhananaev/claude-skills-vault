# Responsive & Cross-Device Behavior

Ensure consistent experience across devices & contexts.

## Breakpoint Behavior Checklist

### Standard Breakpoints

| Name | Width | Typical Device |
|------|-------|----------------|
| Mobile S | 320px | iPhone SE |
| Mobile M | 375px | iPhone 12/13 |
| Mobile L | 425px | Large phones |
| Tablet | 768px | iPad portrait |
| Laptop | 1024px | iPad landscape, small laptop |
| Desktop | 1440px | Standard desktop |
| Large | 2560px | 4K monitors |

### Breakpoint Testing Matrix

| Component | Mobile | Tablet | Desktop | Issue |
|-----------|--------|--------|---------|-------|
| Navigation | ☐ | ☐ | ☐ | |
| Header | ☐ | ☐ | ☐ | |
| Hero section | ☐ | ☐ | ☐ | |
| Content grid | ☐ | ☐ | ☐ | |
| Forms | ☐ | ☐ | ☐ | |
| Tables | ☐ | ☐ | ☐ | |
| Modals | ☐ | ☐ | ☐ | |
| Footer | ☐ | ☐ | ☐ | |

### Responsive Issues Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| No horizontal scroll | Content fits viewport | 🔴 Critical |
| Text readable | No zoom needed | 🟠 Major |
| Images scale | No overflow, maintains ratio | 🟠 Major |
| Buttons accessible | Reachable, properly sized | 🟠 Major |
| Forms usable | Fields visible, submittable | 🔴 Critical |
| Navigation works | Menu accessible | 🔴 Critical |

---

## Touch Target Sizing

### Minimum Sizes

| Platform | Min Size | Recommended |
|----------|----------|-------------|
| iOS (Apple HIG) | 44×44pt | 48×48pt |
| Android (Material) | 48×48dp | 56×56dp |
| Web (WCAG AAA) | 44×44px | 48×48px |

### Touch Target Audit

| Element Type | Check | Pass Criteria |
|--------------|-------|---------------|
| Buttons | Size | Min 44×44px |
| Links in text | Spacing | 8px+ between targets |
| Icons | Padding | Touch area extends beyond icon |
| Form inputs | Height | Min 44px |
| Checkboxes/radios | Hit area | Full label clickable |
| Close buttons | Size + placement | 44×44, not in corner |

### Common Violations

```
❌ Small icon buttons (24×24)
❌ Tight link lists (<8px gap)
❌ Checkbox only (label not clickable)
❌ Tiny close X in corner
❌ Dense table actions
```

---

## RTL/LTR Layout Testing

### RTL Languages

Arabic, Hebrew, Urdu, Persian, Pashto, Sindhi

### RTL Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Text alignment | Right-aligned in RTL | 🔴 Critical |
| Layout mirroring | UI flipped horizontally | 🔴 Critical |
| Navigation | Right-to-left order | 🟠 Major |
| Icons | Directional icons flip | 🟠 Major |
| Numbers | LTR within RTL text | 🟠 Major |
| Forms | Labels on correct side | 🟠 Major |
| Scroll direction | Content flows RTL | 🟠 Major |

### Elements That Should Mirror

```
✓ Layout (sidebar left → right)
✓ Navigation order
✓ Progress indicators
✓ Arrows/chevrons
✓ Sliders
✓ Back/forward buttons
```

### Elements That Should NOT Mirror

```
✗ Logos
✗ Phone numbers
✗ Credit card numbers
✗ Code/technical content
✗ Video player controls (play/pause)
✗ Musical notation
```

### Testing RTL

```html
<!-- Add to <html> for testing -->
<html dir="rtl" lang="ar">
```

```css
/* Use logical properties */
margin-inline-start: 1rem; /* Not margin-left */
padding-inline-end: 1rem;  /* Not padding-right */
```

---

## Viewport & Orientation Handling

### Viewport Checks

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Meta viewport | `width=device-width, initial-scale=1` | 🔴 Critical |
| No fixed widths | Use relative units | 🟠 Major |
| Safe areas | Notch/home indicator clearance | 🟠 Major |
| Zoom support | No `maximum-scale=1` | 🟠 Major |

### Orientation Changes

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Content reflows | Adjusts to new width | 🟠 Major |
| No content loss | All visible in both | 🔴 Critical |
| Modals reposition | Centered, fully visible | 🟠 Major |
| Video adapts | Maintains playback | 🟡 Minor |
| Form state preserved | Input not lost | 🔴 Critical |

### Safe Area Insets (iOS)

```css
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
padding-left: env(safe-area-inset-left);
padding-right: env(safe-area-inset-right);
```

---

## Content Reflow & Readability

### Text Reflow

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Line length | 45-75 characters | 🟡 Minor |
| Font size | Min 16px body text | 🟠 Major |
| Line height | 1.4-1.6 for body | 🟡 Minor |
| No text truncation | Full content accessible | 🟠 Major |
| Responsive font | Scales appropriately | 🟡 Minor |

### WCAG Reflow (1.4.10)

Content reflows at 320px width without:
- Horizontal scrolling for vertical content
- Loss of information or functionality
- Two-dimensional scrolling

### Readability Checks

| Viewport | Max Content Width | Font Size |
|----------|-------------------|-----------|
| Mobile | 100% | 16px base |
| Tablet | 720px | 16-18px |
| Desktop | 1200px | 16-20px |
| Large | 1400px max | 18-22px |

---

## Navigation Pattern Adaptation

### Mobile Navigation Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| Hamburger menu | Many items | Saves space | Hidden discoverability |
| Bottom tabs | <5 primary actions | Thumb-friendly | Limited items |
| Tab bar | Equal-weight sections | Clear, accessible | Takes screen space |
| Priority+ | Many items, some key | Shows important | Complex to implement |

### Navigation Audit

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Mobile nav accessible | Clear trigger, full options | 🔴 Critical |
| Touch-friendly | 44px+ targets | 🟠 Major |
| Current state shown | Active item highlighted | 🟠 Major |
| Depth manageable | Max 2-3 levels on mobile | 🟡 Minor |
| Close mechanism | X or overlay tap | 🟠 Major |
| Focus trapped | In open menu | 🟠 Major |

---

## Image & Media Responsiveness

### Image Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Responsive images | `srcset` or CSS | 🟠 Major |
| Aspect ratio | Maintained on resize | 🟠 Major |
| Lazy loading | `loading="lazy"` | 🟡 Minor |
| Alt text | Present on all | 🔴 Critical |
| Format optimization | WebP w/ fallback | 🟡 Minor |
| Max width | `max-width: 100%` | 🟠 Major |

### Video Responsiveness

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Aspect ratio | 16:9 maintained | 🟠 Major |
| No overflow | Fits container | 🟠 Major |
| Controls accessible | Large enough to tap | 🟠 Major |
| Autoplay | Disabled on mobile | 🟡 Minor |
| Poster image | Shows before load | 🟡 Minor |

### Responsive Image Pattern

```html
<img
  src="image-800.jpg"
  srcset="image-400.jpg 400w, image-800.jpg 800w, image-1200.jpg 1200w"
  sizes="(max-width: 600px) 100vw, 50vw"
  alt="Description"
  loading="lazy"
>
```

---

## Input Method Differences

### Touch vs Mouse vs Keyboard

| Interaction | Touch | Mouse | Keyboard |
|-------------|-------|-------|----------|
| Hover | N/A | `:hover` | N/A |
| Primary click | Tap | Left click | Enter/Space |
| Context menu | Long press | Right click | Context key |
| Drag | Touch drag | Mouse drag | Arrow keys |
| Scroll | Swipe | Wheel/drag | Arrow/Page keys |

### Touch-Specific Considerations

| Check | Implementation | Severity |
|-------|----------------|----------|
| No hover-only content | Always accessible | 🔴 Critical |
| Touch feedback | `:active` states | 🟡 Minor |
| Gesture alternatives | Button fallbacks | 🟠 Major |
| Scroll hijacking | Avoid or provide escape | 🟠 Major |
| Pinch-zoom support | Don't disable | 🟠 Major |

### Hover Fallback Pattern

```css
/* Mouse hover */
@media (hover: hover) {
  .card:hover { transform: scale(1.02); }
}

/* Touch - show on tap instead */
@media (hover: none) {
  .card:active { transform: scale(0.98); }
}
```

---

## Cross-Device Testing Matrix

```markdown
## Device Testing Checklist

### Mobile (Physical Devices)

| Device | OS | Browser | Status |
|--------|----|---------| -------|
| iPhone SE | iOS 15+ | Safari | ☐ |
| iPhone 14 | iOS 16+ | Safari | ☐ |
| Pixel 6 | Android 12+ | Chrome | ☐ |
| Samsung S21 | Android 11+ | Samsung Browser | ☐ |

### Tablet

| Device | OS | Browser | Status |
|--------|----|---------| -------|
| iPad | iPadOS 15+ | Safari | ☐ |
| iPad Pro | iPadOS 15+ | Safari | ☐ |
| Galaxy Tab | Android 11+ | Chrome | ☐ |

### Desktop

| OS | Browser | Status |
|----|---------|--------|
| Windows | Chrome, Edge, Firefox | ☐ |
| macOS | Safari, Chrome | ☐ |
| Linux | Chrome, Firefox | ☐ |
```

---

## Responsive Audit Report Template

```markdown
# Responsive Behavior Audit

**Product:** [Name]
**Date:** [Date]

## Breakpoint Summary

| Breakpoint | Status | Issues |
|------------|--------|--------|
| 320px | ✅/⚠️/❌ | X issues |
| 768px | ✅/⚠️/❌ | X issues |
| 1024px | ✅/⚠️/❌ | X issues |
| 1440px | ✅/⚠️/❌ | X issues |

## Critical Issues

| Issue | Breakpoint | Severity | Fix |
|-------|------------|----------|-----|
| [desc] | [size] | 🔴/🟠/🟡 | [solution] |

## Touch Target Violations

| Element | Current Size | Required | Location |
|---------|--------------|----------|----------|
| [elem] | Xpx | 44px | [page] |

## RTL Issues (if applicable)

| Issue | Location | Fix |
|-------|----------|-----|
| [desc] | [page] | [solution] |
```
