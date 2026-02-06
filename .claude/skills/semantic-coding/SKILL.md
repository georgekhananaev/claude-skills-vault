# Semantic Coding

Scan files, replace hardcoded styles with semantic design tokens (colors, typography, spacing, sizing), edit files directly.

> Refactored from `semantic-colors` (color-only) into a comprehensive design system skill.

## Usage

```
/semantic-coding [path]
```

## DO NOT TOUCH (Non-Negotiable)

- **Gradients:** `from-*`, `via-*`, `to-*`, `bg-gradient-*`, `linear-gradient()`, `radial-gradient()`, `conic-gradient()`
- **SVG defs:** `<linearGradient>`, `<radialGradient>`, `<stop>`, `url(#...)`, anything inside `<defs>`
- **Glass morphism:** `rgba(255,255,255,0.0x)` overlays on gradient backgrounds
- **Decorative shadows:** `boxShadow` glow effects tied to gradient LED/orb effects
- **Animations:** `@keyframes`, animation timing values, transform values
- **Template literals:** `` `border-${color}-500` ``, dynamic class construction
- **Arbitrary values:** `bg-[#hex]`, `text-[14px]`, `p-[20px]` (JIT bracket syntax)
- **Component props:** Color/style values passed as non-className props (e.g., `<Button color="red-500" />`)
- **Token source files:** `globals.css`, `tailwind.config.*`, `tokens.ts`, `theme.ts`
- **Excluded dirs:** `node_modules`, `.next`, `lib/generated`, `prisma/`, `dist/`, `__tests__/`, `*.test.*`, `*.spec.*`

If a value is inside a protected context, **skip** and log `⚠ skipped (protected context)`.

---

## Color Rules

### Color Replacements

> **Note:** Color-to-semantic mapping depends on your project's brand palette. The defaults below assume orange=brand, blue=info. If your brand uses blue/indigo/etc., map that family to `brand` instead and adjust accordingly.

| Hardcoded | Semantic |
|-----------|----------|
| `text-red-*`, `text-rose-*` | `text-error` |
| `text-green-*`, `text-emerald-*`, `text-teal-*` | `text-success` |
| `text-yellow-*`, `text-amber-*` | `text-warning` |
| `text-blue-*`, `text-cyan-*` | `text-info` |
| `text-orange-*` | `text-brand` |
| `text-indigo-*`, `text-violet-*`, `text-purple-*` | `text-primary` |
| `text-pink-*`, `text-fuchsia-*` | `text-accent` |
| `text-gray-*`, `text-slate-*`, `text-zinc-*`, `text-stone-*`, `text-neutral-*`, `text-ink-*` | `text-muted-foreground` |
| `text-gray-900`, `text-slate-900`, `text-zinc-900` | `text-foreground` |
| `text-white` (on semantic bg) | `text-{bg-token}-foreground` |
| `text-black` | `text-foreground` |
| `bg-red-*`, `bg-rose-*` (shade ≥500) | `bg-error` |
| `bg-red-*`, `bg-rose-*` (shade <500) | `bg-error/10` |
| `bg-green-*`, `bg-emerald-*`, `bg-teal-*` (shade ≥500) | `bg-success` |
| `bg-green-*`, `bg-emerald-*`, `bg-teal-*` (shade <500) | `bg-success/10` |
| `bg-yellow-*`, `bg-amber-*` (shade ≥500) | `bg-warning` |
| `bg-yellow-*`, `bg-amber-*` (shade <500) | `bg-warning/10` |
| `bg-blue-*`, `bg-cyan-*` (shade ≥500) | `bg-info` |
| `bg-blue-*`, `bg-cyan-*` (shade <500) | `bg-info/10` |
| `bg-orange-*` | `bg-brand` or `bg-brand/10` |
| `bg-indigo-*`, `bg-violet-*`, `bg-purple-*` | `bg-primary` or `bg-primary/10` |
| `bg-gray-*`, `bg-slate-*`, `bg-zinc-*`, `bg-stone-*`, `bg-neutral-*`, `bg-ink-*` | `bg-muted` |
| `bg-white` (page-level) | `bg-background` |
| `bg-white` (inside card/panel) | `bg-card` |
| `bg-black/50` (overlay) | `bg-overlay` |
| `border-gray-*`, `border-slate-*`, `border-zinc-*`, `border-stone-*`, `border-neutral-*`, `border-ink-*` | `border-border` |
| `border-red-*`, `border-rose-*` | `border-error` |
| `border-green-*`, `border-emerald-*`, `border-teal-*` | `border-success` |
| `border-blue-*`, `border-cyan-*` | `border-info` |
| `border-yellow-*`, `border-amber-*` | `border-warning` |
| `border-orange-*` | `border-brand` |
| `border-indigo-*`, `border-violet-*`, `border-purple-*` | `border-primary` |
| `shadow-emerald-*`, `shadow-green-*` | `shadow-success` |
| `shadow-red-*` | `shadow-error` |
| `shadow-blue-*` | `shadow-info` |
| `ring-red-*` | `ring-error` |
| `ring-green-*` | `ring-success` |
| `ring-blue-*` | `ring-info` |
| `divide-gray-*`, `divide-slate-*` | `divide-border` |
| `placeholder-gray-*` | `placeholder-muted-foreground` |

### Foreground Pairing

| Background | Foreground |
|------------|------------|
| `bg-primary` | `text-primary-foreground` |
| `bg-brand` | `text-brand-foreground` |
| `bg-success` | `text-success-foreground` |
| `bg-error` | `text-error-foreground` |
| `bg-warning` | `text-warning-foreground` |
| `bg-info` | `text-info-foreground` |

### Dark Mode Override Removal

Collapse light+dark pairs into one semantic token:

```diff
- className="text-green-600 dark:text-green-400"
+ className="text-success"

- className="bg-red-100 dark:bg-red-900/20 border-red-200 dark:border-red-800"
+ className="bg-error/10 border-error"
```

---

## Typography Rules

### Font Family

| Hardcoded | Semantic |
|-----------|----------|
| `font-sans` (body text) | `font-body` |
| `font-sans` (headings) | `font-heading` |
| `font-mono` | `font-mono` |
| `font-serif` | `font-display` |
| Inline `fontFamily: 'Inter'` | `var(--font-body)` |
| Inline `fontFamily: 'monospace'` | `var(--font-mono)` |

### Font Size (Text Scale)

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `text-xs` | `text-caption` | Labels, hints, timestamps |
| `text-sm` | `text-body-sm` | Secondary content, metadata |
| `text-base` | `text-body` | Body text, paragraphs |
| `text-lg` | `text-body-lg` | Lead paragraphs, emphasis |
| `text-xl` | `text-heading-sm` | Small headings, card titles |
| `text-2xl` | `text-heading-md` | Section headings |
| `text-3xl` | `text-heading-lg` | Page titles |
| `text-4xl`, `text-5xl` | `text-heading-xl` | Hero headings |
| `text-6xl`, `text-7xl`, `text-8xl`, `text-9xl` | `text-display` | Display/marketing headings |
| Inline `fontSize: '14px'` | `var(--text-body-sm)` |
| Inline `fontSize: '24px'` | `var(--text-heading-md)` |

### Font Weight

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `font-extralight` (200) | `font-thin` | Decorative, display text |
| `font-light` (300) | `font-light` | Subtle body text |
| `font-normal` (400) | `font-normal` | Body text |
| `font-medium` (500) | `font-medium` | Emphasis, labels |
| `font-semibold` (600) | `font-semibold` | Subheadings |
| `font-bold` (700) | `font-bold` | Headings, CTAs |
| `font-extrabold` (800), `font-black` (900) | `font-heavy` | Display, marketing |

### Line Height

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `leading-none` | `leading-none` | Display text, single-line |
| `leading-tight` | `leading-tight` | Headings |
| `leading-snug` | `leading-snug` | Subheadings |
| `leading-normal` | `leading-normal` | Body text |
| `leading-relaxed` | `leading-relaxed` | Long-form content |
| `leading-loose` | `leading-loose` | Legal, fine print |

### Letter Spacing

| Hardcoded | Semantic |
|-----------|----------|
| `tracking-tighter` | `tracking-heading` |
| `tracking-tight` | `tracking-heading` |
| `tracking-normal` | `tracking-body` |
| `tracking-wide` | `tracking-label` |
| `tracking-wider` | `tracking-label` |
| `tracking-widest` + `uppercase` | `tracking-overline` |

### Composite Typography Patterns

Match multi-class patterns before individual classes. Apply the first matching composite rule.

| Hardcoded Pattern | Semantic |
|-------------------|----------|
| `text-6xl+ font-bold/extrabold` | `text-display` |
| `text-4xl font-bold tracking-tight` | `text-heading-xl` |
| `text-3xl font-semibold` | `text-title` |
| `text-2xl font-semibold` | `text-subtitle` |
| `text-lg font-medium` | `text-lead` |
| `text-base` | `text-body` |
| `text-sm text-gray-*` | `text-muted` |
| `text-xs uppercase tracking-wide` | `text-overline` |
| `text-xs font-medium` | `text-label` |

---

## Spacing Rules

### Semantic Spacing Scale

| Hardcoded | Semantic | Value |
|-----------|----------|-------|
| `p-1`, `m-1` | `space-xs` | 4px |
| `p-2`, `m-2` | `space-sm` | 8px |
| `p-3`, `m-3` | `space-md` | 12px |
| `p-4`, `m-4` | `space-lg` | 16px |
| `p-5`, `m-5` | `space-xl` | 20px |
| `p-6`, `m-6` | `space-2xl` | 24px |
| `p-8`, `m-8` | `space-3xl` | 32px |
| `p-10`, `m-10` | `space-4xl` | 40px |
| `p-12`, `m-12` | `space-5xl` | 48px |

### Component Spacing Patterns

| Context | Recommended Token |
|---------|-------------------|
| Button padding | `px-button py-button` or `p-4` |
| Card padding | `p-card` or `p-6` |
| Section padding | `p-section` or `py-12 px-6` |
| Input padding | `px-input py-input` or `px-4 py-2` |
| Gap between items | `gap-sm` (8px), `gap-md` (12px), `gap-lg` (16px) |
| Stack spacing | `space-y-sm`, `space-y-md`, `space-y-lg` |

---

## Sizing Rules

### Width/Height

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `w-4 h-4` | `size-icon-xs` | Small icons |
| `w-5 h-5` | `size-icon-sm` | Default icons |
| `w-6 h-6` | `size-icon-md` | Medium icons |
| `w-8 h-8` | `size-icon-lg` | Large icons |
| `w-10 h-10` | `size-avatar-sm` | Small avatars |
| `w-12 h-12` | `size-avatar-md` | Medium avatars |
| `w-16 h-16` | `size-avatar-lg` | Large avatars |
| `h-10`, `h-11` | `h-input` | Input/button height |
| `max-w-sm` | `max-w-form` | Form container |
| `max-w-xl` | `max-w-content` | Content container |
| `max-w-5xl` | `max-w-page` | Page container |

### Border Radius

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `rounded` | `rounded-sm` | Subtle rounding |
| `rounded-md` | `rounded-base` | Default rounding |
| `rounded-lg` | `rounded-lg` | Cards, modals |
| `rounded-xl` | `rounded-xl` | Large cards |
| `rounded-2xl` | `rounded-2xl` | Hero sections |
| `rounded-full` | `rounded-full` | Pills, avatars |

---

## Shadow Rules

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `shadow-sm` | `shadow-sm` | Subtle elevation |
| `shadow` | `shadow-base` | Default elevation |
| `shadow-md` | `shadow-md` | Cards |
| `shadow-lg` | `shadow-lg` | Modals, dropdowns |
| `shadow-xl` | `shadow-xl` | Popovers |
| `shadow-2xl` | `shadow-2xl` | Floating elements |
| `shadow-success` | `shadow-success` | Success glow |
| `shadow-error` | `shadow-error` | Error glow |

---

## Z-Index Rules

| Hardcoded | Semantic | Use Case |
|-----------|----------|----------|
| `z-0` | `z-base` | Default layer |
| `z-10` | `z-dropdown` | Dropdowns |
| `z-20` | `z-sticky` | Sticky headers |
| `z-30` | `z-overlay` | Overlays |
| `z-40` | `z-modal` | Modals |
| `z-50` | `z-toast` | Toasts, tooltips |

---

## Inline Style Replacements

| Hardcoded | Semantic |
|-----------|----------|
| `style={{ color: '#111827' }}` | `className="text-foreground"` |
| `style={{ color: '#6b7280' }}` | `className="text-muted-foreground"` |
| `style={{ backgroundColor: '#ffffff' }}` | `var(--color-background)` |
| `style={{ fontSize: '14px' }}` | `var(--text-body-sm)` |
| `style={{ fontWeight: 600 }}` | `className="font-semibold"` |
| `style={{ padding: '16px' }}` | `className="p-4"` or `var(--space-lg)` |
| `style={{ borderRadius: '8px' }}` | `var(--radius-base)` |

---

## Third-Party Config Pattern

When a library requires specific values at initialization, use runtime CSS variable resolution:

```js
function cssVar(name, fallback) {
  if (typeof window === 'undefined') return fallback;
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name).trim() || fallback;
}

// Usage: cssVar('--color-brand', '#F97316')
```

Initialize in `useEffect` (not module level) so CSS variables are available.

---

## Scoped Token Pattern

When a page has a fixed dark background that doesn't change with theme, use `var()` with inline fallback:

```js
color: 'var(--status-text-muted, #a1a1aa)'
```

---

## Status Mapping

| Status | Semantic |
|--------|----------|
| `DRAFT` | `muted` |
| `PENDING`, `SUBMITTED` | `warning` |
| `CONFIRMED`, `SUCCESS`, `COMPLETED`, `PAID` | `success` |
| `REJECTED`, `ERROR`, `CANCELLED` | `error` |
| `INFO`, `SENT`, `RECEIVED` | `info` |

---

## Available Tokens Reference

### Colors
**Text:** `text-foreground`, `text-muted-foreground`, `text-primary`, `text-primary-foreground`, `text-brand`, `text-brand-foreground`, `text-accent`, `text-success`, `text-success-foreground`, `text-warning`, `text-warning-foreground`, `text-error`, `text-error-foreground`, `text-info`, `text-info-foreground`

**Background:** `bg-background`, `bg-card`, `bg-muted`, `bg-primary`, `bg-brand`, `bg-accent`, `bg-success`, `bg-warning`, `bg-error`, `bg-info`, `bg-overlay`

**Border:** `border-border`, `border-input`, `border-primary`, `border-brand`, `border-success`, `border-error`, `border-warning`, `border-info`

**Ring:** `ring-primary`, `ring-success`, `ring-error`, `ring-info`

**Shadow:** `shadow-success`, `shadow-error`, `shadow-info`

**Misc:** `divide-border`, `placeholder-muted-foreground`

### Typography
**Font Family:** `font-body`, `font-heading`, `font-mono`, `font-display`

**Font Size:** `text-caption`, `text-body-sm`, `text-body`, `text-body-lg`, `text-heading-sm`, `text-heading-md`, `text-heading-lg`, `text-heading-xl`, `text-display`

**Composite:** `text-title`, `text-subtitle`, `text-lead`, `text-muted`, `text-overline`, `text-label`

**Font Weight:** `font-thin`, `font-light`, `font-normal`, `font-medium`, `font-semibold`, `font-bold`, `font-heavy`

**Letter Spacing:** `tracking-heading`, `tracking-body`, `tracking-label`, `tracking-overline`

**Line Height:** `leading-none`, `leading-tight`, `leading-snug`, `leading-normal`, `leading-relaxed`, `leading-loose`

### Spacing
**Padding/Margin:** `space-xs`, `space-sm`, `space-md`, `space-lg`, `space-xl`, `space-2xl`, `space-3xl`, `space-4xl`, `space-5xl`

**Component:** `p-card`, `p-section`, `p-input`, `px-button`, `py-button`

**Gap:** `gap-xs`, `gap-sm`, `gap-md`, `gap-lg`, `gap-xl`

**Stack:** `space-y-sm`, `space-y-md`, `space-y-lg`

### Sizing
**Icons:** `size-icon-xs`, `size-icon-sm`, `size-icon-md`, `size-icon-lg`

**Avatars:** `size-avatar-sm`, `size-avatar-md`, `size-avatar-lg`

**Containers:** `max-w-form`, `max-w-content`, `max-w-page`

**Input:** `h-input`

### Effects
**Radius:** `rounded-sm`, `rounded-base`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-full`

**Shadow:** `shadow-sm`, `shadow-base`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-2xl`

**Z-Index:** `z-base`, `z-dropdown`, `z-sticky`, `z-overlay`, `z-modal`, `z-toast`

---

## Behavior

For each `.tsx`, `.jsx`, `.ts`, `.js` file in the target path (skip excluded dirs):

1. Read the file
2. Find hardcoded styles (colors, fonts, sizes, spacing)
3. Check if inside protected context (gradient/SVG-def/animation)
4. If safe → apply matching rule and edit immediately
5. If protected context → skip, log as `⚠ skipped`

After all files are done, re-scan to verify zero remaining violations. Print summary.

## Summary Format

```
Semantic coding refactor: N files changed, M replacements
- file.tsx: colors (5), typography (3), spacing (2)
⚠ file.tsx:42 — skipped (gradient context)
⚠ file.tsx:88 — skipped (SVG defs)
```
