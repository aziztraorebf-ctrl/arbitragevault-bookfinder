import { test, expect } from '@playwright/test'

test.describe('Vault Elegance Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start fresh
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.reload()
  })

  test('should display dashboard with greeting', async ({ page }) => {
    await page.goto('/dashboard')

    // Check greeting is present (Bonjour/Bon apres-midi/Bonsoir)
    const greeting = page.locator('h1')
    await expect(greeting).toBeVisible()
    await expect(greeting).toContainText(/Bonjour|Bon apres-midi|Bonsoir/)
  })

  test('should display 4 KPI cards', async ({ page }) => {
    await page.goto('/dashboard')

    // Check all 4 KPI values are present
    await expect(page.getByText('$45,280.15')).toBeVisible()
    await expect(page.getByText('2,450')).toBeVisible()
    await expect(page.getByText('28.4%')).toBeVisible()
    await expect(page.getByText('15')).toBeVisible()
  })

  test('should display 3 action cards', async ({ page }) => {
    await page.goto('/dashboard')

    await expect(page.getByText('New Arbitrage Opportunity')).toBeVisible()
    await expect(page.getByText('Market Alert')).toBeVisible()
    await expect(page.getByText('Performance Report')).toBeVisible()
  })

  test('should display activity feed', async ({ page }) => {
    await page.goto('/dashboard')

    await expect(page.getByText('Activity Feed')).toBeVisible()
    // Check at least one activity event
    await expect(page.getByText(/Deal Closed|Price Alert|Inventory Update/)).toBeVisible()
  })

  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/dashboard')

    // Initial state should be light mode
    const html = page.locator('html')
    await expect(html).toHaveAttribute('data-theme', 'light')

    // Click theme toggle button
    const themeToggle = page.getByRole('button', { name: /Switch to dark mode/i })
    await themeToggle.click()

    // Should be dark mode now
    await expect(html).toHaveAttribute('data-theme', 'dark')

    // Button label should change
    await expect(page.getByRole('button', { name: /Switch to light mode/i })).toBeVisible()
  })

  test('should persist dark mode preference', async ({ page }) => {
    await page.goto('/dashboard')

    // Switch to dark mode
    const themeToggle = page.getByRole('button', { name: /Switch to dark mode/i })
    await themeToggle.click()

    // Reload the page
    await page.reload()

    // Should still be dark mode
    const html = page.locator('html')
    await expect(html).toHaveAttribute('data-theme', 'dark')
  })

  test('should navigate from action card', async ({ page }) => {
    await page.goto('/dashboard')

    // Click "Analyze Deal" button
    await page.getByText('Analyze Deal').click()

    // Should navigate to /analyse
    await expect(page).toHaveURL(/.*\/analyse/)
  })

  test('should show sidebar on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto('/dashboard')

    // Sidebar should be visible
    const sidebar = page.locator('aside')
    await expect(sidebar).toBeVisible()
  })

  test('should hide sidebar on mobile and show hamburger', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')

    // Hamburger menu should be visible
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await expect(hamburger).toBeVisible()

    // Click hamburger to open sidebar
    await hamburger.click()

    // Sidebar should slide in
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveClass(/translate-x-0/)
  })

  test('should expand sidebar on hover (desktop)', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto('/dashboard')

    const sidebar = page.locator('aside')

    // Initial width should be collapsed (72px)
    await expect(sidebar).toHaveClass(/lg:w-\[72px\]/)

    // Hover over sidebar
    await sidebar.hover()

    // Should expand to 240px
    await expect(sidebar).toHaveClass(/lg:w-64/)
  })
})
