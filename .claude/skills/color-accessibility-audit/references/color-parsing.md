# Color Parsing Reference

## Supported Color Formats

### Hex Colors
- 6-digit: `#RRGGBB` (e.g., `#3a7bd5`)
- 3-digit shorthand: `#RGB` (e.g., `#fff` → `#ffffff`)
- 8-digit with alpha: `#RRGGBBAA` — strip alpha for contrast calculation

### RGB / RGBA
- `rgb(R, G, B)` where R, G, B are 0–255
- `rgba(R, G, B, A)` — strip alpha, but warn that transparency affects perceived contrast

### HSL / HSLA
- `hsl(H, S%, L%)` where H is 0–360, S and L are 0–100%
- Convert to RGB first:

```
HSL to RGB conversion:
1. S and L to 0–1 range
2. C = (1 - |2L - 1|) × S
3. X = C × (1 - |(H/60) mod 2 - 1|)
4. m = L - C/2
5. Based on H sector (0-60, 60-120, etc.), assign (C,X,0), (X,C,0), etc.
6. R, G, B = (R'+m, G'+m, B'+m) × 255
```

### Named CSS Colors
Common named colors and their hex values:

| Name | Hex | Name | Hex |
|------|-----|------|-----|
| black | #000000 | white | #ffffff |
| red | #ff0000 | green | #008000 |
| blue | #0000ff | yellow | #ffff00 |
| gray / grey | #808080 | silver | #c0c0c0 |
| orange | #ffa500 | purple | #800080 |
| navy | #000080 | teal | #008080 |
| maroon | #800000 | olive | #808000 |
| aqua | #00ffff | fuchsia | #ff00ff |
| lime | #00ff00 | coral | #ff7f50 |
| salmon | #fa8072 | tomato | #ff6347 |
| gold | #ffd700 | khaki | #f0e68c |
| plum | #dda0dd | orchid | #da70d6 |
| ivory | #fffff0 | linen | #faf0e6 |
| beige | #f5f5dc | lavender | #e6e6fa |
| slategray | #708090 | dimgray | #696969 |
| darkgray | #a9a9a9 | lightgray | #d3d3d3 |
| gainsboro | #dcdcdc | whitesmoke | #f5f5f5 |

### Tailwind CSS Color Mappings (v3 defaults)

**Gray scale:**
| Class | Hex |
|-------|-----|
| gray-50 | #f9fafb |
| gray-100 | #f3f4f6 |
| gray-200 | #e5e7eb |
| gray-300 | #d1d5db |
| gray-400 | #9ca3af |
| gray-500 | #6b7280 |
| gray-600 | #4b5563 |
| gray-700 | #374151 |
| gray-800 | #1f2937 |
| gray-900 | #111827 |
| gray-950 | #030712 |

**Slate scale:**
| Class | Hex |
|-------|-----|
| slate-50 | #f8fafc |
| slate-100 | #f1f5f9 |
| slate-200 | #e2e8f0 |
| slate-300 | #cbd5e1 |
| slate-400 | #94a3b8 |
| slate-500 | #64748b |
| slate-600 | #475569 |
| slate-700 | #334155 |
| slate-800 | #1e293b |
| slate-900 | #0f172a |

**Red scale:**
| Class | Hex |
|-------|-----|
| red-50 | #fef2f2 |
| red-100 | #fee2e2 |
| red-200 | #fecaca |
| red-300 | #fca5a5 |
| red-400 | #f87171 |
| red-500 | #ef4444 |
| red-600 | #dc2626 |
| red-700 | #b91c1c |
| red-800 | #991b1b |
| red-900 | #7f1d1d |

**Blue scale:**
| Class | Hex |
|-------|-----|
| blue-50 | #eff6ff |
| blue-100 | #dbeafe |
| blue-200 | #bfdbfe |
| blue-300 | #93c5fd |
| blue-400 | #60a5fa |
| blue-500 | #3b82f6 |
| blue-600 | #2563eb |
| blue-700 | #1d4ed8 |
| blue-800 | #1e40af |
| blue-900 | #1e3a8a |

**Green scale:**
| Class | Hex |
|-------|-----|
| green-50 | #f0fdf4 |
| green-100 | #dcfce7 |
| green-200 | #bbf7d0 |
| green-300 | #86efac |
| green-400 | #4ade80 |
| green-500 | #22c55e |
| green-600 | #16a34a |
| green-700 | #15803d |
| green-800 | #166534 |
| green-900 | #14532d |

**Yellow scale:**
| Class | Hex |
|-------|-----|
| yellow-50 | #fefce8 |
| yellow-100 | #fef9c3 |
| yellow-200 | #fef08a |
| yellow-300 | #fde047 |
| yellow-400 | #facc15 |
| yellow-500 | #eab308 |
| yellow-600 | #ca8a04 |
| yellow-700 | #a16207 |
| yellow-800 | #854d0e |
| yellow-900 | #713f12 |

**Other common Tailwind colors** — for the full set, refer to https://tailwindcss.com/docs/customizing-colors

The pattern for Tailwind classes:
- `text-{color}-{shade}` → text color
- `bg-{color}-{shade}` → background color
- `text-white` → #ffffff
- `text-black` → #000000

## Parsing Strategy

1. First, normalize the input — strip whitespace, lowercase
2. Try matching in this order: hex → rgb/rgba → hsl/hsla → named color → Tailwind class
3. If the input is CSS code, extract property values from `color:`, `background-color:`, `background:`, `border-color:`
4. If the input is HTML, look for inline styles and class attributes
5. If Tailwind classes, map to hex using the tables above
6. If a color can't be resolved, tell the user and ask for clarification
