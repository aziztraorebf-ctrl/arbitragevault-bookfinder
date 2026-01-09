# Vault Elegance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign Dashboard + Layout with premium "Vault Elegance" theme including dark mode toggle.

**Architecture:** CSS custom properties for theming, React Context for dark mode state, modular UI components (KpiCard, ActionCard, ActivityFeed, Sparkline). Layout uses collapsible sidebar pattern.

**Tech Stack:** React 18, TypeScript, Tailwind CSS 4, Lucide icons, Google Fonts (Playfair Display, Inter)

**Design Spec:** `docs/plans/2026-01-08-vault-elegance-design.md`

---

## Task 1: Theme Foundation - CSS Variables

**Files:**
- Create: `frontend/src/styles/theme.css`
- Modify: `frontend/src/index.css`
- Modify: `frontend/index.html`

**Step 1: Create theme.css with CSS custom properties**

```css
/* frontend/src/styles/theme.css */

/* Light Mode (default) */
:root {
  --bg-primary: #f5f0e8;
  --bg-card: #ffffff;
  --bg-sidebar: #faf8f5;
  --text-primary: #1a1a1a;
  --text-secondary: #6b5b4f;
  --accent: #8b5a4a;
  --accent-hover: #6d4539;
  --success: #059669;
  --danger: #dc2626;
  --border: #e5e0d8;
}

/* Dark Mode */
[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-card: #1e293b;
  --bg-sidebar: #0c1222;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --accent: #d4af37;
  --accent-hover: #b8962f;
  --success: #10b981;
  --danger: #ef4444;
  --border: #334155;
}

/* Utility classes using CSS variables */
.bg-primary { background-color: var(--bg-primary); }
.bg-card { background-color: var(--bg-card); }
.bg-sidebar { background-color: var(--bg-sidebar); }
.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-accent { color: var(--accent); }
.border-theme { border-color: var(--border); }

/* Transitions for theme switching */
body {
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

**Step 2: Add Google Fonts to index.html**

In `frontend/index.html`, add inside `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
```

**Step 3: Import theme.css in index.css**

At top of `frontend/src/index.css`, add:

```css
@import './styles/theme.css';
```

**Step 4: Verify files exist**

Run: `dir frontend\src\styles\theme.css`
Expected: File exists

**Step 5: Commit**

```bash
git add frontend/src/styles/theme.css frontend/src/index.css frontend/index.html
git commit -m "feat(theme): add CSS custom properties for light/dark mode"
```

---

## Task 2: Theme Context and Hook

**Files:**
- Create: `frontend/src/contexts/ThemeContext.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create ThemeContext with localStorage persistence**

```typescript
// frontend/src/contexts/ThemeContext.tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const STORAGE_KEY = 'vault-elegance-theme'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'light' || stored === 'dark') {
        return stored
      }
    }
    return 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  const toggleTheme = () => {
    setThemeState(prev => prev === 'light' ? 'dark' : 'light')
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
```

**Step 2: Wrap App with ThemeProvider**

In `frontend/src/App.tsx`, import and wrap:

```typescript
import { ThemeProvider } from './contexts/ThemeContext'

// In the return, wrap everything:
return (
  <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      {/* ... existing content ... */}
    </QueryClientProvider>
  </ThemeProvider>
)
```

**Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/contexts/ThemeContext.tsx frontend/src/App.tsx
git commit -m "feat(theme): add ThemeContext with localStorage persistence"
```

---

## Task 3: Tailwind Config Extension

**Files:**
- Modify: `frontend/tailwind.config.js`

**Step 1: Extend Tailwind with custom colors and fonts**

Replace entire `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vault: {
          // Light mode
          'bg': 'var(--bg-primary)',
          'card': 'var(--bg-card)',
          'sidebar': 'var(--bg-sidebar)',
          'text': 'var(--text-primary)',
          'text-muted': 'var(--text-secondary)',
          'accent': 'var(--accent)',
          'accent-hover': 'var(--accent-hover)',
          'success': 'var(--success)',
          'danger': 'var(--danger)',
          'border': 'var(--border)',
        },
        // Static colors for specific uses
        'cream': '#f5f0e8',
        'navy': '#0f172a',
        'gold': '#d4af37',
        'bordeaux': '#8b5a4a',
      },
      fontFamily: {
        'display': ['Playfair Display', 'Georgia', 'serif'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 4px 16px rgba(0, 0, 0, 0.12)',
      },
      borderRadius: {
        'card': '16px',
        'card-sm': '12px',
      },
    },
  },
  plugins: [],
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/tailwind.config.js
git commit -m "feat(theme): extend Tailwind with Vault Elegance design tokens"
```

---

## Task 4: Mock Data

**Files:**
- Create: `frontend/src/data/mockDashboard.ts`

**Step 1: Create mock data file**

```typescript
// frontend/src/data/mockDashboard.ts

export interface KpiData {
  value: string
  label: string
  change: number
  sparkData: number[]
}

export interface ActionCardData {
  title: string
  icon: 'BookOpen' | 'Bell' | 'FileText'
  lines: string[]
  action: {
    label: string
    href?: string
    onClick?: () => void
  }
}

export interface ActivityEvent {
  id: string
  type: 'analysis' | 'niche' | 'verification' | 'search_saved' | 'alert'
  timestamp: string
  message: string
  highlight?: string
}

export const mockKpiData: Record<string, KpiData> = {
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

export const mockActionCards: ActionCardData[] = [
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
    action: { label: "Download PDF" }
  }
]

export const mockActivityFeed: ActivityEvent[] = [
  {
    id: "1",
    type: "analysis",
    timestamp: "10:45 AM",
    message: "Analysis Complete: 45 products scored",
    highlight: "45 products"
  },
  {
    id: "2",
    type: "niche",
    timestamp: "09:30 AM",
    message: "Niche Found: 'Psychology Textbooks' (ROI 34%)",
    highlight: "ROI 34%"
  },
  {
    id: "3",
    type: "verification",
    timestamp: "Yesterday",
    message: "Verification: B08N5WRWNW passed (Score: 82)",
    highlight: "Score: 82"
  },
  {
    id: "4",
    type: "search_saved",
    timestamp: "Yesterday",
    message: "Search Saved: 'Q1 2026 Opportunities'",
    highlight: "Q1 2026"
  },
  {
    id: "5",
    type: "alert",
    timestamp: "2 days ago",
    message: "Low Balance Alert: 45 Keepa tokens remaining",
    highlight: "45 tokens"
  }
]

export function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return "Bonjour"
  if (hour >= 12 && hour < 18) return "Bon apres-midi"
  return "Bonsoir"
}

export function formatDate(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/data/mockDashboard.ts
git commit -m "feat(dashboard): add mock data for Vault Elegance dashboard"
```

---

## Task 5: UI Components - Sparkline

**Files:**
- Create: `frontend/src/components/ui/Sparkline.tsx`

**Step 1: Create Sparkline SVG component**

```typescript
// frontend/src/components/ui/Sparkline.tsx

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  className?: string
}

export function Sparkline({
  data,
  width = 80,
  height = 32,
  className = ''
}: SparklineProps) {
  if (data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width
    const y = height - ((value - min) / range) * height
    return `${x},${y}`
  }).join(' ')

  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
    >
      <polyline
        fill="none"
        stroke="var(--accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/Sparkline.tsx
git commit -m "feat(ui): add Sparkline SVG component"
```

---

## Task 6: UI Components - ThemeToggle

**Files:**
- Create: `frontend/src/components/ui/ThemeToggle.tsx`

**Step 1: Create ThemeToggle component**

```typescript
// frontend/src/components/ui/ThemeToggle.tsx
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className={`
        w-10 h-10 flex items-center justify-center
        rounded-full transition-all duration-200
        hover:bg-vault-border/50
        focus:outline-none focus:ring-2 focus:ring-vault-accent focus:ring-offset-2
        ${className}
      `}
      aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5 text-vault-text" />
      ) : (
        <Sun className="w-5 h-5 text-vault-text" />
      )}
    </button>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/ThemeToggle.tsx
git commit -m "feat(ui): add ThemeToggle component with Sun/Moon icons"
```

---

## Task 7: UI Components - KpiCard

**Files:**
- Create: `frontend/src/components/ui/KpiCard.tsx`

**Step 1: Create KpiCard component**

```typescript
// frontend/src/components/ui/KpiCard.tsx
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Sparkline } from './Sparkline'
import type { KpiData } from '../../data/mockDashboard'

interface KpiCardProps extends KpiData {
  className?: string
}

export function KpiCard({
  value,
  label,
  change,
  sparkData,
  className = ''
}: KpiCardProps) {
  const isPositive = change >= 0

  return (
    <div
      className={`
        bg-vault-card rounded-card p-6 shadow-card
        hover:shadow-card-hover transition-shadow duration-200
        ${className}
      `}
    >
      {/* Header with sparkline and change */}
      <div className="flex items-start justify-between mb-4">
        <Sparkline data={sparkData} width={80} height={32} />
        <div
          className={`
            flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full
            ${isPositive
              ? 'bg-vault-success/10 text-vault-success'
              : 'bg-vault-danger/10 text-vault-danger'
            }
          `}
        >
          {isPositive ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          <span>{isPositive ? '+' : ''}{change}%</span>
        </div>
      </div>

      {/* Value */}
      <div className="text-2xl font-bold text-vault-text font-sans mb-1">
        {value}
      </div>

      {/* Label */}
      <div className="text-sm text-vault-text-muted">
        {label}
      </div>
    </div>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/KpiCard.tsx
git commit -m "feat(ui): add KpiCard component with sparkline and change indicator"
```

---

## Task 8: UI Components - ActionCard

**Files:**
- Create: `frontend/src/components/ui/ActionCard.tsx`

**Step 1: Create ActionCard component**

```typescript
// frontend/src/components/ui/ActionCard.tsx
import { useNavigate } from 'react-router-dom'
import { BookOpen, Bell, FileText } from 'lucide-react'
import type { ActionCardData } from '../../data/mockDashboard'

const iconMap = {
  BookOpen,
  Bell,
  FileText,
}

interface ActionCardProps extends ActionCardData {
  className?: string
}

export function ActionCard({
  title,
  icon,
  lines,
  action,
  className = ''
}: ActionCardProps) {
  const navigate = useNavigate()
  const IconComponent = iconMap[icon]

  const handleAction = () => {
    if (action.href) {
      navigate(action.href)
    } else if (action.onClick) {
      action.onClick()
    }
  }

  return (
    <div
      className={`
        bg-vault-card rounded-card-sm p-5 shadow-card
        border-l-[3px] border-vault-accent
        hover:shadow-card-hover transition-shadow duration-200
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-base font-semibold text-vault-text">
          {title}
        </h3>
        <IconComponent className="w-5 h-5 text-vault-text-muted" />
      </div>

      {/* Content lines */}
      <div className="space-y-1 mb-4">
        {lines.map((line, index) => (
          <p key={index} className="text-sm text-vault-text-muted">
            {line}
          </p>
        ))}
      </div>

      {/* Action button */}
      <button
        onClick={handleAction}
        className="
          text-sm font-medium text-vault-accent
          hover:text-vault-accent-hover hover:underline
          transition-colors duration-200
        "
      >
        {action.label}
      </button>
    </div>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/ActionCard.tsx
git commit -m "feat(ui): add ActionCard component with icon and ghost button"
```

---

## Task 9: UI Components - ActivityFeed

**Files:**
- Create: `frontend/src/components/ui/ActivityFeed.tsx`

**Step 1: Create ActivityFeed component**

```typescript
// frontend/src/components/ui/ActivityFeed.tsx
import { BarChart3, Search, CheckCircle, Bookmark, AlertTriangle } from 'lucide-react'
import type { ActivityEvent } from '../../data/mockDashboard'

const iconMap = {
  analysis: BarChart3,
  niche: Search,
  verification: CheckCircle,
  search_saved: Bookmark,
  alert: AlertTriangle,
}

const colorMap = {
  analysis: 'text-vault-accent',
  niche: 'text-vault-success',
  verification: 'text-vault-success',
  search_saved: 'text-vault-accent',
  alert: 'text-vault-danger',
}

interface ActivityFeedProps {
  events: ActivityEvent[]
  className?: string
}

export function ActivityFeed({ events, className = '' }: ActivityFeedProps) {
  return (
    <div
      className={`
        bg-vault-card rounded-card-sm shadow-card overflow-hidden
        ${className}
      `}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-vault-border">
        <h3 className="text-base font-semibold text-vault-text">
          Activity Feed
        </h3>
      </div>

      {/* Events */}
      <div className="divide-y divide-vault-border">
        {events.map((event) => {
          const IconComponent = iconMap[event.type]
          const colorClass = colorMap[event.type]

          return (
            <div
              key={event.id}
              className="px-6 py-4 hover:bg-vault-bg transition-colors duration-150"
            >
              <div className="flex items-start gap-3">
                <IconComponent className={`w-5 h-5 mt-0.5 ${colorClass}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-vault-text">
                    <span className="text-vault-text-muted">{event.timestamp}</span>
                    {' - '}
                    {event.message}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/ActivityFeed.tsx
git commit -m "feat(ui): add ActivityFeed component with event types"
```

---

## Task 10: UI Components - SearchBar

**Files:**
- Create: `frontend/src/components/ui/SearchBar.tsx`

**Step 1: Create SearchBar component**

```typescript
// frontend/src/components/ui/SearchBar.tsx
import { Search } from 'lucide-react'

interface SearchBarProps {
  placeholder?: string
  className?: string
}

export function SearchBar({
  placeholder = "Search books, ISBN, authors...",
  className = ''
}: SearchBarProps) {
  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
      <input
        type="text"
        placeholder={placeholder}
        className="
          w-full h-10 pl-12 pr-4
          bg-vault-bg border border-vault-border
          rounded-full text-sm text-vault-text
          placeholder:text-vault-text-muted
          focus:outline-none focus:ring-2 focus:ring-vault-accent focus:border-transparent
          transition-all duration-200
        "
      />
    </div>
  )
}
```

**Step 2: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ui/SearchBar.tsx
git commit -m "feat(ui): add SearchBar component with rounded style"
```

---

## Task 11: UI Components Index Export

**Files:**
- Create: `frontend/src/components/ui/index.ts`

**Step 1: Create barrel export**

```typescript
// frontend/src/components/ui/index.ts
export { Sparkline } from './Sparkline'
export { ThemeToggle } from './ThemeToggle'
export { KpiCard } from './KpiCard'
export { ActionCard } from './ActionCard'
export { ActivityFeed } from './ActivityFeed'
export { SearchBar } from './SearchBar'
```

**Step 2: Commit**

```bash
git add frontend/src/components/ui/index.ts
git commit -m "feat(ui): add barrel export for UI components"
```

---

## Task 12: Layout Redesign

**Files:**
- Modify: `frontend/src/components/Layout/Layout.tsx`

**Step 1: Complete Layout redesign**

Replace entire `frontend/src/components/Layout/Layout.tsx`:

```typescript
// frontend/src/components/Layout/Layout.tsx
import { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import {
  Menu, X, LayoutDashboard, BarChart3, Search,
  BookMarked, Bot, Package, Bookmark, Settings
} from 'lucide-react'
import { ThemeToggle, SearchBar } from '../ui'

interface LayoutProps {
  children: ReactNode
}

const navigationItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { name: 'Analyse Manuelle', icon: BarChart3, href: '/analyse' },
  { name: 'Niche Discovery', icon: Search, href: '/niche-discovery' },
  { name: 'Mes Niches', icon: BookMarked, href: '/mes-niches' },
  { type: 'separator' as const },
  { name: 'AutoScheduler', icon: Bot, href: '/autoscheduler' },
  { name: 'AutoSourcing', icon: Package, href: '/autosourcing' },
  { name: 'Mes Recherches', icon: Bookmark, href: '/recherches' },
  { type: 'separator' as const },
  { name: 'Configuration', icon: Settings, href: '/config' },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false)

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen bg-vault-bg">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-vault-card border-b border-vault-border z-50">
        <div className="flex items-center justify-between h-full px-4 md:px-6">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-vault-accent rounded-lg flex items-center justify-center">
              <BookMarked className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-sans">
              <span className="font-normal text-vault-text">Arbitrage</span>
              <span className="font-bold text-vault-text">Vault</span>
            </span>
          </div>

          {/* Center: Search (hidden on mobile) */}
          <div className="hidden md:block flex-1 max-w-md mx-8">
            <SearchBar />
          </div>

          {/* Right: Theme toggle + Avatar + Mobile menu */}
          <div className="flex items-center gap-2">
            <ThemeToggle />

            {/* Avatar */}
            <div className="w-10 h-10 rounded-full bg-vault-accent/20 border-2 border-vault-accent flex items-center justify-center">
              <span className="text-sm font-semibold text-vault-accent">AZ</span>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-vault-border/50 transition-colors md:hidden"
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6 text-vault-text" />
              ) : (
                <Menu className="w-6 h-6 text-vault-text" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile backdrop */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        onMouseEnter={() => setIsSidebarExpanded(true)}
        onMouseLeave={() => setIsSidebarExpanded(false)}
        className={`
          fixed left-0 top-16 bottom-0 bg-vault-sidebar border-r border-vault-border z-40
          transition-all duration-200 ease-in-out overflow-hidden
          ${isMobileMenuOpen
            ? 'w-64 translate-x-0'
            : '-translate-x-full md:translate-x-0'
          }
          ${isSidebarExpanded ? 'md:w-64' : 'md:w-[72px]'}
        `}
      >
        <nav className="py-4 px-2">
          <div className="space-y-1">
            {navigationItems.map((item, index) => {
              if (item.type === 'separator') {
                return (
                  <div key={`sep-${index}`} className="my-3 mx-2 border-t border-vault-border" />
                )
              }

              const isActive = location.pathname === item.href ||
                (item.href === '/dashboard' && location.pathname === '/')
              const Icon = item.icon

              return (
                <Link
                  key={item.href}
                  to={item.href!}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`
                    flex items-center gap-3 px-3 py-3 rounded-lg
                    transition-all duration-150 relative
                    ${isActive
                      ? 'bg-vault-accent/10 text-vault-accent font-medium'
                      : 'text-vault-text-muted hover:bg-vault-border/50 hover:text-vault-text'
                    }
                  `}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-8 bg-vault-accent rounded-r-full" />
                  )}

                  <Icon className="w-5 h-5 flex-shrink-0" />

                  <span
                    className={`
                      text-sm whitespace-nowrap transition-opacity duration-200
                      ${isSidebarExpanded || isMobileMenuOpen ? 'opacity-100' : 'opacity-0 md:opacity-0'}
                    `}
                  >
                    {item.name}
                  </span>
                </Link>
              )
            })}
          </div>
        </nav>
      </aside>

      {/* Main content */}
      <main
        className={`
          pt-16 min-h-screen transition-all duration-200
          ${isSidebarExpanded ? 'md:ml-64' : 'md:ml-[72px]'}
        `}
      >
        <div className="p-4 md:p-8 max-w-[1400px]">
          {children}
        </div>
      </main>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/Layout/Layout.tsx
git commit -m "feat(layout): redesign Layout with Vault Elegance theme"
```

---

## Task 13: Dashboard Redesign

**Files:**
- Modify: `frontend/src/components/Dashboard/Dashboard.tsx`

**Step 1: Complete Dashboard redesign**

Replace entire `frontend/src/components/Dashboard/Dashboard.tsx`:

```typescript
// frontend/src/components/Dashboard/Dashboard.tsx
import { KpiCard, ActionCard, ActivityFeed } from '../ui'
import {
  mockKpiData,
  mockActionCards,
  mockActivityFeed,
  getGreeting,
  formatDate
} from '../../data/mockDashboard'

export default function Dashboard() {
  const greeting = getGreeting()
  const dateString = formatDate()

  return (
    <div className="space-y-8">
      {/* Greeting Section */}
      <section>
        <h1 className="text-4xl font-display font-semibold text-vault-text mb-1">
          {greeting} Aziz
        </h1>
        <p className="text-sm text-vault-text-muted">
          {dateString}
        </p>
      </section>

      {/* KPI Cards */}
      <section>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <KpiCard {...mockKpiData.totalValue} />
          <KpiCard {...mockKpiData.productsAnalyzed} />
          <KpiCard {...mockKpiData.avgRoi} />
          <KpiCard {...mockKpiData.pendingReviews} />
        </div>
      </section>

      {/* Action Cards */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          {mockActionCards.map((card, index) => (
            <ActionCard key={index} {...card} />
          ))}
        </div>
      </section>

      {/* Activity Feed */}
      <section>
        <ActivityFeed events={mockActivityFeed} />
      </section>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/Dashboard/Dashboard.tsx
git commit -m "feat(dashboard): redesign Dashboard with Vault Elegance components"
```

---

## Task 14: Verification and Polish

**Files:**
- All files from previous tasks

**Step 1: Full build verification**

Run: `cd frontend && npm run build`
Expected: Build succeeds with 0 errors

**Step 2: Type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No TypeScript errors

**Step 3: Start dev server and visual test**

Run: `cd frontend && npm run dev`

Manual verification checklist:
- [ ] Light mode displays correctly (beige/cream background)
- [ ] Dark mode toggle works (navy/gold theme)
- [ ] Theme persists on page refresh
- [ ] 4 KPI cards display with sparklines
- [ ] 3 Action cards display with working buttons
- [ ] Activity Feed shows 5 events
- [ ] Sidebar collapses on desktop, expands on hover
- [ ] Mobile menu works (hamburger button)
- [ ] Greeting shows correct time-based message
- [ ] Responsive layout works at all breakpoints

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(vault-elegance): complete Dashboard + Layout redesign with dark mode"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Theme CSS Variables | theme.css, index.css, index.html |
| 2 | ThemeContext | ThemeContext.tsx, App.tsx |
| 3 | Tailwind Config | tailwind.config.js |
| 4 | Mock Data | mockDashboard.ts |
| 5 | Sparkline | Sparkline.tsx |
| 6 | ThemeToggle | ThemeToggle.tsx |
| 7 | KpiCard | KpiCard.tsx |
| 8 | ActionCard | ActionCard.tsx |
| 9 | ActivityFeed | ActivityFeed.tsx |
| 10 | SearchBar | SearchBar.tsx |
| 11 | UI Index | ui/index.ts |
| 12 | Layout | Layout.tsx |
| 13 | Dashboard | Dashboard.tsx |
| 14 | Verification | All files |

**Total commits:** 14
**Estimated time:** 2-3 hours
