# Semantic Coding

### Automated Refactoring of Hardcoded Styles to Semantic Design Tokens

> Refactored from `semantic-colors` (color-only) into a comprehensive design system skill covering colors, typography, spacing, sizing, shadows, and z-index.

---

## Why Semantic Tokens?

Instead of describing **what value** something has, describe **what it means**.

```
Hardcoded:   text-red-500         "I am red shade 500"
Semantic:    text-error           "I am an error message"

Hardcoded:   text-2xl             "I am 24px font"
Semantic:    text-heading-md      "I am a section heading"

Hardcoded:   p-4                  "I am 16px padding"
Semantic:    p-card               "I am card padding"
```

**Benefits:**
- **Dark mode for free** - tokens resolve per theme, no `dark:` overrides
- **One source of truth** - change `globals.css`, everything follows
- **Consistent UI** - no more 4 different "error reds" across the app
- **Safe redesigns** - brand color change = 1 file, not 50

---

## How It Works

```
/semantic-coding [path]
```

For each `.tsx`, `.jsx`, `.ts`, `.js` file:

1. Find hardcoded values (colors, typography, spacing, sizing)
2. Check if inside protected context (gradient/SVG/animation/template literal/arbitrary value)
3. Safe → apply rule and edit. Protected → skip and log.
4. Re-scan to verify zero remaining violations.

All conversions are **rule-based and deterministic**. See `SKILL.md` for the complete rule tables.

---

## What It Covers

| Category | Examples |
|----------|----------|
| **Colors** | `text-red-*` → `text-error`, `bg-gray-*` → `bg-muted`, all Tailwind palettes |
| **Typography** | `text-2xl` → `text-heading-md`, `text-6xl+` → `text-display`, composites |
| **Spacing** | `p-4` → `space-lg`, `gap-3` → `gap-md`, component patterns (`p-card`) |
| **Sizing** | `w-5 h-5` → `size-icon-sm`, `h-10` → `h-input`, containers |
| **Effects** | `shadow-emerald-*` → `shadow-success`, `z-40` → `z-modal` |
| **Dark mode** | Collapses `text-green-600 dark:text-green-400` → `text-success` |
| **Inline styles** | `style={{ color: '#6b7280' }}` → `className="text-muted-foreground"` |
| **Third-party** | Runtime `cssVar()` resolution for Mermaid, charts, diagrams |
| **Misc** | `divide-gray-*` → `divide-border`, `placeholder-gray-*` → `placeholder-muted-foreground` |

---

## Safety Guarantees

The skill **never** touches values inside protected contexts:

- **Gradients** - `linear-gradient()`, `from-*`, `via-*`, `to-*`
- **SVG defs** - `<linearGradient>`, `<radialGradient>`, `<stop>`
- **Animations** - `@keyframes`, transform values
- **Glass morphism** - `rgba(255,255,255,0.0x)` overlays
- **Template literals** - `` `border-${color}-500` ``, dynamic class construction
- **Arbitrary values** - `bg-[#hex]`, `text-[14px]` (JIT bracket syntax)
- **Component props** - Non-className color props (e.g., `<Button color="red-500" />`)
- **Token sources** - `globals.css`, `tailwind.config.*`, `tokens.ts`, `theme.ts`
- **Test files** - `__tests__/`, `*.test.*`, `*.spec.*`

Protected matches are logged as `⚠ skipped (protected context)`.

---

## Brand Color Configuration

The default mappings assume `orange`=brand and `blue`=info. If your project uses a different brand color (e.g., blue or indigo), adjust the color family mappings before running. See the note in `SKILL.md` > Color Rules.

---

## Examples

### Dark Mode Collapse

```diff
- className="text-green-600 dark:text-green-400"
+ className="text-success"

- className="bg-red-100 dark:bg-red-900/20 border-red-200 dark:border-red-800"
+ className="bg-error/10 border-error"
```

### Inline Styles

```diff
- style={{ color: '#6b7280' }}
+ className="text-muted-foreground"

- style={{ backgroundColor: '#9ca3af' }}
+ style={{ backgroundColor: 'var(--color-muted)' }}
```

### Third-Party Config (Mermaid)

```diff
- primaryColor: '#2563eb',
+ primaryColor: cssVar('--color-brand', '#2563eb'),
```

---

## Output Format

```
Semantic coding refactor: N files changed, M replacements
- file.tsx: colors (5), typography (3), spacing (2)
⚠ file.tsx:42 — skipped (gradient context)
⚠ file.tsx:88 — skipped (SVG defs)
```

---

## Key Takeaways

1. **Semantic tokens describe intent, not appearance** - `text-error` not `text-red-500`
2. **One source of truth** - change design in `globals.css`, everything follows
3. **Dark mode for free** - semantic tokens resolve to the correct value per theme
4. **Protected contexts are sacred** - never breaks gradients, animations, or dynamic classes
5. **Deterministic** - rule-based, same input = same output
6. **Comprehensive** - colors, typography, spacing, sizing, shadows, z-index
7. **Configurable** - brand color mapping adapts to your project's palette

See `SKILL.md` for complete rule tables and token reference.
