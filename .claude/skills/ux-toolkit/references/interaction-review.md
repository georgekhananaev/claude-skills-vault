# Interaction & Micro-interaction Review

Evaluate feedback, animations, and perceived performance.

## Loading Indicators & Skeleton States

### Loading Type Selection

| Duration | Indicator Type | Example |
|----------|----------------|---------|
| <300ms | None | Instant actions |
| 300ms-1s | Spinner | Button submit |
| 1-3s | Skeleton | Content loading |
| >3s | Progress bar | File upload |
| Unknown | Indeterminate | Background sync |

### Loading State Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Indicates activity | User knows something's happening | 🟠 Major |
| Matches duration | Appropriate indicator for wait | 🟡 Minor |
| Prevents re-click | Button disabled during load | 🟠 Major |
| Cancelable | Long operations can abort | 🟡 Minor |
| Contextual | Near the loading content | 🟡 Minor |
| Accessible | Announced to screen readers | 🟠 Major |

### Skeleton Screen Guidelines

| Aspect | Guideline |
|--------|-----------|
| Shape | Match actual content layout |
| Animation | Subtle shimmer or pulse |
| Contrast | Low contrast, 10-20% darker than bg |
| Duration | Show after 300ms delay |
| Transition | Fade in content, fade out skeleton |

### Implementation Pattern

```css
.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

## Button & Interactive Element Feedback

### Button States

| State | Visual Cue | Timing |
|-------|------------|--------|
| Default | Base style | - |
| Hover | Slight lift/color change | Instant |
| Focus | Visible ring/outline | Instant |
| Active/Pressed | Pressed down effect | Instant |
| Loading | Spinner, disabled | During action |
| Disabled | Greyed, no cursor | - |
| Success | Check mark, green | 1-2s then reset |
| Error | Shake, red | 1-2s then reset |

### Feedback Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| All states defined | Default, hover, focus, active, disabled | 🟠 Major |
| Visual distinction | States clearly different | 🟠 Major |
| Immediate response | <100ms feedback | 🟠 Major |
| Cursor changes | Pointer on clickable | 🟡 Minor |
| Focus visible | Keyboard users see focus | 🔴 Critical |
| Disabled clear | Obviously non-interactive | 🟠 Major |

### Interactive Element Audit

| Element | Hover | Focus | Active | Disabled |
|---------|-------|-------|--------|----------|
| Primary button | ☐ | ☐ | ☐ | ☐ |
| Secondary button | ☐ | ☐ | ☐ | ☐ |
| Text link | ☐ | ☐ | ☐ | ☐ |
| Icon button | ☐ | ☐ | ☐ | ☐ |
| Form input | ☐ | ☐ | ☐ | ☐ |
| Checkbox | ☐ | ☐ | ☐ | ☐ |
| Toggle | ☐ | ☐ | ☐ | ☐ |
| Card/list item | ☐ | ☐ | ☐ | ☐ |

---

## Transition Timing & Easing

### Standard Durations

| Type | Duration | Use Case |
|------|----------|----------|
| Instant | 0-100ms | Hover, focus, click feedback |
| Fast | 100-200ms | Toggles, small state changes |
| Normal | 200-300ms | Modals, expanding content |
| Slow | 300-500ms | Page transitions, large reveals |
| Deliberate | 500ms+ | Emphasis, dramatic effect |

### Easing Functions

| Easing | When to Use | CSS |
|--------|-------------|-----|
| ease-out | Element entering | `cubic-bezier(0, 0, 0.2, 1)` |
| ease-in | Element leaving | `cubic-bezier(0.4, 0, 1, 1)` |
| ease-in-out | State change in place | `cubic-bezier(0.4, 0, 0.2, 1)` |
| linear | Progress/loading | `linear` |

### Timing Audit

| Transition | Current | Recommended | Issue |
|------------|---------|-------------|-------|
| Button hover | Xms | 100-150ms | |
| Modal open | Xms | 200-300ms | |
| Dropdown | Xms | 150-200ms | |
| Page transition | Xms | 300-400ms | |

### Timing Issues

```
❌ Too fast (<50ms) - Jarring, invisible
❌ Too slow (>500ms) - Feels sluggish
❌ Inconsistent - Different timings for same action
❌ No easing - Linear feels mechanical
```

---

## Animation Purpose Validation

### Functional vs Decorative

| Purpose | Justified | Examples |
|---------|-----------|----------|
| Orientation | ✅ | Page transitions, navigation |
| Feedback | ✅ | Button press, form submit |
| Status | ✅ | Loading, success, error |
| Guidance | ✅ | Onboarding, tooltips |
| Hierarchy | ✅ | Reveal order, emphasis |
| Delight | ⚠️ | Only if not distracting |
| Decoration | ❌ | Gratuitous, no purpose |

### Animation Audit Questions

```
1. Does it help user understand state change?
2. Does it guide attention appropriately?
3. Does it improve perceived performance?
4. Can it be reduced/removed without harm?
5. Does it respect prefers-reduced-motion?
```

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Animation Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Purpose defined | Clear functional reason | 🟡 Minor |
| Duration appropriate | Not too long | 🟡 Minor |
| Easing natural | Physics-based feel | ⚪ Cosmetic |
| Reduced motion | Respects preference | 🟠 Major |
| Performance | No jank/stutter | 🟠 Major |
| Interruptible | Can be cancelled | 🟡 Minor |

---

## Perceived Performance Optimization

### Perception Hacks

| Technique | How It Helps | Implementation |
|-----------|--------------|----------------|
| Skeleton screens | Shows progress, reduces uncertainty | Load skeletons immediately |
| Optimistic UI | Feels instant | Update UI before server confirms |
| Progressive loading | Content appears incrementally | Stream content, lazy load |
| Background processing | User continues working | Queue operations, sync later |
| Instant feedback | Acknowledges action | Visual response <100ms |

### Performance Perception Audit

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| First paint <1s | Something visible quickly | 🟠 Major |
| Interactive <3s | User can act | 🟠 Major |
| Feedback <100ms | Immediate acknowledgment | 🟠 Major |
| No jank | Smooth 60fps scrolling | 🟠 Major |
| Lazy loading | Deferred non-critical | 🟡 Minor |

### Optimistic UI Pattern

```
1. User clicks action
2. UI immediately updates (optimistic)
3. API call in background
4. If fails → revert + error message
5. If succeeds → confirm silently
```

---

## Hover/Focus/Active State Consistency

### State Matrix Template

| Component | Hover | Focus | Active | Disabled |
|-----------|-------|-------|--------|----------|
| Style defined | ☐ | ☐ | ☐ | ☐ |
| Visually distinct | ☐ | ☐ | ☐ | ☐ |
| Consistent w/ system | ☐ | ☐ | ☐ | ☐ |
| A11y compliant | ☐ | ☐ | ☐ | ☐ |

### State Guidelines

| State | Requirement |
|-------|-------------|
| Hover | Subtle change, indicates interactivity |
| Focus | High visibility, 3:1 contrast, works w/o hover |
| Active | Shows pressed/clicked, immediate feedback |
| Disabled | Obviously non-interactive, 50%+ opacity reduction |

### Consistency Checks

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Same component = same states | Button A == Button B | 🟠 Major |
| Focus style uniform | Single focus ring style | 🟠 Major |
| Hover patterns match | Similar lift/color across | 🟡 Minor |
| Active feedback uniform | Same press effect | 🟡 Minor |

---

## Toast & Notification Behavior

### Toast Guidelines

| Aspect | Guideline |
|--------|-----------|
| Position | Top-right or bottom-center |
| Duration | 3-5s for info, persistent for errors |
| Max visible | 3 toasts max, queue others |
| Dismissible | Always include close button |
| Accessible | `role="alert"` or `aria-live` |

### Notification Types

| Type | Duration | Icon | Action |
|------|----------|------|--------|
| Success | 3s | ✓ | Auto-dismiss |
| Info | 4s | i | Auto-dismiss |
| Warning | 5s | ⚠ | Action optional |
| Error | Persistent | ✗ | Requires dismiss |

### Toast Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Visible position | Not covering content | 🟠 Major |
| Dismissible | Close button present | 🟠 Major |
| Appropriate duration | Matches severity | 🟡 Minor |
| Queue system | Multiple handled gracefully | 🟡 Minor |
| Mobile placement | Thumb-reachable dismiss | 🟠 Major |
| Screen reader | Announced appropriately | 🟠 Major |

---

## Modal & Overlay Handling

### Modal Behavior Requirements

| Requirement | Implementation |
|-------------|----------------|
| Focus trap | Tab stays within modal |
| Initial focus | First focusable or content |
| Escape closes | Keyboard accessible |
| Backdrop click | Optional close |
| Return focus | To trigger on close |
| Scroll lock | Body doesn't scroll |
| Accessible | `role="dialog"`, `aria-modal` |

### Modal Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Focus trapped | Can't Tab outside | 🔴 Critical |
| Focus returns | To trigger element | 🟠 Major |
| Escape closes | Keyboard accessible | 🟠 Major |
| Backdrop blocks | Content behind inaccessible | 🟠 Major |
| Close button visible | Clear dismissal | 🟠 Major |
| Scroll contained | Only modal scrolls | 🟡 Minor |
| Mobile full-screen | Or properly sized | 🟠 Major |

### Overlay z-index Scale

```css
:root {
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
  --z-toast: 800;
}
```

---

## Interaction Audit Report Template

```markdown
# Interaction & Micro-interaction Audit

**Product:** [Name]
**Date:** [Date]

## Loading States

| Location | Type | Status | Issue |
|----------|------|--------|-------|
| [page/component] | [spinner/skeleton/progress] | ✅/❌ | [desc] |

## Button States

| Button | Hover | Focus | Active | Disabled |
|--------|-------|-------|--------|----------|
| [name] | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |

## Animation Review

| Animation | Purpose | Duration | Easing | Reduced Motion |
|-----------|---------|----------|--------|----------------|
| [name] | [functional/decorative] | Xms | [type] | ✅/❌ |

## Issues Found

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| [desc] | [page] | 🔴/🟠/🟡/⚪ | [fix] |

## Recommendations

1. [Priority fix]
2. [Enhancement]
```
