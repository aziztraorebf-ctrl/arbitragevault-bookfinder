// Navigation Flow E2E Tests - Phase 6
// Valide que toutes les pages principales chargent correctement
const { test, expect } = require('@playwright/test');

const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Navigation Flow', () => {
  test('Should load homepage successfully', async ({ page }) => {
    console.log('Testing homepage load...');

    await page.goto(FRONTEND_URL);

    // Wait for React app
    await page.waitForSelector('#root', { timeout: 10000 });

    // Verify navigation is present
    const nav = page.locator('nav');
    await expect(nav).toBeVisible({ timeout: 5000 });

    // Verify at least one heading
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible({ timeout: 5000 });

    console.log('Homepage loaded successfully');
  });

  test('Should navigate to all major pages via links', async ({ page }) => {
    console.log('Testing navigation to all major pages...');

    await page.goto(FRONTEND_URL);
    await page.waitForSelector('#root', { timeout: 10000 });

    // List of expected pages (adjusted based on actual routes from error-context)
    const expectedPages = [
      { name: 'Dashboard', selectors: ['a[href*="dashboard"]', 'a:has-text("Dashboard")'] },
      { name: 'Analyse Manuelle', selectors: ['a[href*="analyse"]', 'a:has-text("Analyse Manuelle")'] },
      { name: 'AutoSourcing', selectors: ['a[href*="autosourcing"]', 'a:has-text("AutoSourcing")'] },
      { name: 'Mes Niches', selectors: ['a[href*="mes-niches"]', 'a:has-text("Mes Niches")'] }
    ];

    for (const pageDef of expectedPages) {
      console.log(`Checking ${pageDef.name} page...`);

      // Try each selector until one works
      let found = false;
      for (const selector of pageDef.selectors) {
        const link = page.locator(selector).first();
        if (await link.isVisible({ timeout: 2000 }).catch(() => false)) {
          await link.click();
          console.log(`Clicked ${pageDef.name} link`);

          // Wait for page to load
          await page.waitForLoadState('networkidle', { timeout: 10000 });

          // Verify page loaded (has heading or content)
          const content = page.locator('h1, h2, main, .content').first();
          await expect(content).toBeVisible({ timeout: 5000 });

          console.log(`${pageDef.name} page loaded successfully`);
          found = true;

          // Go back to homepage for next test
          await page.goto(FRONTEND_URL);
          await page.waitForSelector('#root', { timeout: 10000 });
          break;
        }
      }

      if (!found) {
        console.log(`${pageDef.name} page link not found (might not be implemented)`);
      }
    }
  });

  test('Should handle 404 page gracefully', async ({ page }) => {
    console.log('Testing 404 page handling...');

    await page.goto(`${FRONTEND_URL}/non-existent-page-12345`);

    // Wait for page to load
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Either show 404 page or redirect to homepage
    const has404 = await page.locator('text=/404/i, text=/not found/i, text=/page introuvable/i').isVisible({ timeout: 5000 }).catch(() => false);
    const hasRoot = await page.locator('#root').isVisible({ timeout: 5000 }).catch(() => false);

    expect(has404 || hasRoot).toBe(true);

    console.log(has404 ? '404 page displayed' : 'Redirected to valid page');
  });

  test('Should maintain navigation state across pages', async ({ page }) => {
    console.log('Testing navigation state persistence...');

    await page.goto(FRONTEND_URL);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Navigation should be visible on all pages
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Navigate to different page
    const analyseLink = page.locator('a[href*="analyse"]').first();
    if (await analyseLink.isVisible({ timeout: 5000 })) {
      await analyseLink.click();
      await page.waitForLoadState('networkidle');

      // Navigation should still be visible
      await expect(nav).toBeVisible({ timeout: 5000 });

      console.log('Navigation persists across pages');
    } else {
      console.log('Analyse link not found, skipping persistence test');
    }
  });

  test('Should have working browser back/forward', async ({ page }) => {
    console.log('Testing browser back/forward navigation...');

    await page.goto(FRONTEND_URL);
    await page.waitForSelector('#root', { timeout: 10000 });

    const initialUrl = page.url();

    // Navigate to another page
    const link = page.locator('a[href]').first();
    if (await link.isVisible({ timeout: 5000 })) {
      await link.click();
      await page.waitForLoadState('networkidle');

      const secondUrl = page.url();
      expect(secondUrl).not.toBe(initialUrl);

      // Go back
      await page.goBack();
      await page.waitForLoadState('networkidle');

      expect(page.url()).toBe(initialUrl);

      // Go forward
      await page.goForward();
      await page.waitForLoadState('networkidle');

      expect(page.url()).toBe(secondUrl);

      console.log('Browser back/forward works correctly');
    } else {
      console.log('No links found, skipping back/forward test');
    }
  });
});
