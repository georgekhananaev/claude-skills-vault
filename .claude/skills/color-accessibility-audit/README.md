# Color Contrast Analyzer — Claude Skill

A Claude Skill that analyzes whether text and background color combinations are readable and accessible, based on the **WCAG 2.1/2.2** standards. It detects visually indistinct color pairs that make text hard to read, checks compliance at multiple levels, auto-suggests fixes, and simulates color blindness.

---

## Why This Exists

One of the most common accessibility failures on the web is poor contrast between text and its background. Light gray text on a white background, dark gray on near-black, or colored text on a similarly-saturated background — these can look fine on a designer's high-end monitor but become illegible for users with low vision, older displays, bright ambient light, or color vision deficiency. This skill catches those problems before they ship.

---

## Core Concepts

### What Is Contrast Ratio?

Contrast ratio is a number from **1:1** (identical colors, invisible text) to **21:1** (pure black on pure white, maximum contrast). It measures how easy it is to distinguish the foreground from the background.

The ratio is derived from the **relative luminance** of each color — essentially, how bright a color appears to the human eye, weighted by how our eyes perceive red, green, and blue light differently.

### The Luminance Formula

Every analysis in this skill is grounded in this formula from the WCAG specification:

**Step 1** — Convert each sRGB color channel to linear light:

```
if value ≤ 0.04045 → linear = value / 12.92
if value > 0.04045 → linear = ((value + 0.055) / 1.055) ^ 2.4
```

**Step 2** — Calculate relative luminance using perceptual weights:

```
L = 0.2126 × R + 0.7152 × G + 0.0722 × B
```

Green contributes the most to perceived brightness (71.52%), which is why green text on a green background is particularly dangerous — even slightly different greens can have very similar luminance values.

**Step 3** — Calculate the contrast ratio:

```
Ratio = (L_lighter + 0.05) / (L_darker + 0.05)
```

The 0.05 offset prevents division by zero and accounts for ambient light.

### WCAG Thresholds

The Web Content Accessibility Guidelines define two conformance levels across two text size categories:

| | Body Text (< 18pt) | Large Text (≥ 18pt or ≥ 14pt bold) |
|---|---|---|
| **Level AA** (SC 1.4.3) | 4.5 : 1 | 3.0 : 1 |
| **Level AAA** (SC 1.4.6) | 7.0 : 1 | 4.5 : 1 |

**AA** is the minimum legal standard in many jurisdictions. **AAA** is the enhanced standard recommended for long-form reading, healthcare, government, and education. Large text gets relaxed thresholds because bigger letterforms are inherently easier to perceive.

For **non-text UI elements** (buttons, icons, form fields), WCAG SC 1.4.11 requires at least **3:1** contrast against adjacent colors.

### Color Blindness (Color Vision Deficiency)

Approximately **8% of men** and **0.5% of women** have some form of color vision deficiency (CVD). The most common types are:

| Type | What Happens | Who's Affected |
|---|---|---|
| **Deuteranomaly** | Reduced green sensitivity | ~5% of men |
| **Protanopia** | No red cones — reds appear dark/muddy | ~1% of men |
| **Deuteranopia** | No green cones — red-green confusion | ~1% of men |
| **Protanomaly** | Reduced red sensitivity | ~1% of men |
| **Tritanopia** | No blue cones — blue-yellow confusion | ~0.003% |

This skill simulates Protanopia, Deuteranopia, and Tritanopia using the **Brettel/Viénot/Mollon** transformation matrices, which mathematically model how each deficiency alters color perception. After simulation, it recalculates contrast ratios to detect pairs that pass for normal vision but fail for color-blind users. It also calculates **ΔE** (perceptual color difference in CIELAB space) to flag when two colors become nearly indistinguishable.

---

## What the Skill Does

When triggered, the skill performs a four-stage analysis on every text/background pair:

### 1. Input Parsing

Accepts colors in any common format and normalizes to hex internally:

- **Hex**: `#3a7bd5`, `#fff`, `#3a7bd5cc` (alpha stripped with warning)
- **RGB / RGBA**: `rgb(58, 123, 213)`, `rgba(58, 123, 213, 0.8)`
- **HSL / HSLA**: `hsl(210, 65%, 53%)`
- **Named CSS colors**: `coral`, `slategray`, `tomato`
- **Tailwind classes**: `text-blue-500`, `bg-gray-100` (mapped to hex via built-in palette)

### 2. Contrast Ratio & WCAG Check

Calculates the precise contrast ratio and evaluates it against all four WCAG thresholds (AA body, AA large, AAA body, AAA large). Reports a clear pass/fail for each.

### 3. The Fixer (Auto-Correction)

When a pair fails, the skill doesn't just say "this is broken." It provides the **nearest safe hex code** that passes — preserving the designer's chosen hue and saturation. The algorithm works by converting the failing color to HSL, holding hue and saturation constant, and binary-searching the lightness channel until it finds the minimum adjustment that hits the target ratio. It provides separate fixes for AA and AAA.

### 4. Color Blindness Simulation

Transforms both colors through CVD simulation matrices for Protanopia, Deuteranopia, and Tritanopia, then recalculates contrast. Flags any pair where contrast drops below threshold or where the ΔE falls below 10 (meaning the colors become hard to tell apart). Also detects high-risk hue combinations like red-on-green regardless of contrast ratio.

---

## Skill File Structure

```
color-contrast-analyzer/
├── SKILL.md                                  # Main skill definition (Claude reads this)
├── README.md                                 # This file
├── scripts/
│   ├── contrast_check.py                     # CLI — individual color pair analysis
│   ├── scan_css.py                           # Scanner — CSS files (globals.css, styles)
│   ├── scan_js.py                            # Scanner — JS/TS (themes, tokens, configs)
│   ├── scan_tailwind.py                      # Scanner — Tailwind classes in JSX/TSX
│   └── scan_svg.py                           # Scanner — SVG fill/stroke/text colors
└── references/
    ├── color-parsing.md                      # Color format conversion tables
    ├── color-blindness-matrices.md           # CVD simulation matrices & ΔE
    └── artifact-template.md                  # React component template
```

**SKILL.md** is the core — it contains the system prompt that tells Claude how to behave when the skill triggers. The `references/` directory contains supplementary data Claude loads on demand. The `scripts/` directory contains a standalone Python tool.

---

## How to Install

Copy the entire `color-contrast-analyzer/` folder into your Claude skills directory:

```bash
cp -r color-contrast-analyzer/ /mnt/skills/user/color-contrast-analyzer/
```

The skill triggers automatically when Claude detects color-related queries in conversation.

---

## How to Use

### In Conversation with Claude

Just talk to Claude about colors. The skill triggers automatically for any of these scenarios:

**Direct color check:**
> "Is `#9ca3af` readable on `#f3f4f6`?"

**CSS / Tailwind review:**
> "Can you check the contrast in this CSS?"
> ```css
> .card { background: #f8f9fa; color: #adb5bd; }
> ```

**Design review:**
> "I'm using `text-gray-400` on `bg-white` for placeholder text. Is that accessible?"

**Screenshot analysis:**
> *[upload a UI screenshot]*
> "The text on this banner looks hard to read. Can you check?"

**Palette audit:**
> "Here's my color palette: primary #2563eb, background #eff6ff, text #94a3b8. Check all combinations."

### Scanning a CSS File

This is the most powerful feature — point the scanner at any CSS file and it finds every contrast issue automatically:

```bash
# Basic scan
python3 scripts/scan_css.py global.css

# With color blindness simulation
python3 scripts/scan_css.py src/styles/global.css --cvd

# JSON output for CI/CD pipelines
python3 scripts/scan_css.py theme.css --json > contrast-report.json
```

**What the scanner does:**

1. Parses every CSS rule in the file
2. Resolves `var(--custom-properties)` defined in `:root` or anywhere else
3. Extracts `color` + `background-color` pairs per selector
4. Infers background from parent selectors when a rule only sets text color (falls back to white)
5. Checks `border-color` against backgrounds for non-text contrast (WCAG SC 1.4.11)
6. Handles `@media` blocks including `prefers-color-scheme: dark`
7. Deduplicates identical color pairs
8. Runs the full analysis on every pair: contrast ratio, WCAG AA/AAA, The Fixer, optional CVD
9. Groups results by severity — failures first, then AA-only warnings, then passing

**Supported CSS patterns:**

- Standard properties: `color`, `background-color`, `background`, `border-color`
- CSS custom properties: `var(--primary)`, `var(--text-muted, #888)` with fallback
- All color formats: `#hex`, `rgb()`, `rgba()`, `hsl()`, `hsla()`, named colors
- Nested `@media`, `@layer`, `@supports` blocks (flattened automatically)
- Pseudo-selectors like `:hover`, `:focus`, `:disabled`

**Example output:**

```
════════════════════════════════════════════════════════════
  COLOR CONTRAST SCAN REPORT
  File: global.css
════════════════════════════════════════════════════════════

  Found 16 color pairs across 14 selectors

  ❌ FAIL AA:         11 pairs
  ⚠️  Pass AA only:   1 pairs
  ✅ Pass AAA:        4 pairs

────────────────────────────────────────────────────────────
  ❌ FAILING PAIRS (below AA 4.5:1)
────────────────────────────────────────────────────────────

    Selector:   .input-placeholder
    Text:        #d1d5db
    Background:  #ffffff
    Contrast:    1.47:1
    AA Body: ❌  AA Large: ❌  AAA Body: ❌  AAA Large: ❌
    Fix for AA:  #6b7789  →  4.54:1
    Fix for AAA: #515a67  →  6.98:1
```

Every failing pair includes a ready-to-copy fix hex code. Just swap the suggested color into your CSS.

### Scanning JS/TS Files (Themes, Tokens, Configs)

The JS/TS scanner handles all the places colors live in modern JavaScript and TypeScript projects:

```bash
# Single file
python3 scripts/scan_js.py theme.ts
python3 scripts/scan_js.py tailwind.config.js --cvd

# Directory (top-level files)
python3 scripts/scan_js.py src/styles/

# Recursive (all JS/TS files in tree, skips node_modules)
python3 scripts/scan_js.py src/ --recursive

# JSON for CI/CD
python3 scripts/scan_js.py src/ -r --json > contrast-report.json
```

**What it detects:**

- **Theme objects** — MUI, Chakra, Mantine, Shadcn, custom themes with `palette.primary.main`, `colors.text.secondary`, etc.
- **Design tokens** — Style Dictionary, Tokens Studio, or any `tokens = { textColor: '#hex', bgColor: '#hex' }` pattern
- **Tailwind config** — `tailwind.config.js/ts` color extensions like `primary: '#6366f1'`
- **Inline styles** — React JSX `style={{ color: '#hex', backgroundColor: '#hex' }}`
- **CSS-in-JS** — Styled-components, Emotion, Stitches color definitions
- **Constants / enums** — `const PRIMARY_COLOR = '#3b82f6'` and similar patterns

**Smart pairing logic:**

The scanner classifies each key semantically — `color`, `textMuted`, `foreground` get tagged as text colors; `background`, `bg`, `surface`, `paper` get tagged as background. It then groups entries by their nesting context (e.g., everything inside `palette.primary` is one group) and pairs text with background within each group. It also understands the `onPrimary`/`primary` naming convention used by Material Design.

**Example output:**

```
════════════════════════════════════════════════════════════
  JS/TS COLOR CONTRAST SCAN REPORT
  Source: theme.ts
════════════════════════════════════════════════════════════

  Found 31 color pairs

  ❌ FAIL AA:         20 pairs
  ⚠️  Pass AA only:   2 pairs
  ✅ Pass AAA:        9 pairs

────────────────────────────────────────────────────────────
  ❌ FAILING PAIRS (below AA 4.5:1)
────────────────────────────────────────────────────────────

    Context:     error
    Source:      inline_style: color + backgroundColor
    Text:        #ef4444  ← error.color  (text L70, bg L70)
    Background:  #22c55e  ← error.backgroundColor
    Contrast:    1.65:1
    AA Body: ❌  AA Large: ❌  AAA Body: ❌  AAA Large: ❌
    Fix for AA:  #850b0b  →  4.5:1
    ⚠️  RED-GREEN combination — critical risk for Protanopia & Deuteranopia
```

Each issue traces back to the exact key path and line number in your source file.

**Supported file types:** `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`

### Scanning Tailwind Classes in JSX/TSX

This scanner reads your actual components and extracts `text-*`, `bg-*`, and `border-*` Tailwind classes, resolves them to hex using the full Tailwind v3 palette, and pairs them per element:

```bash
# Single component
python3 scripts/scan_tailwind.py src/components/Button.tsx

# Whole project
python3 scripts/scan_tailwind.py src/ --recursive --cvd

# With Tailwind class replacement suggestions
python3 scripts/scan_tailwind.py src/ -r --fix

# JSON for CI/CD
python3 scripts/scan_tailwind.py src/ -r --json > report.json
```

**What it detects:**

- `className="text-gray-400 bg-white"` — standard class attributes
- `className={cn('text-red-500', 'bg-green-200')}` — clsx, cn, twMerge, classNames, cva utility functions
- `tw\`text-blue-400 bg-white\`` — tagged template literals
- Ternary patterns: `isActive ? 'text-white bg-blue-600' : 'text-gray-500'`
- Variant prefixes: `dark:text-gray-300`, `hover:text-blue-100`, `focus:bg-blue-50`
- Border contrast: `border-gray-200 bg-white`

**Smart features:**

The `--fix` flag doesn't just suggest hex codes — it suggests **replacement Tailwind classes**. For example:
```
text-gray-400 on bg-white → 2.54:1 ❌
Fix AA: use text-gray-500 → 4.51:1 ✅
```

It groups variant classes separately, so `hover:text-blue-100 hover:bg-blue-50` is checked as its own pair (1.12:1 — near invisible on hover!).

**Full Tailwind v3 palette coverage:** gray, slate, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose — all 22 color scales, all shades 50–950.

### Scanning SVG Files

Checks SVG icons, illustrations, and inline SVG components for fill/stroke/text contrast:

```bash
# Single SVG
python3 scripts/scan_svg.py icon.svg

# All SVGs in a directory
python3 scripts/scan_svg.py public/icons/ --recursive --cvd

# Also finds inline SVGs in JSX/TSX components
python3 scripts/scan_svg.py src/ -r --json > report.json
```

**What it detects:**

- `fill` and `stroke` attributes on all SVG elements
- Inline `style="fill: #hex; stroke: #hex"` attributes
- `<text>` and `<tspan>` elements (checked at SC 1.4.3 text threshold: 4.5:1)
- Graphical elements like `<rect>`, `<circle>`, `<path>` (checked at SC 1.4.11 non-text threshold: 3:1)
- Stroke-vs-fill contrast (is the border distinguishable from the shape?)
- Stroke-vs-background contrast
- `<g>` group inheritance (parent fill/stroke flows to children)
- `currentColor` usage flagged for manual review

**Also scans inline SVGs** in JSX/TSX files — those `<svg>` blocks inside your React components.

### Full Project Scan (All 4 Scanners)

For maximum coverage, run all scanners on your `src/` directory:

```bash
# CSS files (globals.css, module styles)
python3 scripts/scan_css.py src/ --cvd

# Theme files, design tokens, configs
python3 scripts/scan_js.py src/ --recursive --cvd

# Tailwind classes in components
python3 scripts/scan_tailwind.py src/ --recursive --cvd --fix

# SVG icons and inline SVGs
python3 scripts/scan_svg.py src/ --recursive --cvd
```

Or ask Claude to do it in one prompt — it will choose the right scanner(s) automatically.

### Using the CLI Script for Individual Pairs

For batch analysis or integration into a build pipeline:

```bash
# Basic check — one pair
python3 scripts/contrast_check.py "#9ca3af" "#f3f4f6"

# Multiple pairs
python3 scripts/contrast_check.py "#333" "#fff" "#ccc" "#f0f0f0" "#1a1a1a" "#fff"

# With color blindness simulation
python3 scripts/contrast_check.py --cvd "#e53e3e" "#38a169"

# JSON output (for piping to other tools)
python3 scripts/contrast_check.py --json "#333" "#fff"

# Full analysis — multiple pairs, CVD, JSON
python3 scripts/contrast_check.py --cvd --json "#9ca3af" "#f3f4f6" "#e53e3e" "#38a169"
```

**Arguments:**
- Colors are provided in pairs: `<text_color> <background_color>`
- You can provide as many pairs as needed
- `--cvd` enables color blindness simulation (Protanopia, Deuteranopia, Tritanopia)
- `--json` outputs structured JSON instead of the formatted report
- Accepts hex codes (3 or 6 digit) and named CSS colors

### Reading the Output

Here's what a typical analysis looks like:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PAIR 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Text:       #9ca3af
  Background: #f3f4f6
  Contrast:   2.31:1

  WCAG Compliance:
    AA  Body Text  (4.5:1): ❌ Fail
    AA  Large Text (3.0:1): ❌ Fail
    AAA Body Text  (7.0:1): ❌ Fail
    AAA Large Text (4.5:1): ❌ Fail

  Fixes:
    → For AA:  change text to #687181 (ratio 4.47:1)
    → For AAA: change text to #4d535f (ratio 7.02:1)

  Color Blindness Impact:
    🔴 protanopia       2.29:1  ΔE= 29.7  ⚠️  HIGH RISK
    🟢 deuteranopia     2.32:1  ΔE= 30.1  ⚠️  HIGH RISK
    🔵 tritanopia       2.30:1  ΔE= 29.6  ⚠️  HIGH RISK
```

The Fixer tells you exactly which hex code to swap in. Copy `#687181` to meet AA, or `#4d535f` for the stricter AAA — the hue stays the same, only the lightness changes.

---

## Real-World Usage Scenarios

These are copy-paste prompts you can use with Claude to scan and fix colors in real projects. No need to mention the skill by name — just upload your files or describe your project and Claude handles the rest.

### Scenario 1: Scan and Report Only

Upload your project files (or reference the paths) and ask:

> Scan my Next.js project for color contrast and accessibility issues. Check all CSS, JS, and TS files in `src/` for any text/background color combinations that fail WCAG AA or AAA. Include color blindness analysis.

Claude will scan every file, list every failing pair with its file path, line number, contrast ratio, and WCAG pass/fail status, then summarize the results.

### Scenario 2: Scan and Auto-Fix Everything

> Scan my Next.js project for all color contrast issues in `src/`. For every failing pair, automatically replace the colors in the source files with the nearest WCAG AA-compliant fix. Preserve the original hue — only adjust lightness. Show me a before/after summary when done.

Claude will find the issues, compute the minimum-adjustment fix for each, update the actual source files, and give you a changelog.

### Scenario 3: Target Specific Files

> Check `src/styles/globals.css` and `src/lib/theme.ts` for color contrast problems. Fix any pair that fails WCAG AA by updating the hex codes directly in the files. Keep the design intent — only darken or lighten as needed.

### Scenario 4: Full Project Audit with Priorities

> Do a full accessibility color audit on my Next.js project:
> 1. Scan all CSS, JS, and TS files in `src/` recursively
> 2. List every failing color pair with its file, line number, and contrast ratio
> 3. Auto-fix all pairs that fail AA — update the actual source files
> 4. For pairs that pass AA but fail AAA, list them as warnings but don't change them
> 5. Flag any red/green combinations that are risky for color-blind users
> 6. Give me a summary of what was changed

### Scenario 5: Dark Mode Audit

> My Next.js app has a dark mode. Scan `src/styles/globals.css` and `src/lib/theme.ts` for any dark mode color pairs that fail WCAG AA. Check both the light and dark theme tokens. Fix the dark mode issues — the light mode is fine.

### Scenario 6: Component-Level Check

> I just built a new `<StatusBadge>` component. Here's the code:
> *(paste your component)*
> Check if all the color combinations in the badge variants are accessible. Fix any that fail.

### Scenario 7: Tailwind Config Audit

> Scan my `tailwind.config.ts` for accessibility issues. Check every color in the `theme.extend.colors` section against both white and dark backgrounds. Flag any that would fail WCAG AA as body text.

### Scenario 8: Pre-Launch Accessibility Check

> I'm about to launch my site. Do a final color accessibility pass:
> 1. Scan all files in `src/` recursively
> 2. Fix any AA failures automatically
> 3. Generate a report I can share with the team showing what was changed and what still needs attention at AAA level
> 4. Flag any color-blind risks

### Scenario 9: Design Token Review

> Here's my design token file. Check every text/background pair for WCAG compliance. For tokens that fail, suggest replacement values that keep the same hue but pass AA. Output the corrected token file.

### Scenario 10: Fix Only What I Tell You

> Scan `src/styles/globals.css` for contrast issues but DON'T auto-fix anything. Just give me the report. I'll decide which ones to fix.

### Key Phrases That Trigger the Skill

You don't need to use these exact words, but any of these naturally trigger the analysis:

- "color contrast" or "accessibility" or "WCAG"
- "hard to read" or "can't see the text"
- "check the colors" or "audit colors"
- "scan" + any CSS / JS / TS file
- "fix the contrast" or "fix the colors"
- Uploading any `.css`, `.js`, `.ts`, `.jsx`, `.tsx` file with color definitions
- Pasting code that contains hex codes, `rgb()`, `hsl()`, or color property names

---

## Common Failures This Catches

These are the patterns the skill is specifically tuned to detect:

- **Light gray on white** — The number one offender. `#aaa` on `#fff` is only 2.32:1. Looks subtle and "clean" but fails every WCAG threshold.
- **Placeholder text** — Input hints styled at 40–50% opacity or very light gray. Often completely invisible to low-vision users.
- **Dark mode dark-on-dark** — Dark gray text (`#555`) on a near-black background (`#1a1a1a`). Developers test on bright screens and miss it.
- **Colored text on colored backgrounds** — A blue link on a blue-tinted card. Looks fine in Figma, fails in the real world.
- **Red/green status indicators** — Using only color to show success/error, which is invisible to the 6% of men with red-green CVD.
- **Hover states that reduce contrast** — A button that goes from dark text to a lighter tint on hover, dropping below threshold.
- **Thin font weights** — Text at font-weight 200 or 300 reduces perceived contrast even when the ratio technically passes.
- **Text over images/gradients** — No solid scrim behind the text means the contrast varies across the element.

---

## Reference Files

### `references/color-parsing.md`

Contains the full lookup tables for converting between color formats: hex shorthand expansion, HSL-to-RGB conversion algorithm, named CSS color mappings (50+ colors), and Tailwind v3 default palette values for gray, slate, red, blue, green, and yellow scales.

### `references/color-blindness-matrices.md`

Contains the 3×3 transformation matrices for all five CVD types (Protanopia, Deuteranopia, Tritanopia, Protanomaly, Deuteranomaly), the ΔE (CIE76) calculation method, risk thresholds (ΔE < 3 = critical, < 10 = high), and a quick-reference risk table for common color pairings.

### `references/artifact-template.md`

Contains a ready-to-use React component template for generating an interactive visual contrast checker as a Claude artifact. Includes color picker inputs, live preview swatches at multiple text sizes, contrast ratio display with pass/fail badges, and the Fixer suggestions inline.

---

## Standards Reference

This skill implements checks against the following WCAG 2.1/2.2 Success Criteria:

| SC | Name | What It Covers |
|---|---|---|
| 1.4.3 | Contrast (Minimum) | Level AA — 4.5:1 for body text, 3:1 for large text |
| 1.4.6 | Contrast (Enhanced) | Level AAA — 7:1 for body text, 4.5:1 for large text |
| 1.4.11 | Non-text Contrast | Level AA — 3:1 for UI components and graphics |
| 1.4.1 | Use of Color | Do not use color as the only visual means of conveying information |

For the full specification, see: https://www.w3.org/TR/WCAG22/
