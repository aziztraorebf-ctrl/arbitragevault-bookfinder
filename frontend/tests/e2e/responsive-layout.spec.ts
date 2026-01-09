import { test, expect } from '@playwright/test'

test.describe('Responsive Layout', () => {
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

  test('desktop: sidebar visible, hamburger hidden', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    const sidebar = page.locator('aside')
    const hamburger = page.getByRole('button', { name: /menu/i })
    await expect(sidebar).toBeVisible()
    await expect(hamburger).toBeHidden()
  })

  test('mobile: sidebar off-screen by default, hamburger visible', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const sidebar = page.locator('aside')
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    // Sidebar is translated off-screen (has -translate-x-full class)
    await expect(sidebar).toHaveClass(/-translate-x-full/)
    await expect(hamburger).toBeVisible()
  })

  test('mobile: hamburger opens sidebar overlay', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await hamburger.click()
    const sidebar = page.locator('aside')
    // After clicking, sidebar should slide in (translate-x-0)
    await expect(sidebar).toHaveClass(/translate-x-0/)
    await expect(sidebar).toBeVisible()
    // Backdrop should be visible (opacity-100)
    const backdrop = page.locator('[aria-hidden="true"].fixed.inset-0')
    await expect(backdrop).toHaveClass(/opacity-100/)
  })

  test('mobile: clicking nav item closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await hamburger.click()
    // Wait for sidebar to open
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveClass(/translate-x-0/)
    // Click on a nav item
    await page.getByRole('link', { name: /Discovery/i }).click()
    // After navigation, sidebar should close (wait for animation)
    await page.waitForTimeout(500)
    await expect(sidebar).toHaveClass(/-translate-x-full/)
  })

  test('mobile: clicking backdrop closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await hamburger.click()
    // Wait for sidebar to open
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveClass(/translate-x-0/)
    // Click on backdrop (background overlay)
    const backdrop = page.locator('.bg-black\\/50.fixed.inset-0')
    await backdrop.click({ position: { x: 300, y: 300 } })
    // Sidebar should close (wait for animation)
    await page.waitForTimeout(500)
    await expect(sidebar).toHaveClass(/-translate-x-full/)
  })

  test('extra small mobile (320px): layout does not overflow', async ({ page }) => {
    // Test for very small screens (iPhone SE, older devices)
    await page.setViewportSize({ width: 320, height: 568 })

    // Check that main content is visible and not overflowing
    const body = page.locator('body')
    await expect(body).toBeVisible()

    // Header should be fully visible
    const header = page.locator('header')
    await expect(header).toBeVisible()
    const headerBox = await header.boundingBox()
    expect(headerBox?.width).toBeLessThanOrEqual(320)

    // Hamburger should be visible and clickable
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await expect(hamburger).toBeVisible()

    // Main content should not have horizontal scroll at page level
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth)
    const clientWidth = await page.evaluate(() => document.body.clientWidth)
    // Allow small tolerance for rounding
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 5)
  })

  test('extra small mobile (320px): sidebar works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 })

    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await hamburger.click()

    // Sidebar should open
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveClass(/translate-x-0/)

    // Sidebar should be visible and usable
    await expect(sidebar).toBeVisible()

    // Navigation items should be readable
    const dashboardLink = page.getByRole('link', { name: /Dashboard/i })
    await expect(dashboardLink).toBeVisible()
  })
})
