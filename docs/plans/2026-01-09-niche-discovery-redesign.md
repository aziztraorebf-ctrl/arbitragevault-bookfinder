# Niche Discovery - Vault Elegance Redesign

> **For Claude:** Use frontend-design skill to implement this design.

**Goal:** Harmoniser la page Niche Discovery avec le design system Vault Elegance.

**Approach:** Harmonisation visuelle complete (page + composants + table).

**Tech Stack:** React, TypeScript, Tailwind CSS, Lucide Icons

---

## Design Decisions

| Question | Choice |
|----------|--------|
| Layout boutons strategie | Responsive (cote-a-cote desktop, empiles mobile) |
| Couleurs boutons | Distinctives adaptees Vault (emeraude + ambre) |
| Accordion recherche | Collapsed par defaut |
| Hero banner | Prominent avec gradient Vault |
| Scope | Complet (page + NicheCards + table) |

---

## Color Palette - Strategy Buttons

| Strategy | Light Mode | Dark Mode |
|----------|------------|-----------|
| Standard (rapide) | `#2E7D32` emerald-700 | `#4CAF50` emerald-500 |
| Patience (profit) | `#D4A574` vault-accent | `#E8C9A0` vault-accent-light |

---

## Page Structure

```
+----------------------------------------------------------+
|  HEADER                                                   |
|  "Niche Discovery" (h1, Playfair)                        |
|  "Decouvrez des niches rentables..." (subtitle)          |
+----------------------------------------------------------+
|  HERO BANNER (gradient vault-accent)                      |
|  +------------------------------------------------------+ |
|  |  [Book icon] Strategie Textbook                      | |
|  |  Description des strategies...                       | |
|  |  +---------------------+  +---------------------+    | |
|  |  | Standard (emerald)  |  | Patience (ambre)    |    | |
|  |  | BSR 100K-250K       |  | BSR 250K-400K       |    | |
|  |  +---------------------+  +---------------------+    | |
|  +------------------------------------------------------+ |
+----------------------------------------------------------+
|  DIVIDER                                                  |
|  ─────────────── OU ───────────────                      |
+----------------------------------------------------------+
|  ACCORDION CARD (collapsed)                               |
|  [Search icon] Recherche Personnalisee            [v]    |
+----------------------------------------------------------+
|  RESULTS: NICHE CARDS (when niches discovered)           |
|  +----------------+  +----------------+  +----------------+
|  | NicheCard 1    |  | NicheCard 2    |  | NicheCard 3    |
|  +----------------+  +----------------+  +----------------+
+----------------------------------------------------------+
|  RESULTS: PRODUCT TABLE (when exploring niche)           |
|  UnifiedProductTable with Vault styling                   |
+----------------------------------------------------------+
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `NicheDiscovery.tsx` | Header Vault, remove gradient bg, spacing |
| `AutoDiscoveryHero.tsx` | Gradient Vault, button colors, typography |
| `ManualFiltersSection.tsx` | Card Vault, inputs Vault, accordion header |
| `NicheCard.tsx` | Card Vault, badges, hover effects |
| `CacheIndicator.tsx` | Badge style Vault |

---

## CSS Classes Reference

### Page Container (NicheDiscovery.tsx)
```css
/* Remove gradient background */
/* OLD: bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50 */
/* NEW: */
bg-vault-bg
```

### Page Header
```css
/* Title */
text-4xl md:text-5xl font-display font-semibold text-vault-text tracking-tight

/* Subtitle */
text-sm md:text-base text-vault-text-secondary mt-2
```

### Hero Banner (AutoDiscoveryHero.tsx)
```css
/* Container */
bg-gradient-to-r from-vault-accent to-vault-accent-dark
rounded-2xl p-6 md:p-8 shadow-vault-md
border border-vault-accent/20

/* Title */
text-2xl md:text-3xl font-display font-semibold text-white

/* Subtitle text */
text-white/90 text-sm md:text-base

/* Strategy buttons container */
flex flex-col sm:flex-row gap-4 mt-6
```

### Strategy Button - Standard (Emerald)
```css
flex-1 px-6 py-4 rounded-xl font-semibold
bg-emerald-600 hover:bg-emerald-700
text-white shadow-lg hover:shadow-xl
transition-all duration-200
disabled:opacity-50 disabled:cursor-not-allowed
```

### Strategy Button - Patience (Ambre/Gold)
```css
flex-1 px-6 py-4 rounded-xl font-semibold
bg-amber-600 hover:bg-amber-700
text-white shadow-lg hover:shadow-xl
transition-all duration-200
disabled:opacity-50 disabled:cursor-not-allowed
```

### Divider "OU"
```css
/* Container */
flex items-center gap-4 my-8

/* Lines */
h-px bg-vault-border flex-1

/* Text badge */
text-vault-text-muted font-medium text-sm px-4 py-1
bg-vault-card border border-vault-border rounded-full
```

### Accordion Card (ManualFiltersSection.tsx)
```css
/* Container */
bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm
overflow-hidden

/* Header (clickable) */
px-6 py-4 flex items-center justify-between cursor-pointer
hover:bg-vault-hover transition-colors

/* Header title */
text-base font-semibold text-vault-text flex items-center gap-3

/* Chevron icon */
w-5 h-5 text-vault-text-muted transition-transform duration-200
/* When expanded: rotate-180 */

/* Content area */
px-6 pb-6 pt-2 border-t border-vault-border
```

### Form Inputs (inside accordion)
```css
/* Input fields */
bg-vault-bg border border-vault-border rounded-xl px-4 py-3
text-vault-text placeholder:text-vault-text-muted
focus:ring-2 focus:ring-vault-accent focus:border-transparent

/* Labels */
text-sm font-medium text-vault-text-secondary mb-2

/* Search button */
bg-vault-accent hover:bg-vault-accent-dark text-white
font-medium px-6 py-3 rounded-xl
transition-colors duration-200
```

### Niche Cards (NicheCard.tsx)
```css
/* Card container */
bg-vault-card border border-vault-border rounded-2xl
shadow-vault-sm hover:shadow-vault-md
transition-all duration-200 overflow-hidden
group

/* Card header */
px-5 py-4 border-b border-vault-border-light

/* Niche name */
text-lg font-semibold text-vault-text

/* Stats badges */
inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium
bg-vault-accent-light text-vault-accent

/* Explore button */
w-full mt-4 px-4 py-3 rounded-xl font-medium
bg-vault-accent hover:bg-vault-accent-dark text-white
transition-colors duration-200
```

### Results Section Header
```css
/* "Niches Decouvertes" title */
text-2xl font-display font-semibold text-vault-text mb-6
```

### Loading State
```css
/* Spinner */
animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full

/* Loading text */
text-vault-text-secondary text-base mt-4
```

### Empty State Card
```css
bg-vault-card border border-vault-border rounded-2xl
shadow-vault-sm p-8 text-center

/* Title */
text-xl font-semibold text-vault-text mb-2

/* Description */
text-vault-text-secondary text-sm max-w-md mx-auto
```

---

## Lucide Icons

| Element | Icon | Size |
|---------|------|------|
| Hero title | `BookOpen` | w-8 h-8 |
| Standard button | `Zap` (fast) | w-5 h-5 |
| Patience button | `Clock` | w-5 h-5 |
| Accordion header | `Search` | w-5 h-5 |
| Accordion chevron | `ChevronDown` | w-5 h-5 |
| Niche card explore | `ArrowRight` | w-4 h-4 |
| Back to niches | `ArrowLeft` | w-4 h-4 |
| Loading spinner | (CSS animation) | w-12 h-12 |

---

## Dark Mode

All `vault-*` tokens automatically adapt via CSS custom properties.

Hero gradient in dark mode:
```css
/* Light: from-vault-accent to-vault-accent-dark */
/* Dark: from-[#1a1a2e] to-[#16213e] with gold accents */
```

Strategy buttons keep their colors (emerald/amber) in both modes for consistency.

---

## Responsive Breakpoints

| Viewport | Hero Buttons | Niche Cards Grid | Accordion |
|----------|--------------|------------------|-----------|
| Mobile (<640px) | Stack vertical | 1 column | Full width |
| Tablet (640-1024px) | Side-by-side | 2 columns | Full width |
| Desktop (>1024px) | Side-by-side | 3 columns | Full width |

---

## Interactions

### Strategy Buttons
- **Default:** Solid color with shadow
- **Hover:** Darker shade + larger shadow
- **Loading:** Show spinner, disable button
- **Disabled:** 50% opacity, no pointer

### Accordion
- **Collapsed:** Show header only, chevron pointing down
- **Expanded:** Show content, chevron rotated 180deg
- **Hover header:** Subtle background change

### Niche Cards
- **Default:** Standard shadow
- **Hover:** Elevated shadow, slight scale (1.02)
- **Click explore:** Navigate to products view

---

## Testing Checklist

After implementation:
1. [ ] Visual check desktop/tablet/mobile
2. [ ] Dark mode toggle on all components
3. [ ] Strategy button click triggers discovery
4. [ ] Accordion expand/collapse works
5. [ ] Niche cards display correctly
6. [ ] Product table shows after exploration
7. [ ] Loading states display correctly
8. [ ] Empty state displays when no results

---

## E2E Tests to Create

File: `frontend/tests/e2e/niche-discovery.spec.ts`

Tests:
1. Page displays with Vault title and subtitle
2. Hero banner with strategy buttons visible
3. Standard button triggers discovery
4. Patience button triggers discovery
5. Accordion expands on click
6. Dark mode toggle works
7. Mobile layout (buttons stacked)
8. Niche cards display after discovery (mock)
