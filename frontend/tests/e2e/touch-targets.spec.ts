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
      expect(box?.height).toBeGreaterThanOrEqual(44)
    }
  })
})
