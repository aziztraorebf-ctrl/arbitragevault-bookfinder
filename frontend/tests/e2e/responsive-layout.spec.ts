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
})
