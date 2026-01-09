/**
 * E2E Tests - Niche Discovery Page
 * Tests Vault Elegance design implementation
 */

import { test, expect } from '@playwright/test'

test.describe('Niche Discovery - Vault Elegance', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('onboarding_completed', 'true')
      localStorage.setItem('hasSeenWelcome', 'true')
    })
    await page.goto('/niche-discovery')
    await page.waitForLoadState('networkidle')

    // Close onboarding modal if present
    const skipBtn = page.locator('button:has-text("Passer")').first()
    if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await skipBtn.click()
      await page.waitForTimeout(300)
    }
  })

  test('should display page with Vault title and subtitle', async ({ page }) => {
    // Check page title with Vault typography
    const title = page.locator('h1')
    await expect(title).toBeVisible()
    await expect(title).toHaveText('Niche Discovery')
    await expect(title).toHaveClass(/font-display/)
    await expect(title).toHaveClass(/text-vault-text/)
  })

  test('should display hero banner with strategy title', async ({ page }) => {
    // Check hero section
    const heroTitle = page.locator('h2').first()
    await expect(heroTitle).toBeVisible()
    await expect(heroTitle).toContainText('Strategie Textbook')
  })

  test('should display Standard strategy button with emerald color', async ({ page }) => {
    const standardBtn = page.locator('button:has-text("Textbook Standard")')
    await expect(standardBtn).toBeVisible()
    await expect(standardBtn).toHaveClass(/bg-emerald-600/)
  })

  test('should display Patience strategy button with amber color', async ({ page }) => {
    const patienceBtn = page.locator('button:has-text("Textbook Patience")')
    await expect(patienceBtn).toBeVisible()
    await expect(patienceBtn).toHaveClass(/bg-amber-600/)
  })

  test('should display BSR ranges on strategy buttons', async ({ page }) => {
    // Standard button shows BSR 100K-250K
    const standardBtn = page.locator('button:has-text("Textbook Standard")')
    await expect(standardBtn).toContainText('BSR 100K-250K')

    // Patience button shows BSR 250K-400K
    const patienceBtn = page.locator('button:has-text("Textbook Patience")')
    await expect(patienceBtn).toContainText('BSR 250K-400K')
  })

  test('should display accordion collapsed by default', async ({ page }) => {
    // Accordion header should be visible
    const accordionHeader = page.locator('h3:has-text("Recherche Personnalisee")')
    await expect(accordionHeader).toBeVisible()

    // Search button should NOT be visible (accordion collapsed)
    const searchBtn = page.locator('button[type="submit"]:has-text("Rechercher")')
    await expect(searchBtn).not.toBeVisible()
  })

  test('should expand accordion on click', async ({ page }) => {
    // Click accordion header
    const accordionBtn = page.locator('button:has(h3:has-text("Recherche Personnalisee"))')
    await accordionBtn.click()
    await page.waitForTimeout(300)

    // Search button should now be visible
    const searchBtn = page.locator('button[type="submit"]:has-text("Rechercher")')
    await expect(searchBtn).toBeVisible()

    // Form inputs should be visible
    const bsrMinInput = page.locator('input').nth(1) // BSR Minimum
    await expect(bsrMinInput).toBeVisible()
  })

  test('should display divider with "OU" text', async ({ page }) => {
    // Target the specific divider in the main content area (not sidebar)
    const dividerContainer = page.locator('.flex.items-center.gap-4.my-8')
    await expect(dividerContainer).toBeVisible()

    // Check the "OU" text span inside the divider
    const dividerText = dividerContainer.locator('span')
    await expect(dividerText).toHaveText('OU')
    await expect(dividerText).toHaveClass(/bg-vault-card/)
    await expect(dividerText).toHaveClass(/border-vault-border/)
  })

  test('should toggle dark mode correctly', async ({ page }) => {
    // Find and click dark mode toggle
    const themeToggle = page.getByRole('button', { name: /Switch to dark mode/i })
    if (await themeToggle.isVisible()) {
      await themeToggle.click()
      await page.waitForTimeout(300)

      // Verify dark mode is active
      const html = page.locator('html')
      await expect(html).toHaveAttribute('data-theme', 'dark')
    }
  })

  test('should stack buttons vertically on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 })
    await page.waitForTimeout(300)

    // Both buttons should still be visible
    const standardBtn = page.locator('button:has-text("Textbook Standard")')
    const patienceBtn = page.locator('button:has-text("Textbook Patience")')

    await expect(standardBtn).toBeVisible()
    await expect(patienceBtn).toBeVisible()

    // Get button positions
    const standardBox = await standardBtn.boundingBox()
    const patienceBox = await patienceBtn.boundingBox()

    // On mobile, patience button should be below standard (stacked)
    // Check that Y position of patience > Y position of standard
    expect(patienceBox!.y).toBeGreaterThan(standardBox!.y)
  })

  test('should display buttons side by side on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.waitForTimeout(300)

    const standardBtn = page.locator('button:has-text("Textbook Standard")')
    const patienceBtn = page.locator('button:has-text("Textbook Patience")')

    // Get button positions
    const standardBox = await standardBtn.boundingBox()
    const patienceBox = await patienceBtn.boundingBox()

    // On desktop, buttons should be roughly on same Y position (side by side)
    // Allow 10px tolerance for alignment
    expect(Math.abs(patienceBox!.y - standardBox!.y)).toBeLessThan(10)
  })

  test('should display empty state with Vault styling', async ({ page }) => {
    // Empty state should be visible initially
    const emptyState = page.locator('text=Pret a decouvrir des niches rentables')
    await expect(emptyState).toBeVisible()

    // Check it has Vault card styling
    const emptyCard = page.locator('.bg-vault-card:has-text("Pret a decouvrir")')
    await expect(emptyCard).toBeVisible()
  })

  test('should not have horizontal overflow on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 })
    await page.waitForTimeout(300)

    // Check for horizontal overflow
    const hasOverflow = await page.evaluate(() => {
      const viewportWidth = window.innerWidth
      const elements = document.querySelectorAll('*')
      for (const el of elements) {
        const rect = el.getBoundingClientRect()
        if (rect.right > viewportWidth + 5) {
          return true
        }
      }
      return false
    })

    expect(hasOverflow).toBe(false)
  })

  test('should display Lucide icons in hero section', async ({ page }) => {
    // Check for SVG icons in hero (BookOpen, Zap, Clock)
    const heroSection = page.locator('.bg-gradient-to-r.from-vault-accent')
    const svgIcons = heroSection.locator('svg')

    // Should have at least 3 icons (BookOpen in title, Zap and Clock in buttons)
    const iconCount = await svgIcons.count()
    expect(iconCount).toBeGreaterThanOrEqual(3)
  })
})
