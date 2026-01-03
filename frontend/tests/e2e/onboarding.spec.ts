import { test, expect } from '@playwright/test'

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test by navigating first
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.reload()
  })

  test('shows wizard on first visit', async ({ page }) => {
    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeVisible()
  })

  test('does not show wizard after completion', async ({ page }) => {
    // Complete the wizard
    await page.getByRole('button', { name: /Suivant/i }).click()
    await page.getByRole('button', { name: /Suivant/i }).click()
    await page.getByRole('button', { name: /Commencer/i }).click()

    // Verify wizard is closed
    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeHidden()

    // Verify it stays hidden after reload
    await page.reload()
    await expect(wizard).toBeHidden()
  })

  test('skip button closes wizard', async ({ page }) => {
    // Use getByText for the text button (not the X icon)
    await page.getByText('Passer', { exact: true }).click()
    const wizard = page.locator('text=Bienvenue sur ArbitrageVault')
    await expect(wizard).toBeHidden()
  })
})
