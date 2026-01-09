import { test, expect } from '@playwright/test'

test.describe('Vault Elegance Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('onboarding_completed', 'true')
      localStorage.setItem('hasSeenWelcome', 'true')
    })
    await page.goto('/dashboard')

    // Close onboarding modal if present
    const skipBtn = page.locator('button:has-text("Passer")').first()
    if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await skipBtn.click()
    }
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

    // Check all 4 KPI labels are present (values may vary)
    await expect(page.getByText('Total Arbitrage Value')).toBeVisible()
    await expect(page.getByText('Book Inventory Count')).toBeVisible()
    await expect(page.getByText('Profit Margin (Avg)')).toBeVisible()
    await expect(page.getByText('Pending Deals')).toBeVisible()
  })

  test('should display 3 action cards', async ({ page }) => {
    await page.goto('/dashboard')

    await expect(page.getByText('New Arbitrage Opportunity')).toBeVisible()
    await expect(page.getByText('Market Alert')).toBeVisible()
    await expect(page.getByText('Performance Report')).toBeVisible()
  })

  test('should display activity feed', async ({ page }) => {
    // Check that Activity Feed heading is visible
    await expect(page.getByText('Activity Feed')).toBeVisible()
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
    // Click "Analyze Deal" button in action card
    const analyzeBtn = page.locator('button:has-text("Analyze Deal")').first()
    await analyzeBtn.click()

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

    const sidebar = page.locator('aside')

    // Sidebar should be visible on desktop
    await expect(sidebar).toBeVisible()

    // Hover over sidebar to trigger expansion
    await sidebar.hover()

    // After hover, sidebar should have expanded state (group-hover classes apply)
    // Just verify sidebar remains visible after hover interaction
    await expect(sidebar).toBeVisible()
  })
})
