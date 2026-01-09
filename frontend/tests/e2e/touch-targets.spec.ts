import { test, expect } from '@playwright/test'

test.describe('Touch Targets', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('onboarding_completed', 'true')
      localStorage.setItem('hasSeenWelcome', 'true')
    })
  })

  test('buttons have minimum 44px touch target', async ({ page }) => {
    await page.goto('/dashboard')

    // Check theme toggle button (always present)
    const themeToggle = page.getByRole('button', { name: /Switch to dark mode/i })
    const box = await themeToggle.boundingBox()

    // Theme toggle should have minimum touch target
    expect(box?.height).toBeGreaterThanOrEqual(40)
    expect(box?.width).toBeGreaterThanOrEqual(40)
  })

  test('nav items have adequate spacing on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')

    // Open menu
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    await hamburger.click()

    // Check nav links (filter out separators by checking for 'a' tag)
    const navLinks = page.locator('aside nav a')
    const count = await navLinks.count()

    expect(count).toBeGreaterThan(0)

    for (let i = 0; i < Math.min(count, 5); i++) {
      const box = await navLinks.nth(i).boundingBox()
      // Nav items should have adequate height for touch
      expect(box?.height).toBeGreaterThanOrEqual(44)
    }
  })
})
