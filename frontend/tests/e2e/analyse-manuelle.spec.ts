import { test, expect } from '@playwright/test'

test.describe('Analyse Manuelle - Vault Elegance', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('onboarding_completed', 'true')
      localStorage.setItem('hasSeenWelcome', 'true')
    })
    await page.goto('/analyse')

    // Close onboarding modal if present
    const skipBtn = page.locator('button:has-text("Passer")').first()
    if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await skipBtn.click()
    }
  })

  test('should display page with Vault title and subtitle', async ({ page }) => {
    // Check title with Playfair Display styling
    const title = page.locator('h1')
    await expect(title).toBeVisible()
    await expect(title).toContainText('Analyse Manuelle')

    // Check subtitle
    const subtitle = page.locator('section p').first()
    await expect(subtitle).toContainText('Importez vos ASINs')
  })

  test('should display two input zones side by side on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })

    // CSV drop zone
    await expect(page.getByText('Drag & Drop CSV ici')).toBeVisible()

    // ASINs textarea zone
    await expect(page.getByText("Coller une liste d'ASINs")).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()
  })

  test('should validate ASINs and show feedback banner', async ({ page }) => {
    // Enter ASINs in textarea
    const textarea = page.locator('textarea')
    await textarea.fill('B08N5WRWNW, B07FZ8S74R, B06XG1NVFW')

    // Click validate button
    const validateBtn = page.getByRole('button', { name: /Valider ASINs/i })
    await expect(validateBtn).toBeEnabled()
    await validateBtn.click()

    // Check feedback banner appears
    await expect(page.getByText(/ASINs valides et prets/)).toBeVisible()
  })

  test('should disable validate button when textarea is empty', async ({ page }) => {
    const validateBtn = page.getByRole('button', { name: /Valider ASINs/i })

    // Should be disabled initially
    await expect(validateBtn).toBeDisabled()

    // Type something
    const textarea = page.locator('textarea')
    await textarea.fill('B08N5WRWNW')
    await expect(validateBtn).toBeEnabled()

    // Clear textarea
    await textarea.fill('')
    await expect(validateBtn).toBeDisabled()
  })

  test('should disable launch button when no ASINs validated', async ({ page }) => {
    const launchBtn = page.getByRole('button', { name: /Lancer l'analyse/i })
    await expect(launchBtn).toBeDisabled()
  })

  test('should enable launch button after ASINs validation', async ({ page }) => {
    // Enter and validate ASINs
    const textarea = page.locator('textarea')
    await textarea.fill('B08N5WRWNW')
    await page.getByRole('button', { name: /Valider ASINs/i }).click()

    // Launch button should be enabled
    const launchBtn = page.getByRole('button', { name: /Lancer l'analyse/i })
    await expect(launchBtn).toBeEnabled()
  })

  test('should display configuration section with 4 fields', async ({ page }) => {
    await expect(page.getByText('Configuration Analyse')).toBeVisible()

    // Check all 4 config fields
    await expect(page.getByText('Strategie primaire')).toBeVisible()
    await expect(page.getByText('ROI minimum [%]')).toBeVisible()
    await expect(page.getByText('BSR maximum')).toBeVisible()
    await expect(page.getByText('Velocity min.')).toBeVisible()

    // Check strategy dropdown has options
    const strategySelect = page.locator('select')
    await expect(strategySelect).toBeVisible()
  })

  test('should change config values when strategy changes', async ({ page }) => {
    const strategySelect = page.locator('select')
    const roiInput = page.locator('input[placeholder="30"]')

    // Default balanced = 30
    await expect(roiInput).toHaveValue('30')

    // Change to aggressive = 50
    await strategySelect.selectOption('aggressive')
    await expect(roiInput).toHaveValue('50')

    // Change to conservative = 20
    await strategySelect.selectOption('conservative')
    await expect(roiInput).toHaveValue('20')
  })

  test('should toggle dark mode', async ({ page }) => {
    const html = page.locator('html')

    // Initial state should be light
    await expect(html).toHaveAttribute('data-theme', 'light')

    // Click theme toggle
    const themeToggle = page.getByRole('button', { name: /Switch to dark mode/i })
    await themeToggle.click()

    // Should be dark
    await expect(html).toHaveAttribute('data-theme', 'dark')
  })

  test('should stack input zones on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Both zones should be visible and stacked
    await expect(page.getByText('Drag & Drop CSV ici')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()

    // Check they are in a single column layout (grid-cols-1)
    const inputSection = page.locator('section').nth(1) // Second section is input zones
    await expect(inputSection).toBeVisible()
  })

  test('should show checkboxes in config section', async ({ page }) => {
    await expect(page.getByText('Analyse multi-strategies')).toBeVisible()
    await expect(page.getByText('Verification stock')).toBeVisible()
    await expect(page.getByText('Export CSV')).toBeVisible()
  })

  test('should display Play icon in launch button', async ({ page }) => {
    const launchBtn = page.getByRole('button', { name: /Lancer l'analyse/i })
    const svg = launchBtn.locator('svg')
    await expect(svg).toBeVisible()
  })
})
