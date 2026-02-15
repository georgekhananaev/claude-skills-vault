# Color Blindness Simulation Matrices

## Overview

These matrices transform standard sRGB color values to simulate how colors appear to people with various forms of color vision deficiency (CVD). Based on the Brettel, Viénot & Mollon (1997) model, widely used in accessibility tools.

## How to Apply

1. Convert hex to linear RGB (same linearization as the luminance formula)
2. Multiply the [R, G, B] vector by the appropriate 3×3 matrix
3. Clamp values to [0, 1] range
4. Convert back to sRGB and then to hex

```
[R_sim]     [m00 m01 m02]   [R_linear]
[G_sim]  =  [m10 m11 m12] × [G_linear]
[B_sim]     [m20 m21 m22]   [B_linear]
```

## Simulation Matrices

### Protanopia (no red cones)
Affects ~1% of men. Reds appear dark/muddy, red-green confusion.

```
[0.152286  1.052583  -0.204868]
[0.114503  0.786281   0.099216]
[0.003882  -0.048116  1.044234]
```

### Deuteranopia (no green cones)
Affects ~1% of men. Most common full dichromacy. Red-green confusion.

```
[0.367322  0.860646  -0.227968]
[0.280085  0.672501   0.047413]
[-0.011820  0.042940   0.968881]
```

### Tritanopia (no blue cones)
Affects ~0.003% of population. Blue-yellow confusion.

```
[1.255528  -0.076749  -0.178779]
[-0.078411  0.930809   0.147602]
[0.004733   0.691367   0.303900]
```

### Protanomaly (reduced red sensitivity)
Affects ~1% of men. Milder form of protanopia.

```
[0.458064  0.679578  -0.137642]
[0.092785  0.846313   0.060902]
[-0.007494  -0.016807  1.024301]
```

### Deuteranomaly (reduced green sensitivity)
Affects ~5% of men. Most common CVD overall.

```
[0.547494  0.607765  -0.155259]
[0.181692  0.781742   0.036566]
[-0.010410  0.027275   0.983136]
```

## Usage in the Skill

After simulating both the text and background color through a given matrix:

1. **Recalculate contrast ratio** of the simulated pair using the standard luminance formula
2. **Compare to the original ratio** — flag if it drops below a WCAG threshold
3. **Calculate ΔE (CIELAB)** between the two simulated colors:
   - ΔE < 3: Colors are nearly indistinguishable — **critical risk**
   - ΔE 3–10: Colors are very similar — **high risk**
   - ΔE 10–25: Noticeable difference — **moderate risk** (check context)
   - ΔE > 25: Clearly distinguishable — **low risk**

## ΔE Calculation (simplified CIELAB)

To compute perceptual difference:

1. Convert both simulated colors from linear RGB to CIELAB:
   - RGB → XYZ (using D65 illuminant matrix)
   - XYZ → Lab (using D65 reference white: X=0.95047, Y=1.0, Z=1.08883)

2. ΔE = sqrt((L₁-L₂)² + (a₁-a₂)² + (b₁-b₂)²)

This is the CIE76 formula. Adequate for this use case (detecting indistinguishable pairs).

## Quick Risk Lookup Table

For common color pairings, here's a cheat sheet of CVD risk:

| Combination | Protanopia Risk | Deuteranopia Risk | Tritanopia Risk |
|------------|----------------|-------------------|-----------------|
| Red on green | **Critical** | **Critical** | Low |
| Green on red | **Critical** | **Critical** | Low |
| Red on brown | **High** | **High** | Low |
| Blue on purple | Low | Low | **High** |
| Yellow on green | Moderate | **High** | Low |
| Blue on green | Low | Moderate | Moderate |
| Orange on red | **High** | **High** | Low |
| Pink on gray | Moderate | Moderate | Low |

## Implementation Notes

- Always apply simulation to **both** the text and background color before recalculating contrast
- The Python script `scripts/contrast_check.py` includes the `--cvd` flag for color blindness analysis
- The React artifact template includes a toggle for switching between CVD simulation views
- When a pair is risky for CVD: recommend adding non-color indicators (icons, patterns, underlines, labels)
