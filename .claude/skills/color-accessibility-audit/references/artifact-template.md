# Artifact Template — Color Contrast Checker

When the user provides multiple color pairs, or when a visual representation would help, create a React artifact using this template as a starting point. Adapt as needed.

## Key Features to Include

1. **Color swatches** showing text on background
2. **Live contrast ratio** calculation
3. **WCAG pass/fail badges** (AA normal, AA large, AAA)
4. **Color picker inputs** so users can tweak colors interactively
5. **Suggested fixes** for failing pairs
6. **Color blindness simulation** (optional, for advanced analysis)

## Template Structure

```jsx
import { useState, useCallback } from "react";

// ---- Utility Functions ----

function hexToRgb(hex) {
  hex = hex.replace("#", "");
  if (hex.length === 3) {
    hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
  }
  const num = parseInt(hex, 16);
  return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
}

function luminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function contrastRatio(hex1, hex2) {
  const c1 = hexToRgb(hex1);
  const c2 = hexToRgb(hex2);
  const l1 = luminance(c1.r, c1.g, c1.b);
  const l2 = luminance(c2.r, c2.g, c2.b);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function getWcagRating(ratio) {
  if (ratio >= 7) return { level: "AAA", normalText: true, largeText: true };
  if (ratio >= 4.5) return { level: "AA", normalText: true, largeText: true };
  if (ratio >= 3) return { level: "AA Large", normalText: false, largeText: true };
  return { level: "Fail", normalText: false, largeText: false };
}

// ---- Badge Component ----

function Badge({ pass, label }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
      pass ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
    }`}>
      {pass ? "✅" : "❌"} {label}
    </span>
  );
}

// ---- Color Pair Card ----

function ColorPairCard({ textColor, bgColor, onTextChange, onBgChange, label }) {
  const ratio = contrastRatio(textColor, bgColor);
  const rating = getWcagRating(ratio);
  
  return (
    <div className="border rounded-lg p-4 mb-4 bg-white shadow-sm">
      {label && <h3 className="text-sm font-semibold text-gray-500 mb-2">{label}</h3>}
      
      {/* Preview */}
      <div
        className="rounded-lg p-6 mb-3 text-center"
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        <p className="text-2xl font-bold mb-1">Sample Heading</p>
        <p className="text-base">This is body text to check readability.</p>
        <p className="text-sm">Small text is harder to read with low contrast.</p>
      </div>
      
      {/* Color inputs */}
      <div className="flex gap-4 mb-3">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Text:</label>
          <input type="color" value={textColor} onChange={e => onTextChange(e.target.value)} className="w-8 h-8 rounded cursor-pointer" />
          <input type="text" value={textColor} onChange={e => onTextChange(e.target.value)} className="w-24 text-sm border rounded px-2 py-1 font-mono" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Background:</label>
          <input type="color" value={bgColor} onChange={e => onBgChange(e.target.value)} className="w-8 h-8 rounded cursor-pointer" />
          <input type="text" value={bgColor} onChange={e => onBgChange(e.target.value)} className="w-24 text-sm border rounded px-2 py-1 font-mono" />
        </div>
      </div>
      
      {/* Results */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-lg font-bold" style={{ color: ratio >= 4.5 ? "#16a34a" : ratio >= 3 ? "#ca8a04" : "#dc2626" }}>
            {ratio.toFixed(2)}:1
          </span>
          <span className="text-sm text-gray-500 ml-1">contrast ratio</span>
        </div>
        <div className="flex gap-2">
          <Badge pass={rating.normalText} label="AA" />
          <Badge pass={rating.largeText} label="AA Large" />
          <Badge pass={ratio >= 7} label="AAA" />
        </div>
      </div>
    </div>
  );
}

// ---- Main Component ----

export default function ContrastChecker() {
  // Initialize with the user's color pairs here
  const [pairs, setPairs] = useState([
    { text: "#333333", bg: "#ffffff", label: "Pair 1" },
  ]);

  const updatePair = (index, field, value) => {
    const updated = [...pairs];
    updated[index] = { ...updated[index], [field]: value };
    setPairs(updated);
  };

  const addPair = () => {
    setPairs([...pairs, { text: "#333333", bg: "#ffffff", label: `Pair ${pairs.length + 1}` }]);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-1">Color Contrast Checker</h1>
      <p className="text-gray-500 mb-6">Check if your text colors are readable against their backgrounds.</p>
      
      {pairs.map((pair, i) => (
        <ColorPairCard
          key={i}
          textColor={pair.text}
          bgColor={pair.bg}
          label={pair.label}
          onTextChange={(v) => updatePair(i, "text", v)}
          onBgChange={(v) => updatePair(i, "bg", v)}
        />
      ))}
      
      <button
        onClick={addPair}
        className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
      >
        + Add Color Pair
      </button>
    </div>
  );
}
```

## Customization Notes

- Pre-populate `pairs` state with the user's actual colors
- Add labels that match the user's context (e.g., "Header text", "Button label", "Placeholder text")
- For CSS/Tailwind analysis, show the original class/property names alongside the hex values
- If suggesting fixes, add a "Suggested" column with auto-corrected colors that hit AA minimum
- For large analyses (10+ pairs), add a summary section at the top showing how many pass/fail

## Suggesting Fixes

When a pair fails, adjust the failing color to meet at minimum AA (4.5:1):
- If the text is too light on a light background, darken the text
- If the text is too dark on a dark background, lighten the text
- Preserve the hue — only adjust lightness
- Show the suggested color next to the original for easy comparison
