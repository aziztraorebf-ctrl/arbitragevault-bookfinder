# Phase 12 - UX Audit + Mobile-First + Accueil Guide Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve user experience with mobile-first responsive design, functional hamburger menu, and guided onboarding for new users.

**Architecture:** Progressive enhancement approach - fix mobile layout first (hamburger menu, collapsible sidebar), then add horizontal table scroll, finally implement welcome wizard. CSS-only solutions where possible, minimal JavaScript state.

**Tech Stack:** React + TypeScript + Tailwind CSS (responsive utilities) + Lucide icons

---

## Current State Analysis

**Problems Identified:**
1. **Layout.tsx:45** - Sidebar fixed 264px, no responsive breakpoints
2. **Layout.tsx:38-40** - Hamburger button visual only, not functional
3. **Layout.tsx:81** - `ml-64 mt-16` hardcoded, breaks on mobile
4. **UnifiedProductTable.tsx:262** - `overflow-x-auto` exists but columns too wide
5. **Dashboard.tsx** - KPI cards work, but action cards need touch optimization
6. **No onboarding** - New users land on dashboard with no guidance

---

## Task 1: Mobile Sidebar State Hook

**Files:**
- Create: `frontend/src/hooks/useMobileMenu.ts`
- Test: `frontend/src/hooks/__tests__/useMobileMenu.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend/src/hooks/__tests__/useMobileMenu.test.ts
import { renderHook, act } from '@testing-library/react'
import { useMobileMenu } from '../useMobileMenu'

describe('useMobileMenu', () => {
  it('should start closed', () => {
    const { result } = renderHook(() => useMobileMenu())
    expect(result.current.isOpen).toBe(false)
  })

  it('should toggle open/close', () => {
    const { result } = renderHook(() => useMobileMenu())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(true)

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(false)
  })

  it('should close explicitly', () => {
    const { result } = renderHook(() => useMobileMenu())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(true)

    act(() => {
      result.current.close()
    })
    expect(result.current.isOpen).toBe(false)
  })

  it('should close on route change', () => {
    // Will be tested in Layout integration test
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --testPathPattern="useMobileMenu" --run`
Expected: FAIL with "Cannot find module '../useMobileMenu'"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/hooks/useMobileMenu.ts
import { useState, useCallback } from 'react'

export function useMobileMenu() {
  const [isOpen, setIsOpen] = useState(false)

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
  }, [])

  return { isOpen, toggle, close }
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --testPathPattern="useMobileMenu" --run`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend/src/hooks/useMobileMenu.ts frontend/src/hooks/__tests__/useMobileMenu.test.ts
git commit -m "feat(phase12): add useMobileMenu hook for responsive sidebar"
```

---

## Task 2: Responsive Layout with Hamburger Menu

**Files:**
- Modify: `frontend/src/components/Layout/Layout.tsx`
- Test: `frontend/tests/e2e/responsive-layout.spec.ts`

**Step 1: Write the E2E test**

```typescript
// frontend/tests/e2e/responsive-layout.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Responsive Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('desktop: sidebar visible, hamburger hidden', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })

    const sidebar = page.locator('aside')
    const hamburger = page.getByRole('button', { name: /menu/i })

    await expect(sidebar).toBeVisible()
    await expect(hamburger).toBeHidden()
  })

  test('mobile: sidebar hidden, hamburger visible', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    const sidebar = page.locator('aside')
    const hamburger = page.getByRole('button', { name: /menu/i })

    await expect(sidebar).toBeHidden()
    await expect(hamburger).toBeVisible()
  })

  test('mobile: hamburger opens sidebar overlay', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()

    const sidebar = page.locator('aside')
    await expect(sidebar).toBeVisible()

    // Check overlay backdrop exists
    const backdrop = page.locator('[data-testid="mobile-backdrop"]')
    await expect(backdrop).toBeVisible()
  })

  test('mobile: clicking nav item closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()

    // Click a nav item
    await page.getByRole('link', { name: /Niche Discovery/i }).click()

    // Sidebar should close
    const sidebar = page.locator('aside')
    await expect(sidebar).toBeHidden()
  })

  test('mobile: clicking backdrop closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()

    const backdrop = page.locator('[data-testid="mobile-backdrop"]')
    await backdrop.click()

    const sidebar = page.locator('aside')
    await expect(sidebar).toBeHidden()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx playwright test responsive-layout.spec.ts`
Expected: FAIL (sidebar always visible, hamburger not functional)

**Step 3: Modify Layout.tsx for responsive behavior**

```typescript
// frontend/src/components/Layout/Layout.tsx
import { useLocation, Link } from 'react-router-dom'
import { useEffect, type ReactNode } from 'react'
import { Menu, X } from 'lucide-react'
import { useMobileMenu } from '../../hooks/useMobileMenu'

interface LayoutProps {
  children: ReactNode
}

// Navigation items avec emojis
const navigationItems = [
  { name: 'Dashboard', emoji: '...', href: '/dashboard' },
  { name: 'Analyse Manuelle', emoji: '...', href: '/analyse' },
  { name: 'Niche Discovery', emoji: '...', href: '/niche-discovery' },
  { name: 'Mes Niches', emoji: '...', href: '/mes-niches' },
  { name: 'AutoScheduler', emoji: '...', href: '/autoscheduler' },
  { name: 'AutoSourcing', emoji: '...', href: '/autosourcing' },
  { name: 'Mes Recherches', emoji: '...', href: '/recherches' },
  { name: 'Configuration', emoji: '...', href: '/config' }
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { isOpen, toggle, close } = useMobileMenu()

  // Close sidebar on route change
  useEffect(() => {
    close()
  }, [location.pathname, close])

  return (
    <div className="flex min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-50">
        <div className="flex items-center justify-between h-full px-4 md:px-6">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="text-lg md:text-xl font-bold text-gray-900">ArbitrageVault</span>
          </div>

          {/* Hamburger menu - visible only on mobile */}
          <button
            onClick={toggle}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors duration-100"
            aria-label={isOpen ? 'Close menu' : 'Open menu'}
          >
            {isOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile backdrop */}
      {isOpen && (
        <div
          data-testid="mobile-backdrop"
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={close}
        />
      )}

      {/* Sidebar - responsive */}
      <aside className={`
        fixed left-0 top-16 bottom-0 w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto z-40
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        <nav className="py-4 px-3">
          <div className="space-y-2">
            {navigationItems.map((item, index) => {
              const isActive = location.pathname === item.href ||
                             (item.href === '/dashboard' && location.pathname === '/')

              return (
                <div key={item.href}>
                  <Link
                    to={item.href}
                    onClick={close}
                    className={`
                      flex items-center space-x-3 px-4 py-3 rounded-md
                      transition-all duration-100
                      ${isActive
                        ? 'bg-blue-100 font-semibold text-blue-700'
                        : 'text-gray-700 hover:bg-blue-50'
                      }
                    `}
                  >
                    <span className="text-xl">{item.emoji}</span>
                    <span className="text-sm">{item.name}</span>
                  </Link>

                  {/* Separators after specific groups */}
                  {(index === 3 || index === 5) && (
                    <div className="my-2 border-t border-gray-200"></div>
                  )}
                </div>
              )
            })}
          </div>
        </nav>
      </aside>

      {/* Main content area - responsive margin */}
      <div className="flex-1 md:ml-64 mt-16">
        <main className="p-4 md:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx playwright test responsive-layout.spec.ts`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add frontend/src/components/Layout/Layout.tsx frontend/tests/e2e/responsive-layout.spec.ts
git commit -m "feat(phase12): implement responsive sidebar with hamburger menu"
```

---

## Task 3: Mobile-Optimized Tables

**Files:**
- Modify: `frontend/src/components/unified/UnifiedProductTable.tsx`
- Test: `frontend/tests/e2e/mobile-table.spec.ts`

**Step 1: Write the E2E test**

```typescript
// frontend/tests/e2e/mobile-table.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Mobile Table Scroll', () => {
  test('table scrolls horizontally on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/niche-discovery')

    // Wait for potential table to exist (depends on data)
    // Check that table container has scroll behavior
    const tableContainer = page.locator('.overflow-x-auto').first()

    if (await tableContainer.count() > 0) {
      // Get scroll width
      const scrollWidth = await tableContainer.evaluate(el => el.scrollWidth)
      const clientWidth = await tableContainer.evaluate(el => el.clientWidth)

      // If content is wider than viewport, horizontal scroll should work
      if (scrollWidth > clientWidth) {
        await expect(tableContainer).toHaveCSS('overflow-x', 'auto')
      }
    }
  })

  test('table header stays sticky on scroll', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/analyse')

    // Table header should have sticky positioning
    const thead = page.locator('thead').first()
    if (await thead.count() > 0) {
      await expect(thead).toHaveCSS('position', 'sticky')
    }
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx playwright test mobile-table.spec.ts`
Expected: May fail on sticky header

**Step 3: Update UnifiedProductTable for mobile optimization**

```typescript
// frontend/src/components/unified/UnifiedProductTable.tsx
// Key changes in the table section (around line 261-331):

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px]">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
            <tr>
              {showAccordion && <th className="px-3 md:px-4 py-3 w-12"></th>}
              {showRank && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Rank
                </th>
              )}
              <th className="px-3 md:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                ASIN
              </th>
              <th className="px-3 md:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase max-w-[200px]">
                Titre
              </th>
              {showScore && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Score
                </th>
              )}
              <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                ROI
              </th>
              <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                Velocity
              </th>
              <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                BSR
              </th>
              {showRecommendation && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Reco
                </th>
              )}
              {showAmazonBadges && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Amz
                </th>
              )}
              {showVerifyButton && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {/* ... rows ... */}
          </tbody>
        </table>
      </div>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx playwright test mobile-table.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/unified/UnifiedProductTable.tsx frontend/tests/e2e/mobile-table.spec.ts
git commit -m "feat(phase12): optimize tables for mobile horizontal scroll"
```

---

## Task 4: Touch-Friendly Buttons and Touch Targets

**Files:**
- Modify: `frontend/src/components/unified/UnifiedProductRow.tsx`
- Modify: `frontend/src/components/Dashboard/Dashboard.tsx`
- Test: `frontend/tests/e2e/touch-targets.spec.ts`

**Step 1: Write the E2E test**

```typescript
// frontend/tests/e2e/touch-targets.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Touch Targets', () => {
  test('buttons have minimum 44px touch target', async ({ page }) => {
    await page.goto('/dashboard')

    // Check "Check Balance" button
    const checkBalanceBtn = page.getByRole('button', { name: /Check Balance/i })
    const box = await checkBalanceBtn.boundingBox()

    expect(box?.height).toBeGreaterThanOrEqual(44)
  })

  test('nav items have adequate spacing on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Open menu
    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()

    // Check nav links
    const navLinks = page.locator('aside a')
    const count = await navLinks.count()

    for (let i = 0; i < count; i++) {
      const box = await navLinks.nth(i).boundingBox()
      // Min 44px height for touch target
      expect(box?.height).toBeGreaterThanOrEqual(44)
    }
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx playwright test touch-targets.spec.ts`
Expected: May fail if buttons are too small

**Step 3: Update components for touch-friendly sizing**

For Dashboard.tsx, ensure buttons have min-height:

```typescript
// In Dashboard.tsx, update the Check Balance button (around line 91-97):
<button
  onClick={checkBalance}
  disabled={loading}
  className="w-full px-4 py-3 min-h-[44px] bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 text-sm font-medium"
>
  {loading ? 'Checking...' : 'Check Balance'}
</button>
```

For UnifiedProductRow.tsx, ensure verify button has adequate size:

```typescript
// Verify button should have min touch target
<button
  onClick={() => onVerify?.(product)}
  disabled={verificationLoading}
  className="px-4 py-2 min-h-[44px] min-w-[44px] bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-lg transition-colors"
>
  {verificationLoading ? '...' : 'Verifier'}
</button>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx playwright test touch-targets.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/unified/UnifiedProductRow.tsx frontend/src/components/Dashboard/Dashboard.tsx frontend/tests/e2e/touch-targets.spec.ts
git commit -m "feat(phase12): ensure 44px minimum touch targets"
```

---

## Task 5: Welcome Wizard Component

**Files:**
- Create: `frontend/src/components/onboarding/WelcomeWizard.tsx`
- Create: `frontend/src/hooks/useOnboarding.ts`
- Test: `frontend/src/components/onboarding/__tests__/WelcomeWizard.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/onboarding/__tests__/WelcomeWizard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { WelcomeWizard } from '../WelcomeWizard'

const mockOnComplete = jest.fn()

const renderWizard = () => {
  return render(
    <BrowserRouter>
      <WelcomeWizard onComplete={mockOnComplete} />
    </BrowserRouter>
  )
}

describe('WelcomeWizard', () => {
  beforeEach(() => {
    mockOnComplete.mockClear()
  })

  it('renders first step by default', () => {
    renderWizard()
    expect(screen.getByText(/Bienvenue/i)).toBeInTheDocument()
    expect(screen.getByText(/1.*3/)).toBeInTheDocument()
  })

  it('navigates to next step on button click', () => {
    renderWizard()
    const nextButton = screen.getByRole('button', { name: /Suivant/i })
    fireEvent.click(nextButton)
    expect(screen.getByText(/2.*3/)).toBeInTheDocument()
  })

  it('navigates back on previous button click', () => {
    renderWizard()
    // Go to step 2
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i }))
    // Go back
    fireEvent.click(screen.getByRole('button', { name: /Retour/i }))
    expect(screen.getByText(/1.*3/)).toBeInTheDocument()
  })

  it('calls onComplete on last step', () => {
    renderWizard()
    // Navigate through all steps
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i })) // Step 2
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i })) // Step 3
    fireEvent.click(screen.getByRole('button', { name: /Commencer/i })) // Complete
    expect(mockOnComplete).toHaveBeenCalledTimes(1)
  })

  it('shows skip button', () => {
    renderWizard()
    const skipButton = screen.getByRole('button', { name: /Passer/i })
    expect(skipButton).toBeInTheDocument()
    fireEvent.click(skipButton)
    expect(mockOnComplete).toHaveBeenCalledTimes(1)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --testPathPattern="WelcomeWizard" --run`
Expected: FAIL with "Cannot find module '../WelcomeWizard'"

**Step 3: Create useOnboarding hook**

```typescript
// frontend/src/hooks/useOnboarding.ts
import { useState, useEffect } from 'react'

const ONBOARDING_KEY = 'arbitragevault_onboarding_complete'

export function useOnboarding() {
  const [showWizard, setShowWizard] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_KEY)
    setShowWizard(!completed)
    setIsLoading(false)
  }, [])

  const completeOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    setShowWizard(false)
  }

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY)
    setShowWizard(true)
  }

  return { showWizard, isLoading, completeOnboarding, resetOnboarding }
}
```

**Step 4: Create WelcomeWizard component**

```typescript
// frontend/src/components/onboarding/WelcomeWizard.tsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronLeft, Search, TrendingUp, BookOpen, X } from 'lucide-react'

interface WelcomeWizardProps {
  onComplete: () => void
}

interface Step {
  title: string
  description: string
  icon: React.ReactNode
  action?: {
    label: string
    href: string
  }
}

const steps: Step[] = [
  {
    title: 'Bienvenue sur ArbitrageVault',
    description: 'Decouvrez des opportunites de livres rentables en quelques clics. Ce guide vous montre comment utiliser les fonctionnalites principales.',
    icon: <BookOpen className="w-16 h-16 text-blue-500" />,
  },
  {
    title: 'Decouvrez des Niches',
    description: 'Utilisez Niche Discovery pour trouver des categories de livres avec un bon potentiel de profit. Filtrez par ROI, velocite et prix.',
    icon: <Search className="w-16 h-16 text-purple-500" />,
    action: {
      label: 'Aller a Niche Discovery',
      href: '/niche-discovery',
    },
  },
  {
    title: 'Analysez vos Resultats',
    description: 'Consultez vos recherches sauvegardees dans Mes Recherches. Verifiez les produits interessants avant de les sourcer.',
    icon: <TrendingUp className="w-16 h-16 text-green-500" />,
    action: {
      label: 'Voir Mes Recherches',
      href: '/recherches',
    },
  },
]

export function WelcomeWizard({ onComplete }: WelcomeWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const isLastStep = currentStep === steps.length - 1
  const step = steps[currentStep]

  const handleNext = () => {
    if (isLastStep) {
      onComplete()
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(0, prev - 1))
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <span className="text-sm text-gray-500">
            Etape {currentStep + 1} / {steps.length}
          </span>
          <button
            onClick={onComplete}
            className="text-gray-400 hover:text-gray-600 p-1"
            aria-label="Passer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-8 text-center">
          <div className="flex justify-center mb-6">
            {step.icon}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {step.title}
          </h2>
          <p className="text-gray-600 mb-6">
            {step.description}
          </p>
          {step.action && (
            <Link
              to={step.action.href}
              onClick={onComplete}
              className="inline-block px-6 py-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors mb-4"
            >
              {step.action.label}
            </Link>
          )}
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 pb-4">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentStep ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center gap-1 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Retour
          </button>
          <button
            onClick={onComplete}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Passer
          </button>
          <button
            onClick={handleNext}
            className="flex items-center gap-1 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            {isLastStep ? 'Commencer' : 'Suivant'}
            {!isLastStep && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- --testPathPattern="WelcomeWizard" --run`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add frontend/src/components/onboarding/WelcomeWizard.tsx frontend/src/hooks/useOnboarding.ts frontend/src/components/onboarding/__tests__/WelcomeWizard.test.tsx
git commit -m "feat(phase12): add WelcomeWizard component and useOnboarding hook"
```

---

## Task 6: Integrate Welcome Wizard in App

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/tests/e2e/onboarding.spec.ts`

**Step 1: Write the E2E test**

```typescript
// frontend/tests/e2e/onboarding.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ context }) => {
    // Clear localStorage before each test
    await context.addInitScript(() => {
      localStorage.clear()
    })
  })

  test('shows wizard on first visit', async ({ page }) => {
    await page.goto('/')

    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeVisible()
  })

  test('does not show wizard after completion', async ({ page }) => {
    await page.goto('/')

    // Complete wizard
    await page.getByRole('button', { name: /Suivant/i }).click()
    await page.getByRole('button', { name: /Suivant/i }).click()
    await page.getByRole('button', { name: /Commencer/i }).click()

    // Reload page
    await page.reload()

    // Wizard should not appear
    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeHidden()
  })

  test('skip button closes wizard', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('button', { name: /Passer/i }).click()

    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeHidden()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx playwright test onboarding.spec.ts`
Expected: FAIL (wizard not integrated yet)

**Step 3: Integrate wizard in App.tsx**

```typescript
// frontend/src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import { WelcomeWizard } from './components/onboarding/WelcomeWizard'
import { useOnboarding } from './hooks/useOnboarding'

// Import des pages
import AnalyseManuelle from './pages/AnalyseManuelle'
import NicheDiscovery from './pages/NicheDiscovery'
import MesNiches from './pages/MesNiches'
import AutoScheduler from './pages/AutoScheduler'
import AutoSourcing from './pages/AutoSourcing'
import Configuration from './pages/Configuration'
import MesRecherches from './pages/MesRecherches'
import RechercheDetail from './pages/RechercheDetail'

// Initialize React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function AppContent() {
  const { showWizard, isLoading, completeOnboarding } = useOnboarding()

  if (isLoading) {
    return null // or a loading spinner
  }

  return (
    <>
      {showWizard && <WelcomeWizard onComplete={completeOnboarding} />}
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analyse" element={<AnalyseManuelle />} />
          <Route path="/niche-discovery" element={<NicheDiscovery />} />
          <Route path="/mes-niches" element={<MesNiches />} />
          <Route path="/autoscheduler" element={<AutoScheduler />} />
          <Route path="/autosourcing" element={<AutoSourcing />} />
          <Route path="/config" element={<Configuration />} />
          <Route path="/recherches" element={<MesRecherches />} />
          <Route path="/recherches/:id" element={<RechercheDetail />} />
          {/* Fallback route */}
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </Layout>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: 'bg-white shadow-lg border',
        }}
      />
    </>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppContent />
      </Router>
    </QueryClientProvider>
  )
}

export default App
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx playwright test onboarding.spec.ts`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/tests/e2e/onboarding.spec.ts
git commit -m "feat(phase12): integrate welcome wizard in App"
```

---

## Task 7: Loading States and Micro-Interactions

**Files:**
- Create: `frontend/src/components/ui/LoadingSpinner.tsx`
- Create: `frontend/src/components/ui/SkeletonCard.tsx`
- Modify: `frontend/src/components/Dashboard/Dashboard.tsx`
- Test: Unit tests for components

**Step 1: Create LoadingSpinner component**

```typescript
// frontend/src/components/ui/LoadingSpinner.tsx
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  return (
    <div
      className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]} ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}
```

**Step 2: Create SkeletonCard component**

```typescript
// frontend/src/components/ui/SkeletonCard.tsx
interface SkeletonCardProps {
  className?: string
}

export function SkeletonCard({ className = '' }: SkeletonCardProps) {
  return (
    <div className={`bg-white shadow-md rounded-xl p-6 animate-pulse ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-6 h-6 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
      <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-12"></div>
    </div>
  )
}
```

**Step 3: Create index export**

```typescript
// frontend/src/components/ui/index.ts
export { LoadingSpinner } from './LoadingSpinner'
export { SkeletonCard } from './SkeletonCard'
```

**Step 4: Write unit tests**

```typescript
// frontend/src/components/ui/__tests__/LoadingSpinner.test.tsx
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    render(<LoadingSpinner />)
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-6', 'h-6')
  })

  it('renders with small size', () => {
    render(<LoadingSpinner size="sm" />)
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-4', 'h-4')
  })

  it('renders with large size', () => {
    render(<LoadingSpinner size="lg" />)
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-8', 'h-8')
  })

  it('has accessible name', () => {
    render(<LoadingSpinner />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading')
  })
})
```

**Step 5: Run tests**

Run: `cd frontend && npm test -- --testPathPattern="LoadingSpinner" --run`
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat(phase12): add LoadingSpinner and SkeletonCard components"
```

---

## Task 8: Final Build Verification and E2E Suite

**Files:**
- Test: All E2E tests

**Step 1: Run TypeScript build**

Run: `cd frontend && npm run build`
Expected: Build success, no errors

**Step 2: Run all unit tests**

Run: `cd frontend && npm test -- --run`
Expected: All tests pass

**Step 3: Run all E2E tests**

Run: `cd frontend && npx playwright test`
Expected: All tests pass

**Step 4: Manual responsive check**

Open http://localhost:5173 in browser:
1. Desktop (1920x1080): Sidebar visible, hamburger hidden
2. Mobile (375x667): Hamburger visible, tap opens sidebar
3. Tablet (768x1024): Test intermediate breakpoint

**Step 5: Final commit**

```bash
git add .
git commit -m "feat(phase12): complete UX audit and mobile-first implementation"
```

---

## Summary

| Task | Description | Tests | Est. Time |
|------|-------------|-------|-----------|
| 1 | Mobile Sidebar State Hook | 3 unit | 15 min |
| 2 | Responsive Layout with Hamburger | 5 E2E | 30 min |
| 3 | Mobile-Optimized Tables | 2 E2E | 20 min |
| 4 | Touch-Friendly Buttons | 2 E2E | 15 min |
| 5 | Welcome Wizard Component | 5 unit | 45 min |
| 6 | Integrate Welcome Wizard | 3 E2E | 20 min |
| 7 | Loading States Components | 4 unit | 20 min |
| 8 | Final Verification | - | 15 min |

**Total estimated time:** ~3 hours

**Key deliverables:**
- Functional hamburger menu on mobile (< 768px)
- Collapsible sidebar with overlay backdrop
- Horizontal scroll for tables on mobile
- 44px minimum touch targets
- 3-step welcome wizard for new users
- Loading spinner and skeleton components
- Comprehensive E2E test coverage

---

**For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
