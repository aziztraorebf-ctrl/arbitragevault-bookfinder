// Manual Search Flow E2E Tests - Phase 5
// Valide le workflow complet de recherche manuelle avec vraies donnees Keepa
const { test, expect } = require('@playwright/test');
const { getRandomASIN } = require('../test-utils/random-data');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

// Use seed-based randomization for reproducibility
const TEST_SEED = process.env.TEST_SEED || 'manual-search-flow';
const TEST_ASINS = {
  learning_python: getRandomASIN(`${TEST_SEED}-book`, 'books_low_bsr'),
  kindle_oasis: getRandomASIN(`${TEST_SEED}-electronics`, 'electronics')
};

test.describe('Manual Search Flow', () => {
  test('Should navigate to search page and find search form', async ({ page }) => {
    console.log('Testing manual search page navigation...');

    await page.goto(FRONTEND_URL);

    // Wait for React app to mount
    await page.waitForSelector('#root', { timeout: 10000 });

    // Find link to manual search (route is /analyse)
    const searchLink = page.locator('a[href*="analyse"]').first();

    if (await searchLink.isVisible({ timeout: 5000 })) {
      await searchLink.click();
      console.log('Navigated to search page via link');
    } else {
      // Direct navigation if link not found
      await page.goto(`${FRONTEND_URL}/analyse`);
      console.log('Navigated to search page directly');
    }

    // Verify search form is present (textarea for ASINs)
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    console.log('Search form found and visible');
  });

  test('Should search single ASIN and display results', async ({ page }) => {
    console.log('Testing single ASIN search with real Keepa data...');

    await page.goto(`${FRONTEND_URL}/analyse`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Find and fill textarea with ASIN
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await searchInput.fill(TEST_ASINS.learning_python);

    console.log(`Searching for ASIN: ${TEST_ASINS.learning_python}`);

    // Click "Valider ASINs" button
    const validateButton = page.locator('button:has-text("Valider ASINs")').first();
    await validateButton.click();

    // Wait for validation message
    await page.waitForSelector('text=/ASINs prêts pour l\'analyse/i', { timeout: 5000 });

    // Click "Lancer analyse" button
    const analyzeButton = page.locator('button:has-text("Lancer analyse")').first();
    await analyzeButton.click();

    // Wait for results to load (might take 5-10s for Keepa API)
    console.log('Waiting for Keepa API results...');

    // Wait for either results table or error (longer timeout for Keepa API)
    await page.waitForTimeout(2000); // Give it time to start loading

    // Check if HTTP 429 error occurred (TokenErrorAlert)
    const tokenError = page.locator('[role="alert"]').filter({ hasText: /token/i });
    if (await tokenError.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('HTTP 429 detected - tokens insufficient, test skipped gracefully');

      // Verify TokenErrorAlert is displayed
      expect(await tokenError.isVisible()).toBe(true);

      console.log('TokenErrorAlert verified for HTTP 429');
      return; // Skip rest of test
    }

    // Wait for results table to appear or success message
    const resultsAppeared = await Promise.race([
      page.waitForSelector('table', { timeout: 45000 }).then(() => 'table'),
      page.locator('text=/Analyse terminée/i').first().waitFor({ timeout: 45000 }).then(() => 'success')
    ]);

    console.log(`Results loaded (${resultsAppeared}), verifying display...`);

    // Verify results table is displayed
    const resultsTable = page.locator('table').first();
    await expect(resultsTable).toBeVisible({ timeout: 5000 });

    // Verify table has data rows (tbody with tr elements)
    const tableRows = page.locator('table tbody tr');
    const rowCount = await tableRows.count();

    expect(rowCount).toBeGreaterThan(0);

    console.log(`Results displayed successfully: ${rowCount} rows in table`);
  });

  test('Should handle invalid ASIN gracefully', async ({ page }) => {
    console.log('Testing invalid ASIN error handling...');

    await page.goto(`${FRONTEND_URL}/analyse`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Fill textarea with invalid ASIN (too short)
    const searchInput = page.locator('textarea[placeholder*="ASIN"], textarea').first();
    await searchInput.fill('INVALID');

    // Click validate button
    const validateButton = page.locator('button:has-text("Valider ASINs")').first();
    await validateButton.click();

    // Wait for error message (fixed toast in bottom-right)
    await page.waitForSelector('.fixed.bottom-4.right-4, [role="alert"]', { timeout: 10000 });

    const errorMessage = page.locator('.fixed.bottom-4.right-4, [role="alert"]').first();
    await expect(errorMessage).toBeVisible();

    // Verify error message contains expected text about ASIN format
    const errorText = await errorMessage.textContent();
    expect(errorText).toMatch(/ASIN|format|valide/i);

    console.log('Invalid ASIN error displayed correctly:', errorText);
  });
});
