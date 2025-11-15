const { test, expect } = require('@playwright/test');

const FRONTEND_URL = process.env.FRONTEND_URL || 'https://arbitragevault.netlify.app';
const BACKEND_URL = process.env.BACKEND_URL || 'https://arbitragevault-backend-v2.onrender.com';

test.describe('AutoSourcing Safeguards', () => {
  test('Should display cost estimate before job submission', async ({ page }) => {
    // Navigate to AutoSourcing page
    await page.goto(`${FRONTEND_URL}/autosourcing`);

    // Wait for page load
    await page.waitForSelector('h1:has-text("AutoSourcing")', { timeout: 10000 });

    // Click on create job button to open modal
    const createButton = page.locator('button:has-text("Nouvelle Recherche"), button:has-text("Nouveau Job"), button:has-text("Create"), button:has-text("New")').first();
    await createButton.waitFor({ state: 'visible', timeout: 10000 });
    await createButton.click();

    // Wait for modal to open
    await page.waitForSelector('h2:has-text("Nouvelle Recherche Personnalisée")', { timeout: 10000 });

    // Fill job configuration - using exact placeholder from production UI
    await page.fill('input[placeholder*="Livres Techniques"]', 'Test Safeguards');

    // Set max results to a high value
    const maxResultsInput = page.locator('input[name="max_results"], input[placeholder*="max"], input[type="number"]').first();
    if (await maxResultsInput.isVisible()) {
      await maxResultsInput.fill('50');
    }

    // Look for estimate button - exact text from UI
    const estimateButton = page.locator('button:has-text("Estimer le Cout")').first();
    await estimateButton.waitFor({ state: 'visible', timeout: 10000 });
    await estimateButton.click();

    // Wait for cost estimate panel to appear
    await page.waitForSelector('text=/Estimation du Cout/i', { timeout: 10000 });

    // Verify cost estimate details are displayed
    await expect(page.locator('text=/Tokens estimes:/i')).toBeVisible();
    await expect(page.locator('text=/Balance actuelle:/i')).toBeVisible();
    await expect(page.locator('text=/Limite max:/i')).toBeVisible();

    console.log('Cost estimation feature validated successfully');
  });

  test('Should reject job if cost exceeds limit', async ({ page }) => {
    // Mock API to return JOB_TOO_EXPENSIVE error
    await page.route('**/api/v1/autosourcing/run_custom', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: "JOB_TOO_EXPENSIVE",
            estimated_tokens: 500,
            max_allowed: 200,
            suggestion: "Reduce max_results or narrow filters"
          }
        })
      });
    });

    // Navigate to AutoSourcing page
    await page.goto(`${FRONTEND_URL}/autosourcing`);

    // Wait for page load
    await page.waitForSelector('h1:has-text("AutoSourcing")', { timeout: 10000 });

    // Click on create job button to open modal
    const createButton = page.locator('button:has-text("Nouvelle Recherche"), button:has-text("Nouveau Job"), button:has-text("Create"), button:has-text("New")').first();
    await createButton.waitFor({ state: 'visible', timeout: 10000 });
    await createButton.click();

    // Wait for modal to open
    await page.waitForSelector('h2:has-text("Nouvelle Recherche Personnalisée")', { timeout: 10000 });

    // Fill minimal form - using exact placeholder from production UI
    await page.fill('input[placeholder*="Livres Techniques"]', 'Expensive Job');

    // Submit form - using exact text from UI
    const submitButton = page.locator('button:has-text("Lancer Recherche")').first();
    await submitButton.click();

    // Verify error message appears in red panel
    await page.waitForSelector('div.bg-red-50:has-text("Job trop couteux")', { timeout: 10000 });

    // Verify error details contain token information
    await expect(page.locator('text=/500.*tokens/i')).toBeVisible();
    await expect(page.locator('text=/limite.*200/i')).toBeVisible();

    console.log('JOB_TOO_EXPENSIVE error handling validated');
  });

  test('Should enforce timeout on long-running jobs', async ({ page }) => {
    // Mock API to simulate timeout
    await page.route('**/api/v1/autosourcing/run_custom', async route => {
      // Delay response to simulate timeout
      await new Promise(resolve => setTimeout(resolve, 3000));
      route.fulfill({
        status: 408,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: "Job timeout - reduce search scope"
        })
      });
    });

    // Navigate to AutoSourcing page
    await page.goto(`${FRONTEND_URL}/autosourcing`);

    // Wait for page load
    await page.waitForSelector('h1:has-text("AutoSourcing")', { timeout: 10000 });

    // Click on create job button to open modal
    const createButton = page.locator('button:has-text("Nouvelle Recherche"), button:has-text("Nouveau Job"), button:has-text("Create"), button:has-text("New")').first();
    await createButton.waitFor({ state: 'visible', timeout: 10000 });
    await createButton.click();

    // Wait for modal to open
    await page.waitForSelector('h2:has-text("Nouvelle Recherche Personnalisée")', { timeout: 10000 });

    // Fill minimal form - using exact placeholder from production UI
    await page.fill('input[placeholder*="Livres Techniques"]', 'Timeout Test');

    // Submit form - using exact text from UI
    const submitButton = page.locator('button:has-text("Lancer Recherche")').first();
    await submitButton.click();

    // Verify timeout error appears in red panel
    await page.waitForSelector('div.bg-red-50:has-text("Timeout")', { timeout: 15000 });

    // Verify error message contains timeout information
    await expect(page.locator('text=/Timeout du job/i')).toBeVisible();
    await expect(page.locator('text=/reduire.*portee/i')).toBeVisible();

    console.log('Timeout safeguard validated - job rejected after timeout');
  });
});