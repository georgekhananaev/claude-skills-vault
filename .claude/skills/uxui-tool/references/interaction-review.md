# Interaction Review

Evaluate micro-interactions, animations, feedback patterns, and state transitions.

## Interaction Principles

### Feedback Loop

```
User Action → System Response → State Change → Visual Feedback
    │              │                │               │
    └──────────────┴────────────────┴───────────────┘
                    < 100ms perceived instant
                    < 1s maintains attention
                    > 1s needs progress indicator
```

### Response Time Guidelines

| Duration | Perception | Required Feedback |
|----------|------------|-------------------|
| 0-100ms | Instant | None needed |
| 100-300ms | Slight delay | Subtle transition |
| 300ms-1s | Noticeable wait | Loading indicator |
| 1-10s | Long wait | Progress indicator |
| >10s | Too long | Progress + estimate |

---

## State Transitions

### Required States

| State | Visual Treatment | Purpose |
|-------|------------------|---------|
| Default | Base appearance | Starting point |
| Hover | Subtle change | Affordance signal |
| Focus | High contrast outline | Keyboard navigation |
| Active/Pressed | Depressed/changed | Confirm activation |
| Disabled | Muted, no cursor | Unavailable |
| Loading | Spinner/skeleton | Processing |
| Success | Green/checkmark | Completion |
| Error | Red/warning | Problem |

### State Checklist

```
□ Every interactive element has hover state
□ Focus state visible (3:1 contrast min)
□ Active state provides feedback
□ Disabled state clearly different
□ Loading state for async actions
□ Success confirmation visible
□ Error state with recovery path
□ Empty state with guidance
```

---

## Animation Guidelines

### Timing Functions

| Function | Use Case |
|----------|----------|
| `ease-out` | Enter animations |
| `ease-in` | Exit animations |
| `ease-in-out` | Moving elements |
| `linear` | Opacity, color only |

### Duration Standards

| Animation Type | Duration | Notes |
|----------------|----------|-------|
| Micro-feedback | 100-150ms | Button press, toggle |
| Small transitions | 150-200ms | Hover, focus |
| Medium transitions | 200-300ms | Modal open, dropdown |
| Large transitions | 300-500ms | Page transitions |
| Complex animations | 500-1000ms | Onboarding, tutorials |

### Animation Checklist

```
□ Purpose: Every animation serves UX goal
□ Duration: Appropriate for action type
□ Easing: Matches physical expectation
□ Performance: 60fps maintained
□ Reduced motion: Respects prefers-reduced-motion
□ Not blocking: User can still interact
□ Consistent: Similar actions = similar animations
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

---

## Micro-Interactions

### High-Impact Micro-Interactions

| Interaction | Purpose | Example |
|-------------|---------|---------|
| Button feedback | Confirm click | Ripple, color change |
| Form validation | Prevent errors | Inline checkmarks |
| Progress indication | Show status | Progress bars, steps |
| Pull-to-refresh | Mobile pattern | Spinner animation |
| Skeleton loading | Perceived performance | Content placeholders |
| Success celebration | Delight | Confetti, checkmark |

### Micro-Interaction Audit

```
□ Buttons respond on press (not release)
□ Toggle switches animate smoothly
□ Form fields validate inline
□ Loading states are informative
□ Success states are celebratory (when appropriate)
□ Error states guide recovery
□ Tooltips appear smoothly
□ Dropdowns animate consistently
```

---

## Loading Patterns

### Loading State Options

| Pattern | Best For | Implementation |
|---------|----------|----------------|
| Spinner | Short waits (<3s) | Simple, universal |
| Skeleton | Content loading | Shows structure |
| Progress bar | Known duration | File uploads |
| Shimmer | Feed content | Modern, polished |
| Optimistic UI | Fast actions | Assume success |

### Loading Checklist

```
□ Loading appears within 300ms
□ Progress indicator for >1s operations
□ Skeleton matches final layout
□ Cancel option for long operations
□ Error state on failure
□ Retry option available
□ No layout shift on load complete
```

---

## Gesture Interactions

### Standard Gestures

| Gesture | Common Action | Considerations |
|---------|---------------|----------------|
| Tap | Primary action | Clear touch target |
| Double-tap | Zoom/select | Avoid if possible |
| Long press | Context menu | Show affordance |
| Swipe | Navigate/delete | Provide alternatives |
| Pinch | Zoom | Don't disable |
| Pull down | Refresh | Mobile standard |

### Gesture Guidelines

```
□ Gestures have visual affordances
□ Non-gesture alternatives exist (WCAG)
□ Accidental gestures preventable
□ Gesture feedback immediate
□ Swipe actions reversible
□ Multi-touch optional
```

---

## Feedback Patterns

### Types of Feedback

| Type | Use Case | Example |
|------|----------|---------|
| Visual | State changes | Color, icon, animation |
| Textual | Messages | Toast, inline text |
| Haptic | Mobile actions | Vibration |
| Audio | Important alerts | Notification sound |

### Toast/Notification Guidelines

| Type | Duration | Action |
|------|----------|--------|
| Success | 3-5s auto-dismiss | Optional view |
| Info | 5-8s auto-dismiss | Optional action |
| Warning | Manual dismiss | Required attention |
| Error | Manual dismiss | Recovery action |

### Feedback Checklist

```
□ Actions confirmed within 100ms
□ Success clearly communicated
□ Errors explain what went wrong
□ Errors provide recovery path
□ Toasts don't block interactions
□ Critical notifications persist
□ Undo available for destructive actions
```

---

## Scroll Behavior

### Scroll Patterns

| Pattern | Use Case |
|---------|----------|
| Smooth scroll | Anchor links |
| Infinite scroll | Feeds, lists |
| Parallax | Hero sections |
| Sticky elements | Navigation, headers |
| Scroll snap | Carousels, galleries |

### Scroll Checklist

```
□ Scroll behavior smooth for anchors
□ Infinite scroll has end indicator
□ Sticky elements don't obscure content
□ Scroll position preserved on back
□ Scroll to top available on long pages
□ Pull-to-refresh where expected
□ No scroll hijacking
```

---

## Interaction Audit Template

```markdown
## Interaction Audit: [Component/Page]

### States Evaluation

| State | Present | Accessible | Notes |
|-------|---------|------------|-------|
| Default | ✅/❌ | — | |
| Hover | ✅/❌ | ✅/❌ | |
| Focus | ✅/❌ | ✅/❌ | |
| Active | ✅/❌ | ✅/❌ | |
| Disabled | ✅/❌ | ✅/❌ | |
| Loading | ✅/❌ | ✅/❌ | |
| Error | ✅/❌ | ✅/❌ | |

### Animation Review

| Animation | Duration | Easing | Purpose |
|-----------|----------|--------|---------|
| [Name] | [Xms] | [Type] | [Why] |

### Reduced Motion
- Status: ✅ Supported / ❌ Not supported

### Issues Found

| Issue | Category | Severity | Effort |
|-------|----------|----------|--------|
| [Description] | [State/Animation/Feedback] | 🔴/🟠/🟡 | L/M/H |
```