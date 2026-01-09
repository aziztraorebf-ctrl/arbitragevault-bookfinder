# Vault Elegance Design System

**Date**: 8 Janvier 2026
**Scope**: Dashboard + Layout redesign avec Dark Mode
**Status**: APPROVED

---

## Overview

Redesign complet du Dashboard et Layout de ArbitrageVault avec un style premium "Vault Elegance". Inclut un dark mode avec toggle manuel.

### Decisions cles

| Decision | Choix | Raison |
|----------|-------|--------|
| Scope | Dashboard + Layout | Base de reference pour autres pages |
| Donnees | Mockees realistes | Valider design sans toucher backend |
| Dark mode | Toggle manuel header | Controle utilisateur explicite |
| Palette dark | Navy + Or | Evoque le "Vault", luxueux |
| Activity Feed | Focus Analyse | Correspond aux features actuelles |

---

## Section 1: Palette & Tokens

### Light Mode

```css
:root {
  --bg-primary: #f5f0e8;      /* Fond beige creme */
  --bg-card: #ffffff;          /* Cards blanches */
  --bg-sidebar: #faf8f5;       /* Sidebar differenciee */
  --text-primary: #1a1a1a;     /* Titres, texte important */
  --text-secondary: #6b5b4f;   /* Texte secondaire marron */
  --accent: #8b5a4a;           /* Bordeaux - accents, liens */
  --accent-hover: #6d4539;     /* Hover sur accents */
  --success: #059669;          /* Vert profit/positif */
  --danger: #dc2626;           /* Rouge perte/negatif */
  --border: #e5e0d8;           /* Bordures subtiles */
}
```

### Dark Mode (Navy + Or)

```css
[data-theme="dark"] {
  --bg-primary: #0f172a;       /* Fond navy profond */
  --bg-card: #1e293b;          /* Cards slate fonce */
  --bg-sidebar: #0c1222;       /* Sidebar plus sombre */
  --text-primary: #f8fafc;     /* Texte clair */
  --text-secondary: #94a3b8;   /* Texte gris-bleu */
  --accent: #d4af37;           /* Or - accents, liens */
  --accent-hover: #b8962f;     /* Hover sur accents */
  --success: #10b981;          /* Vert emeraude */
  --danger: #ef4444;           /* Rouge vif */
  --border: #334155;           /* Bordures slate */
}
```

### Typographie

| Usage | Font | Taille | Poids |
|-------|------|--------|-------|
| Greeting | Playfair Display | 2.5rem (40px) | 600 |
| KPI Values | Inter | 1.75rem (28px) | 700 |
| Card Titles | Inter | 1rem (16px) | 600 |
| Body | Inter | 0.875rem (14px) | 400 |
| Labels | Inter | 0.75rem (12px) | 500 |

---

## Section 2: Layout Structure

### Header (64px height)

```
+---------------------------------------------------------------------+
| [Logo] ArbitrageVault          [Search...]           [Theme] [Avatar]|
+---------------------------------------------------------------------+
```

| Element | Specification |
|---------|---------------|
| Logo | Icone livre + "Arbitrage" (regular) + "Vault" (bold) |
| Search | width 320px, border-radius 24px, placeholder gris |
| Theme toggle | Icone Sun/Moon, 40px touch target |
| Avatar | 40px cercle, border 2px --accent |

### Sidebar

| Mode | Largeur | Comportement |
|------|---------|--------------|
| Desktop collapsed | 72px | Icones seules |
| Desktop hover | 240px | Expand avec labels |
| Mobile | 0px / 280px | Hidden / Slide-in overlay |

Navigation items:
1. Dashboard
2. Analytics (Analyse Manuelle)
3. Discovery (Niche Discovery)
4. Bookmarks (Mes Niches)
5. ---separator---
6. AutoScheduler
7. AutoSourcing
8. Searches (Mes Recherches)
9. ---separator---
10. Settings (Configuration)

Active state: Barre verticale 3px --accent a gauche

### Main Content

```css
.main-content {
  margin-left: 72px; /* desktop */
  margin-top: 64px;
  padding: 32px;
  max-width: 1400px;
  background: var(--bg-primary);
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    padding: 16px;
  }
}
```

---

## Section 3: Dashboard Components

### Greeting Section

```tsx
<section className="greeting">
  <h1>Bonjour Aziz</h1>        // Playfair Display 2.5rem
  <p>Thursday, January 8, 2026</p>  // Inter 0.875rem --text-secondary
</section>
```

Logique salutation:
- 5h-12h: "Bonjour"
- 12h-18h: "Bon apres-midi"
- 18h-5h: "Bonsoir"

### KPI Cards (4 en row)

```
+------------------+  +------------------+  +------------------+  +------------------+
| [sparkline]  +12%|  | [sparkline]  +3% |  | [sparkline]  +2% |  | [sparkline]  -2% |
| $45,280.15       |  | 2,450            |  | 28.4%            |  | 15               |
| Total Value      |  | Products Analyzed|  | Avg ROI          |  | Pending Reviews  |
+------------------+  +------------------+  +------------------+  +------------------+
```

| Prop | Type | Description |
|------|------|-------------|
| value | string | Valeur principale formatee |
| label | string | Description sous la valeur |
| change | number | Variation % (positif/negatif) |
| sparkData | number[] | 7 points pour mini-graphe |
| icon? | ReactNode | Icone optionnelle |

Style:
- Card: --bg-card, border-radius 16px, shadow-sm
- Padding: 24px
- Sparkline: 80px wide, 32px tall, stroke --accent
- Change badge: top-right, font-size 0.75rem

Responsive:
- Desktop: grid-cols-4
- Tablet: grid-cols-2
- Mobile: grid-cols-1

### Action Cards (3 en row)

```
+------------------------+  +------------------------+  +------------------------+
| New Opportunity     [i]|  | Market Alert        [i]|  | Performance Report  [i]|
| ISBN 978-3-16-148410-0 |  | Price Drop Detected.   |  | Monthly Analytics Ready|
| Profit: $85.00         |  | 'Innovator's Dilemma'  |  | Period: December 2025  |
| Source: Retailer A     |  | Price: $12.50          |  | Top 5 Categories       |
|                        |  |                        |  |                        |
| [Analyze Deal]         |  | [View Details]         |  | [Download PDF]         |
+------------------------+  +------------------------+  +------------------------+
```

| Prop | Type | Description |
|------|------|-------------|
| title | string | Titre de la card |
| icon | ReactNode | Icone en haut a droite |
| lines | string[] | 2-4 lignes de description |
| action | { label, onClick } | Bouton d'action |

Style:
- Card: --bg-card, border-radius 12px
- Border-left: 3px solid --accent
- Padding: 20px
- Action button: ghost, --accent color

### Activity Feed

```
+--------------------------------------------------------------------+
| Activity Feed                                                       |
+--------------------------------------------------------------------+
| [icon] 10:45 AM - Analysis Complete: 45 products scored            |
+--------------------------------------------------------------------+
| [icon] 09:30 AM - Niche Found: 'Psychology Textbooks' (ROI 34%)    |
+--------------------------------------------------------------------+
| [icon] Yesterday - Verification: B08N5WRWNW passed (Score: 82)     |
+--------------------------------------------------------------------+
| [icon] Yesterday - Search Saved: 'Q1 2026 Opportunities'           |
+--------------------------------------------------------------------+
| [icon] 2 days ago - Low Balance Alert: 45 Keepa tokens remaining   |
+--------------------------------------------------------------------+
```

Event types:

| Type | Icon | Color |
|------|------|-------|
| analysis | BarChart3 | --accent |
| niche | Search | --success |
| verification | CheckCircle | --success |
| search_saved | Bookmark | --accent |
| alert | AlertTriangle | --danger |

Style:
- Container: --bg-card, border-radius 12px
- Header: padding 16px 24px, border-bottom, font-semibold
- Row: padding 16px 24px, border-bottom, hover --bg-primary
- Timestamp: 0.75rem, --text-secondary
- Max display: 5 items

---

## Section 4: Mock Data

### KPI Data

```typescript
const mockKpiData = {
  totalValue: {
    value: "$45,280.15",
    label: "Total Arbitrage Value",
    change: 12.5,
    sparkData: [32, 35, 33, 38, 42, 40, 45]
  },
  productsAnalyzed: {
    value: "2,450",
    label: "Products Analyzed",
    change: 3.2,
    sparkData: [180, 195, 210, 205, 230, 240, 245]
  },
  avgRoi: {
    value: "28.4%",
    label: "Average ROI",
    change: 1.8,
    sparkData: [24, 25, 26, 27, 26, 28, 28]
  },
  pendingReviews: {
    value: "15",
    label: "Pending Reviews",
    change: -2.1,
    sparkData: [22, 20, 18, 17, 16, 16, 15]
  }
}
```

### Action Cards Data

```typescript
const mockActionCards = [
  {
    title: "New Arbitrage Opportunity",
    icon: "BookOpen",
    lines: [
      "ISBN 978-3-16-148410-0",
      "Potential Profit: $85.00",
      "Source: Online Retailer A",
      "Destination: B2B Market B"
    ],
    action: { label: "Analyze Deal", href: "/analyse" }
  },
  {
    title: "Market Alert",
    icon: "Bell",
    lines: [
      "Price Drop Detected.",
      "Book: 'The Innovator's Dilemma'",
      "Current Price: $12.50",
      "Alert: Below Threshold"
    ],
    action: { label: "View Details", href: "/niche-discovery" }
  },
  {
    title: "Performance Report",
    icon: "FileText",
    lines: [
      "Monthly Analytics Ready.",
      "Period: December 2025",
      "Insights: Top 5 Categories",
      "Profitable Categories"
    ],
    action: { label: "Download PDF", onClick: () => {} }
  }
]
```

### Activity Feed Data

```typescript
const mockActivityFeed = [
  {
    type: "analysis",
    timestamp: "10:45 AM",
    message: "Analysis Complete: 45 products scored",
    highlight: "45 products"
  },
  {
    type: "niche",
    timestamp: "09:30 AM",
    message: "Niche Found: 'Psychology Textbooks' (ROI 34%)",
    highlight: "ROI 34%"
  },
  {
    type: "verification",
    timestamp: "Yesterday",
    message: "Verification: B08N5WRWNW passed (Score: 82)",
    highlight: "Score: 82"
  },
  {
    type: "search_saved",
    timestamp: "Yesterday",
    message: "Search Saved: 'Q1 2026 Opportunities'",
    highlight: "Q1 2026"
  },
  {
    type: "alert",
    timestamp: "2 days ago",
    message: "Low Balance Alert: 45 Keepa tokens remaining",
    highlight: "45 tokens"
  }
]
```

---

## Section 5: Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `src/styles/theme.css` | Variables CSS light/dark |
| `src/contexts/ThemeContext.tsx` | Context + useTheme hook |
| `src/components/ui/KpiCard.tsx` | KPI card component |
| `src/components/ui/ActionCard.tsx` | Action card component |
| `src/components/ui/ActivityFeed.tsx` | Activity feed component |
| `src/components/ui/ThemeToggle.tsx` | Sun/Moon toggle button |
| `src/components/ui/Sparkline.tsx` | Mini line chart SVG |
| `src/components/ui/SearchBar.tsx` | Header search input |
| `src/data/mockDashboard.ts` | Mock data for dashboard |

### Modified Files

| File | Changes |
|------|---------|
| `tailwind.config.js` | Add custom colors, fonts |
| `index.html` | Add Google Fonts link |
| `src/index.css` | Import theme.css |
| `src/App.tsx` | Wrap with ThemeProvider |
| `src/components/Layout/Layout.tsx` | Complete redesign |
| `src/components/Dashboard/Dashboard.tsx` | Complete redesign |

---

## Section 6: Implementation Order

1. **Theme foundation** (theme.css, ThemeContext, tailwind.config)
2. **UI components** (KpiCard, ActionCard, ActivityFeed, Sparkline, ThemeToggle)
3. **Layout redesign** (Header, Sidebar, responsive)
4. **Dashboard redesign** (Greeting, KPIs, Actions, Feed)
5. **Polish** (animations, hover states, mobile testing)

---

## Section 7: Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Sidebar hidden, 1 col KPIs, hamburger menu |
| Tablet | 768-1024px | Sidebar collapsed 72px, 2 col KPIs |
| Desktop | > 1024px | Sidebar collapsed 72px (expand hover), 4 col KPIs |

---

## Acceptance Criteria

- [ ] Light mode matches mockup reference image
- [ ] Dark mode uses Navy + Gold palette
- [ ] Theme toggle in header works with localStorage persistence
- [ ] All 4 KPI cards display with sparklines
- [ ] 3 Action cards display with functional buttons
- [ ] Activity Feed shows 5 mock events
- [ ] Responsive: mobile, tablet, desktop
- [ ] Sidebar collapses/expands correctly
- [ ] Greeting shows correct time-based salutation
- [ ] Build passes with 0 TypeScript errors
- [ ] No accessibility regressions (44px touch targets maintained)

---

**Approved by**: User
**Date**: 8 Janvier 2026
