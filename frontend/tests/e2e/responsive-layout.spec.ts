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

  test('mobile: sidebar off-screen by default, hamburger visible', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const sidebar = page.locator('aside')
    const hamburger = page.getByRole('button', { name: /menu/i })
    // Sidebar is translated off-screen (not truly hidden in DOM)
    await expect(sidebar).toHaveAttribute('data-state', 'closed')
    await expect(hamburger).toBeVisible()
  })

  test('mobile: hamburger opens sidebar overlay', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveAttribute('data-state', 'open')
    await expect(sidebar).toBeVisible()
    const backdrop = page.locator('[data-testid="mobile-backdrop"]')
    await expect(backdrop).toBeVisible()
  })

  test('mobile: clicking nav item closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()
    // Wait for sidebar to open
    await expect(page.locator('aside')).toHaveAttribute('data-state', 'open')
    await page.getByRole('link', { name: /Niche Discovery/i }).click()
    const sidebar = page.locator('aside')
    // After navigation, sidebar should close
    await expect(sidebar).toHaveAttribute('data-state', 'closed')
  })

  test('mobile: clicking backdrop closes sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()
    // Wait for sidebar to open
    await expect(page.locator('aside')).toHaveAttribute('data-state', 'open')
    const backdrop = page.locator('[data-testid="mobile-backdrop"]')
    await expect(backdrop).toBeVisible()
    // Click on backdrop - need to use force since sidebar may intercept
    await backdrop.click({ force: true })
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveAttribute('data-state', 'closed')
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
    const hamburger = page.getByRole('button', { name: /menu/i })
    await expect(hamburger).toBeVisible()

    // Main content should not have horizontal scroll at page level
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth)
    const clientWidth = await page.evaluate(() => document.body.clientWidth)
    // Allow small tolerance for rounding
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 5)
  })

  test('extra small mobile (320px): sidebar works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 })

    const hamburger = page.getByRole('button', { name: /menu/i })
    await hamburger.click()

    // Sidebar should open
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveAttribute('data-state', 'open')

    // Sidebar width (256px / w-64) should fit within screen with some overflow
    // This is expected behavior - sidebar overlays content
    const sidebarBox = await sidebar.boundingBox()
    expect(sidebarBox?.x).toBeGreaterThanOrEqual(0)

    // Navigation items should be readable
    const dashboardLink = page.getByRole('link', { name: /Dashboard/i })
    await expect(dashboardLink).toBeVisible()
  })
})
