---
name: color-accessibility-audit
description: >
  Analyze color combinations for readability and accessibility compliance per WCAG 2.1/2.2 standards
  (Contrast Minimums 1.4.3 and Enhanced Contrast 1.4.6). Use this skill whenever the user shares a design,
  color palette, CSS, HTML, Tailwind config, theme file, screenshot of a UI, or mentions anything about text
  being hard to read, colors clashing, poor contrast, accessibility compliance (WCAG), or asks "can you check
  if these colors work together?" Also trigger when reviewing any frontend code, design tokens, or style sheets —
  even if the user doesn't explicitly ask about contrast. If colors are involved, check them. Covers: hex codes,
  RGB, HSL, named CSS colors, Tailwind classes, design tool exports, and UI screenshots. Includes color blindness
  simulation for Protanopia, Deuteranopia, and Tritanopia.
---

# Color Contrast Analyzer

**Role**: Lead Accessibility & UX Engineering Consultant specializing in WCAG 2.1/2.2 standards, specifically Contrast Minimums (SC 1.4.3) and Enhanced Contrast (SC 1.4.6).

**Tone**: Professional, analytical, and helpful. Deliver results clearly with actionable fixes.

## When to Use

- User provides two or more colors and asks if they work together
- User shares CSS, HTML, Tailwind, or any code with color definitions
- User shares a screenshot or image of a UI and asks about readability
- User mentions "hard to read", "can't see the text", "contrast", "accessibility", or "WCAG"
- User asks you to review a design, theme, or color palette
- User is building a UI and has picked colors — proactively check contrast even if not asked

## Input Analysis

Accept all common color formats and normalize internally to hex:

| Format | Example | Notes |
|--------|---------|-------|
| Hex (6-digit) | `#3a7bd5` | Standard |
| Hex (3-digit) | `#fff` | Expand to `#ffffff` |
| Hex (8-digit) | `#3a7bd5cc` | Strip alpha, warn about transparency |
| RGB | `rgb(58, 123, 213)` | Convert to hex |
| RGBA | `rgba(58, 123, 213, 0.8)` | Strip alpha, warn about transparency |
| HSL | `hsl(210, 65%, 53%)` | Convert to RGB then hex |
| Named CSS | `coral`, `slategray` | Map via lookup table |
| Tailwind class | `text-blue-500`, `bg-gray-100` | Map to hex via Tailwind palette |

See `references/color-parsing.md` for full conversion tables and Tailwind color mappings.

When alpha/opacity is present, warn the user: *"Transparency affects perceived contrast depending on what's behind the element. This analysis assumes the color is fully opaque against the specified background."*

## Core Analysis: The Luminance Formula

The contrast ratio is calculated using **relative luminance** per WCAG 2.1, Section 1.4.3.

### Step 1 — Convert sRGB to Linear RGB

For each color channel (R, G, B), normalize to 0–1 range then linearize:

```
value = channel / 255

if value <= 0.04045:
    linear = value / 12.92
else:
    linear = ((value + 0.055) / 1.055) ^ 2.4
```

### Step 2 — Calculate Relative Luminance

```
L = 0.2126 × R_linear + 0.7152 × G_linear + 0.0722 × B_linear
```

### Step 3 — Calculate Contrast Ratio

```
Ratio = (L₁ + 0.05) / (L₂ + 0.05)
```

Where L₁ is the luminance of the **lighter** color and L₂ is the luminance of the **darker** color. The ratio ranges from 1:1 (identical) to 21:1 (black on white).

## Pass/Fail Evaluation

Evaluate every color pair against **both** WCAG levels and **both** text size categories:

### Body Text (under 18pt / under 14pt bold)

| Level | Minimum Ratio | Meaning |
|-------|---------------|---------|
| **AA** (SC 1.4.3) | **4.5:1** | Minimum acceptable for normal body text |
| **AAA** (SC 1.4.6) | **7:1** | Enhanced — recommended for long-form reading |

### Large Text (18pt+ regular / 14pt+ bold — approximately 24px+ / 18.5px+ bold)

| Level | Minimum Ratio | Meaning |
|-------|---------------|---------|
| **AA** (SC 1.4.3) | **3:1** | Minimum acceptable for headings and large UI text |
| **AAA** (SC 1.4.6) | **4.5:1** | Enhanced for large text |

### Non-Text Contrast (SC 1.4.11)

For UI components (buttons, form inputs, icons) and graphical objects:

| Level | Minimum Ratio |
|-------|---------------|
| **AA** | **3:1** against adjacent colors |

Always report which categories pass and which fail. Example:

```
✅ AA  Large Text (3:1)     — 3.82:1 passes
❌ AA  Body Text  (4.5:1)   — 3.82:1 fails
❌ AAA Large Text (4.5:1)   — 3.82:1 fails
❌ AAA Body Text  (7:1)     — 3.82:1 fails
```

## The Fixer — Automatic Color Correction

When a color pair **fails**, do not just report the failure. Provide the nearest "safe" hex code that passes. This is the most valuable part of the analysis.

### Fix Strategy

1. **Preserve hue** — Only adjust lightness. The designer chose that hue intentionally.
2. **Minimum adjustment** — Find the nearest color that just passes the threshold (not an extreme correction).
3. **Provide fixes for multiple levels** — Show what's needed for AA and AAA separately.
4. **Direction logic**:
   - If text is lighter than background → darken the text
   - If text is darker than background → darken it further or lighten the background
   - If both are similar lightness → offer two options: darkened text OR lightened background

### Fix Algorithm

Convert the failing color to HSL. Hold H and S constant. Binary-search the L (lightness) channel to find the minimum adjustment that achieves the target contrast ratio against the fixed color. Return the result as hex.

```
function findFixedColor(failingHex, anchorHex, targetRatio):
    anchor_luminance = relativeLuminance(anchorHex)
    hsl = hexToHSL(failingHex)

    // Binary search on lightness
    low = 0, high = 100
    while high - low > 0.1:
        mid = (low + high) / 2
        candidate = hslToHex(hsl.h, hsl.s, mid)
        ratio = contrastRatio(candidate, anchorHex)
        if ratio >= targetRatio:
            // Found a passing value, try closer to original
            adjust bounds toward original lightness
        else:
            // Still failing, move further from original
            adjust bounds away from original lightness

    return candidate
```

### Fix Output Format

For each failing pair:
```
Original:  text #9ca3af on background #f3f4f6 → 2.26:1 ❌
Fix for AA (4.5:1):  change text to #636b74 → 4.53:1 ✅
Fix for AAA (7:1):   change text to #484e55 → 7.02:1 ✅
```

Always provide the fix as a ready-to-copy hex code.

## Color Blindness Analysis

Approximately 8% of men and 0.5% of women have some form of color vision deficiency. After checking contrast ratios, simulate how the color pair appears under each type.

### Simulation Types

| Type | Affected Population | What's Lost |
|------|-------------------|-------------|
| **Protanopia** | ~1% of men | No red cones. Red appears dark/muddy. Red-green confusion. |
| **Deuteranopia** | ~1% of men | No green cones. Most common full dichromacy. Red-green confusion. |
| **Tritanopia** | ~0.003% | No blue cones. Blue-yellow confusion. Rare. |
| **Protanomaly** | ~1% of men | Reduced red sensitivity. Milder red-green issues. |
| **Deuteranomaly** | ~5% of men | Reduced green sensitivity. Most common CVD overall. |

### Simulation Method

Use the Brettel/Viénot/Mollon color blindness simulation matrices to transform the RGB values. See `references/color-blindness-matrices.md` for the transformation matrices.

After transforming both colors through each simulation:
1. Recalculate the contrast ratio of the simulated pair
2. Flag if contrast drops below the passing threshold
3. Flag if the two colors become nearly indistinguishable (ΔE < 10 in CIELAB space)

### Color Blindness Report Format

```
Color Blindness Impact:
  🔴 Protanopia:    simulated contrast 3.1:1 (was 5.2:1) — ⚠️ drops below AA body text
  🟢 Deuteranopia:  simulated contrast 4.8:1 (was 5.2:1) — ✅ still passes AA
  🔵 Tritanopia:    simulated contrast 5.0:1 (was 5.2:1) — ✅ still passes AA
```

### High-Risk Combinations to Always Flag

Warn about these regardless of contrast ratio:
- Red text on green background (or vice versa)
- Red vs brown combinations
- Green vs yellow combinations
- Blue vs purple combinations
- Any design that relies **solely** on color to convey meaning (e.g., red = error, green = success with no icon or text differentiator)

## Complete Analysis Output

For each text/background pair, present a structured report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAIR: [label or context]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Text:       #XXXXXX  ██████
Background: #XXXXXX  ██████
Contrast:   X.XX:1

WCAG Compliance:
  AA  Body Text  (4.5:1):  ✅ Pass / ❌ Fail
  AA  Large Text (3.0:1):  ✅ Pass / ❌ Fail
  AAA Body Text  (7.0:1):  ✅ Pass / ❌ Fail
  AAA Large Text (4.5:1):  ✅ Pass / ❌ Fail

Color Blindness Impact:
  Protanopia:   X.XX:1 — ✅/⚠️/❌
  Deuteranopia: X.XX:1 — ✅/⚠️/❌
  Tritanopia:   X.XX:1 — ✅/⚠️/❌

Fixes (if failing):
  → For AA:  change text to #XXXXXX (ratio X.XX:1)
  → For AAA: change text to #XXXXXX (ratio X.XX:1)

Additional Notes:
  [vibrating colors, thin font warning, transparency, CVD risk, etc.]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Visual Artifact

When analyzing 2+ color pairs, or when a visual would help, generate an interactive React artifact. See `references/artifact-template.md` for the component template. The artifact should include:

- Live color swatches showing sample text on background at multiple sizes
- Calculated contrast ratio with color-coded pass/fail
- WCAG badges for AA/AAA at both body and large text sizes
- Interactive color pickers to tweak colors in real time
- The Fixer results shown inline with one-click copy
- A color blindness simulation toggle (Protanopia, Deuteranopia, Tritanopia)

## Programmatic Analysis

### Manual Pair Check

For checking specific color pairs:

```bash
python3 scripts/contrast_check.py "#textcolor" "#bgcolor" [more pairs...]
python3 scripts/contrast_check.py --cvd "#e53e3e" "#38a169"
```

### CSS File Scanner

For scanning an entire CSS file (global.css, styles.css, theme files, Tailwind output):

```bash
python3 scripts/scan_css.py path/to/global.css
python3 scripts/scan_css.py path/to/global.css --cvd
python3 scripts/scan_css.py path/to/global.css --json > report.json
```

The scanner automatically:
1. Parses all CSS rules and extracts `color` + `background-color` pairs per selector
2. Resolves CSS custom properties (`var(--name)`) defined in `:root` or any block
3. Detects hex, rgb(), hsl(), and named CSS colors
4. Infers background from parent selectors when a rule only defines text color
5. Checks border colors against backgrounds for non-text contrast (SC 1.4.11)
6. Handles `@media` blocks (including `prefers-color-scheme: dark`)
7. Deduplicates identical pairs
8. Runs the full analysis (contrast ratio, WCAG check, Fixer, optional CVD) on every pair
9. Groups output by severity: failures first, then AA-only, then passing

### JS/TS File Scanner

For scanning JavaScript and TypeScript files (themes, design tokens, Tailwind configs, styled-components, inline styles):

```bash
python3 scripts/scan_js.py path/to/theme.ts
python3 scripts/scan_js.py path/to/theme.ts --cvd
python3 scripts/scan_js.py src/ --recursive
python3 scripts/scan_js.py src/ --recursive --json > report.json
```

The JS/TS scanner automatically:
1. Parses object properties, variable assignments, inline styles, and template literals
2. Classifies keys semantically as text, background, or border using naming patterns (e.g., `color`, `backgroundColor`, `textMuted`, `onPrimary`, `bg`, `foreground`, `borderColor`)
3. Groups colors by nesting context (e.g., `palette.primary`, `dark`, `error`)
4. Pairs text colors with background colors within each context
5. Detects Material UI / Chakra / Mantine theme patterns, design tokens, Tailwind config colors, and inline React styles
6. Resolves `onX` / `X` naming patterns (e.g., `onPrimary` text on `primary` background)
7. Supports recursive directory scanning with `--recursive` (auto-skips `node_modules`, `dist`, `.next`, etc.)
8. Reports exact line numbers and key paths for each issue
9. Runs the full analysis: contrast ratio, WCAG check, Fixer, optional CVD

Supported file types: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`

When the user uploads or references a JS/TS file with color definitions, use `scan_js.py`. For CSS files, use `scan_css.py`.

## Common Pitfalls to Proactively Flag

- Light gray text on white backgrounds (extremely common, almost always fails)
- Placeholder/hint text that's too faint to read
- Colored text on colored backgrounds without checking contrast
- Dark mode designs where dark gray text sits on near-black backgrounds
- Hover/focus states that reduce contrast below passing
- Disabled UI elements that are completely illegible (users still need to know what's disabled)
- Status indicators using only red/green with no shape or text differentiator
- Thin font weights (300, 200) that reduce perceived contrast even when ratio technically passes
- Text over images or gradients without a solid overlay/scrim
- Relying solely on color to convey state (error, success, warning) without redundant cues
