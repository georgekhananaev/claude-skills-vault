# Responsive Behavior Audit

Evaluate cross-device behavior, breakpoints, touch interactions, RTL/LTR support, and PWA compliance.

## Breakpoint Testing

### Standard Breakpoints

| Name | Width | Devices |
|------|-------|---------|
| Mobile S | 320px | iPhone SE, small Android |
| Mobile M | 375px | iPhone 12/13/14 |
| Mobile L | 425px | Large phones |
| Tablet | 768px | iPad Mini, tablets |
| Laptop | 1024px | iPad Pro, small laptops |
| Desktop | 1440px | Standard monitors |
| Large | 1920px+ | Large monitors |

### Critical Test Widths

```
320px  - Minimum supported (stress test)
375px  - Common mobile
768px  - Tablet portrait
1024px - Tablet landscape / small laptop
1280px - Laptop
1440px - Desktop
```

### Breakpoint Checklist

```
□ Content readable at 320px
□ No horizontal scroll at any breakpoint
□ Images scale appropriately
□ Navigation transforms correctly
□ Touch targets adequate on mobile
□ Typography scales appropriately
□ Forms usable on mobile
□ Tables have mobile strategy
□ Modals fit viewport
□ Fixed elements don't obscure content
```

---

## Touch Interaction

### Touch Target Requirements

| Standard | Minimum | Recommended |
|----------|---------|-------------|
| WCAG 2.2 | 24×24px | 44×44px |
| Apple HIG | 44×44pt | — |
| Material | 48×48dp | — |

### Touch Target Audit

```
□ All interactive elements ≥44×44px
□ Adequate spacing between targets (≥8px)
□ Touch feedback visible
□ No hover-dependent functionality
□ Swipe gestures have alternatives
□ Long-press has alternative
□ Pinch-zoom not blocked
□ Double-tap not required
```

### Gesture Alternatives (WCAG 2.5.1)

| Gesture | Required Alternative |
|---------|---------------------|
| Swipe | Buttons, tap targets |
| Pinch | Zoom buttons |
| Drag | Tap to select + move |
| Multi-finger | Single-finger option |
| Long press | Visible menu trigger |

---

## Mobile-Specific Issues

### Common Problems

| Issue | Impact | Severity |
|-------|--------|----------|
| Tiny touch targets | Mis-taps | 🔴 Critical |
| Hover-only info | Inaccessible | 🔴 Critical |
| Fixed position abuse | Obscured content | 🟠 Major |
| Viewport not set | Zoom/scale issues | 🔴 Critical |
| No input type | Wrong keyboard | 🟠 Major |
| Landscape broken | Unusable | 🟠 Major |

### Input Type Optimization

| Input | Type | Keyboard |
|-------|------|----------|
| Email | `type="email"` | @ visible |
| Phone | `type="tel"` | Number pad |
| Number | `type="number"` or `inputmode="numeric"` | Number pad |
| URL | `type="url"` | .com, / visible |
| Search | `type="search"` | Search button |

### Mobile Form Best Practices

```
□ Labels above inputs (not beside)
□ Input types set correctly
□ Autocomplete attributes set
□ Inline validation
□ Large submit buttons
□ Sticky keyboard doesn't obscure fields
□ Scroll to errors
```

---

## RTL/LTR Support

### RTL Checklist

```
□ dir="rtl" on html or container
□ Text alignment flips
□ Layout direction flips
□ Icons with direction flip (arrows, etc.)
□ Directional icons don't flip (play, etc.)
□ Number alignment correct
□ Form layout adapts
□ Navigation order reverses
□ Progress indicators reverse
□ Carousels reverse
```

### Bidirectional Content

| Element | RTL Behavior |
|---------|--------------|
| Text alignment | Right-aligned |
| Flexbox/Grid | Direction reverses |
| Margins/Padding | Logical properties |
| Icons (arrows) | Mirror |
| Icons (universal) | Don't mirror |
| Numbers | LTR within RTL |
| Phone numbers | LTR |
| Dates | Locale-dependent |

### CSS Logical Properties

```css
/* Use logical properties for RTL support */
margin-inline-start: 16px;  /* Not margin-left */
padding-inline-end: 16px;   /* Not padding-right */
border-inline-start: 1px;   /* Not border-left */
inset-inline-start: 0;      /* Not left: 0 */
```

---

## PWA Compliance

### Core PWA Checklist

```
□ HTTPS served
□ manifest.json present
□ Service worker registered
□ Offline page available
□ App icons (192px, 512px)
□ Splash screen configured
□ Theme color set
□ Start URL defined
□ Display mode set (standalone/fullscreen)
□ Orientation specified
```

### Manifest Requirements

```json
{
  "name": "Full App Name",
  "short_name": "App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Offline Strategy

| Strategy | Use Case |
|----------|----------|
| Cache-first | Static assets |
| Network-first | Dynamic content |
| Stale-while-revalidate | Balanced freshness |
| Offline fallback | Graceful degradation |

---

## Performance Considerations

### Mobile Performance Targets

| Metric | Target | Tool |
|--------|--------|------|
| LCP | <2.5s | Lighthouse |
| FID | <100ms | Lighthouse |
| CLS | <0.1 | Lighthouse |
| TTI | <3.8s | Lighthouse |
| Bundle size | <200KB JS | webpack-bundle-analyzer |

### Mobile Performance Checklist

```
□ Images optimized (WebP, srcset)
□ Lazy loading implemented
□ Critical CSS inlined
□ JS deferred/async
□ Fonts optimized (display: swap)
□ No layout shifts on load
□ Touch response <100ms
□ Animations at 60fps
```

---

## Cross-Browser Testing

### Browser Matrix

| Browser | Versions | Priority |
|---------|----------|----------|
| Chrome | Latest, Latest-1 | High |
| Safari | Latest, Latest-1 | High |
| Firefox | Latest | Medium |
| Edge | Latest | Medium |
| Samsung Internet | Latest | Medium (if mobile audience) |

### Safari-Specific Issues

```
□ Date input fallback
□ Flexbox gap support
□ CSS aspect-ratio support
□ Safe area insets (notch)
□ Overscroll behavior
□ 100vh issue addressed
```

---

## Responsive Audit Template

```markdown
## Responsive Audit: [Page/Component]

### Breakpoint Testing

| Breakpoint | Status | Issues |
|------------|--------|--------|
| 320px | ✅/❌ | |
| 375px | ✅/❌ | |
| 768px | ✅/❌ | |
| 1024px | ✅/❌ | |
| 1440px | ✅/❌ | |

### Touch Targets
- Minimum size: [X]px
- Issues: [List any <44px targets]

### RTL Support
- Status: ✅ Supported / ❌ Not supported / ⚠️ Partial

### PWA Score
- Lighthouse PWA: [X]/100

### Issues Found

| Issue | Breakpoint | Severity | Effort |
|-------|------------|----------|--------|
| [Description] | [Width] | 🔴/🟠/🟡 | L/M/H |
```