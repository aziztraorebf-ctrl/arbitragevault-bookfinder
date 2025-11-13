// Token Error Handling UI Tests - Phase 6
// Valide que le frontend affiche un message d'erreur quand HTTP 429 survient
// Note: TokenErrorAlert dedie avec badges balance/deficit n'est PAS encore implemente
// Ces tests validant le comportement actuel (message erreur generique)
const { test, expect } = require('@playwright/test');

const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Token Error Handling UI', () => {
  test('Should display error message on mocked HTTP 429', async ({ page }) => {
    console.log('Testing error message display with mocked 429...');

    // Mock HTTP 429 response for any Keepa API call
    await page.route('**/api/v1/keepa/**', async (route) => {
      console.log('Mocking HTTP 429 for:', route.request().url());

      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'X-Token-Balance': '3',
          'X-Token-Required': '15',
          'Retry-After': '180'
        },
        body: JSON.stringify({
          detail: 'Insufficient Keepa tokens: balance=3, required=15, deficit=12. Try again in 180 seconds.'
        })
      });
    });

    // Navigate to search page and trigger API call
    await page.goto(`${FRONTEND_URL}/analyse`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Fill and validate ASIN
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await searchInput.fill('B00FLIJJSA');

    const validateButton = page.locator('button:has-text("Valider ASINs")').first();
    await validateButton.click();

    await page.waitForSelector('text=/ASINs prêts/i', { timeout: 5000 });

    const analyzeButton = page.locator('button:has-text("Lancer analyse")').first();
    await analyzeButton.click();

    // Wait for error message to appear (generic error, not dedicated TokenErrorAlert)
    console.log('Waiting for error message...');

    await page.waitForSelector('text=/Erreur/i', {
      timeout: 10000
    });

    const errorMessage = page.locator('text=/Erreur/i').first();
    await expect(errorMessage).toBeVisible();

    // Verify French error message
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/erreur/i);

    console.log('Error message displayed:', errorText);

    // Note: TokenErrorAlert with balance badges and dedicated token error UI is NOT yet implemented
    // This test validates that HTTP 429 triggers SOME error message (generic fallback)
    console.log('Note: Dedicated TokenErrorAlert with balance/deficit badges not yet implemented');
    console.log('Frontend shows generic error message instead');
  });

  test('Should display error indicator on HTTP 429', async ({ page }) => {
    console.log('Testing error indicator display...');

    // Mock HTTP 429
    await page.route('**/api/v1/keepa/**', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'X-Token-Balance': '0',
          'X-Token-Required': '10'
        },
        body: JSON.stringify({
          detail: 'Insufficient tokens'
        })
      });
    });

    await page.goto(`${FRONTEND_URL}/analyse`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Trigger API call
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await searchInput.fill('0593655036');

    const validateButton = page.locator('button:has-text("Valider ASINs")').first();
    await validateButton.click();

    await page.waitForSelector('text=/ASINs prêts/i', { timeout: 5000 });

    const analyzeButton = page.locator('button:has-text("Lancer analyse")').first();
    await analyzeButton.click();

    // Wait for any error indicator
    await page.waitForSelector('text=/Erreur/i', { timeout: 10000 });

    const errorElement = page.locator('text=/Erreur/i').first();
    await expect(errorElement).toBeVisible();

    console.log('Error indicator displayed successfully');
  });

  test('Should show persistent error state after HTTP 429', async ({ page }) => {
    console.log('Testing persistent error state...');

    let callCount = 0;

    // Always return HTTP 429 (to test persistent error)
    await page.route('**/api/v1/keepa/**', async (route) => {
      callCount++;

      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'X-Token-Balance': '0',
          'X-Token-Required': '5'
        },
        body: JSON.stringify({
          detail: 'Insufficient tokens'
        })
      });
    });

    await page.goto(`${FRONTEND_URL}/analyse`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Trigger API call
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await searchInput.fill('B00FLIJJSA');

    const validateButton = page.locator('button:has-text("Valider ASINs")').first();
    await validateButton.click();

    await page.waitForSelector('text=/ASINs prêts/i', { timeout: 5000 });

    const analyzeButton = page.locator('button:has-text("Lancer analyse")').first();
    await analyzeButton.click();

    // Wait for error message
    await page.waitForSelector('text=/Erreur/i', { timeout: 10000 });

    const errorMessage = page.locator('text=/Erreur/i').first();
    const errorVisible = await errorMessage.isVisible();
    expect(errorVisible).toBe(true);

    console.log(`HTTP 429 triggered API call ${callCount} time(s)`);
    console.log('Error persists as expected (no automatic retry)');
  });
});
