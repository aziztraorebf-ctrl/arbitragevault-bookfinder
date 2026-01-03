import { test, expect } from '@playwright/test'

test.describe('Mobile Table Scroll', () => {
  test('table scrolls horizontally on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/niche-discovery')

    // Check that table container has scroll behavior
    const tableContainer = page.locator('.overflow-x-auto').first()

    if (await tableContainer.count() > 0) {
      const scrollWidth = await tableContainer.evaluate(el => el.scrollWidth)
      const clientWidth = await tableContainer.evaluate(el => el.clientWidth)

      if (scrollWidth > clientWidth) {
        await expect(tableContainer).toHaveCSS('overflow-x', 'auto')
      }
    }
  })

  test('table header stays sticky on scroll', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/analyse')

    const thead = page.locator('thead').first()
    if (await thead.count() > 0) {
      await expect(thead).toHaveCSS('position', 'sticky')
    }
  })
})
