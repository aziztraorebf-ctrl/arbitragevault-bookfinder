# Analyse Manuelle - Vault Elegance Redesign

> **For Claude:** Use frontend-design skill to implement this design.

**Goal:** Harmoniser la page Analyse Manuelle avec le design system Vault Elegance du Dashboard.

**Approach:** Option A - Harmonisation visuelle sans changement de logique.

**Tech Stack:** React, TypeScript, Tailwind CSS, Lucide Icons

---

## Design Decisions

| Question | Choice |
|----------|--------|
| Layout input zones | Side-by-side (stack on mobile) |
| CTA button style | ActionCard style with Lucide icon |
| Config organization | Single card with 4-column grid |
| ASIN feedback | Discrete improved banner |
| Page header | Title + descriptive subtitle |

---

## Page Structure

```
+----------------------------------------------------------+
|  HEADER                                                   |
|  "Analyse Manuelle" (h1, Playfair)                       |
|  "Importez vos ASINs ou un fichier CSV..." (subtitle)    |
+----------------------------------------------------------+
|  INPUT ZONES (2 columns desktop, stack mobile)           |
|  +------------------------+  +------------------------+   |
|  |  Drop CSV Zone         |  |  Paste ASINs Zone      |   |
|  |  - Upload icon         |  |  - Textarea            |   |
|  |  - Dashed border       |  |  - "Valider" button    |   |
|  +------------------------+  +------------------------+   |
+----------------------------------------------------------+
|  FEEDBACK BANNER (conditional)                           |
|  [CheckCircle] "3 ASINs valides et prets pour l'analyse" |
+----------------------------------------------------------+
|  CONFIG CARD                                             |
|  "Configuration Analyse" (heading)                       |
|  [Strategy v] [ROI %] [BSR max] [Velocity]              |
|  [ ] Multi-strategies  [ ] Stock check  [ ] Export CSV   |
+----------------------------------------------------------+
|  CTA BUTTON (centered)                                   |
|  [Play icon] "Lancer l'analyse"                         |
+----------------------------------------------------------+
```

---

## CSS Classes Reference

### Page Container
```css
space-y-8 animate-fade-in
```

### Title (h1)
```css
text-4xl md:text-5xl font-display font-semibold text-vault-text tracking-tight
```

### Subtitle
```css
text-sm md:text-base text-vault-text-secondary mt-2
```

### Cards (input zones, config)
```css
bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm p-6
```

### Drop Zone
```css
border-2 border-dashed border-vault-border-light hover:border-vault-accent
rounded-xl p-8 transition-colors cursor-pointer
flex flex-col items-center justify-center gap-4 min-h-[200px]
```

### Drop Zone (drag-over state)
```css
border-vault-accent bg-vault-accent/5 animate-pulse
```

### Textarea
```css
bg-vault-bg border border-vault-border rounded-xl px-4 py-3
text-vault-text placeholder:text-vault-text-muted
focus:ring-2 focus:ring-vault-accent focus:border-transparent
w-full min-h-[120px] resize-none
```

### Input Fields
```css
bg-vault-bg border border-vault-border rounded-xl px-4 py-3
text-vault-text focus:ring-2 focus:ring-vault-accent
```

### Select/Dropdown
```css
bg-vault-bg border border-vault-border rounded-xl px-4 py-3
text-vault-text appearance-none cursor-pointer
focus:ring-2 focus:ring-vault-accent
```

### Checkboxes
```css
accent-vault-accent w-4 h-4 rounded
```

### Checkbox Labels
```css
text-sm text-vault-text-secondary flex items-center gap-2 cursor-pointer
```

### Feedback Banner (success)
```css
bg-vault-accent-light border border-vault-accent/20 rounded-xl
px-4 py-3 flex items-center gap-3
```

### Feedback Banner Text
```css
text-sm font-medium text-vault-accent
```

### CTA Button
```css
bg-vault-accent hover:bg-vault-accent-dark text-white
font-medium px-8 py-4 rounded-xl
shadow-vault-md hover:shadow-vault-lg
transition-all duration-200
flex items-center justify-center gap-2
disabled:opacity-50 disabled:cursor-not-allowed
```

### Secondary Button (Valider ASINs)
```css
bg-vault-accent text-white font-medium px-6 py-3 rounded-xl
hover:bg-vault-accent-dark transition-colors
disabled:bg-vault-border disabled:text-vault-text-muted
```

---

## Responsive Breakpoints

| Viewport | Input Zones | Config Grid | CTA |
|----------|-------------|-------------|-----|
| Mobile (<768px) | Stack vertical | 1 column | Full width |
| Tablet (768-1024px) | Side-by-side | 2 columns | Auto width |
| Desktop (>1024px) | Side-by-side | 4 columns | Auto width |

### Grid Classes

**Input zones container:**
```css
grid grid-cols-1 md:grid-cols-2 gap-6
```

**Config fields grid:**
```css
grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4
```

**Checkboxes row:**
```css
flex flex-wrap gap-6 mt-4
```

---

## Lucide Icons

| Element | Icon | Size |
|---------|------|------|
| Drop zone | `Upload` | w-10 h-10 |
| Feedback success | `CheckCircle` | w-5 h-5 |
| CTA button | `Play` | w-5 h-5 |
| Dropdown chevron | `ChevronDown` | w-4 h-4 |

---

## Interactions

### Drop Zone
- **Default:** Dashed border `vault-border-light`
- **Hover:** Border changes to `vault-accent`
- **Drag-over:** Background tint + pulse animation
- **File dropped:** Show filename, change icon to `FileCheck`

### Valider ASINs Button
- **Disabled:** When textarea is empty
- **Enabled:** When ASINs are present
- **Click:** Parse ASINs, show feedback banner

### CTA Button
- **Disabled:** No ASINs validated and no CSV uploaded
- **Enabled:** When data is ready
- **Loading:** Show spinner, disable button
- **Click:** Submit analysis request

### Inputs
- **Focus:** 2px ring `vault-accent`
- **Invalid:** Border `red-500` (if validation needed)

---

## Dark Mode

All `vault-*` tokens automatically adapt via CSS custom properties in `theme.css`.

No additional work needed - colors switch based on `data-theme="dark"` attribute.

---

## Files to Modify

1. `frontend/src/pages/AnalyseManuelle.tsx` - Main page component (apply new styles)

## No New Components Needed

All styling uses existing Tailwind classes and vault tokens. No new reusable components required for this redesign.

---

## Testing

After implementation:
1. Visual check desktop/tablet/mobile
2. Dark mode toggle
3. ASIN validation flow
4. CSV drop interaction
5. Form submission
