/**
 * E2E Test: Mes Recherches Page
 * Phase 11 - Centralized Search Results
 */

const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  console.log('Starting E2E test for /recherches page...');

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  try {
    // Test 1: Navigate to /recherches page
    console.log('\n--- Test 1: Page loads with correct title ---');
    await page.goto(`${TARGET_URL}/recherches`);
    await page.waitForLoadState('networkidle');

    // Check page title
    const pageTitle = await page.locator('h1').first().textContent();
    console.log('Page title:', pageTitle);

    if (pageTitle && pageTitle.includes('Mes Recherches')) {
      console.log('PASS: Page title is correct');
    } else {
      console.log('FAIL: Page title does not match expected "Mes Recherches"');
    }

    // Take screenshot of initial state
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-recherches-initial.png',
      fullPage: true
    });
    console.log('Screenshot saved: test-recherches-initial.png');

    // Test 2: Check stats cards visibility
    console.log('\n--- Test 2: Stats cards visibility ---');

    // Wait for stats to potentially load (may fail if API not responding)
    await page.waitForTimeout(2000);

    // Check for stats section (Total, Niche Discovery, AutoSourcing, Analyse Manuelle)
    const statsSection = await page.locator('.grid.grid-cols-4').first();
    const statsVisible = await statsSection.isVisible().catch(() => false);

    if (statsVisible) {
      console.log('PASS: Stats section is visible');

      // Check individual stat labels
      const statLabels = ['Total', 'Niche Discovery', 'AutoSourcing', 'Analyse Manuelle'];
      for (const label of statLabels) {
        const statElement = await page.locator(`text=${label}`).first();
        const isVisible = await statElement.isVisible().catch(() => false);
        console.log(`  - ${label}: ${isVisible ? 'VISIBLE' : 'NOT FOUND'}`);
      }
    } else {
      console.log('INFO: Stats section not visible (may require auth or data)');
    }

    // Test 3: Filter buttons
    console.log('\n--- Test 3: Filter buttons ---');

    const filterLabels = ['Toutes', 'Niche Discovery', 'AutoSourcing', 'Analyse Manuelle'];

    for (const filterLabel of filterLabels) {
      const filterButton = await page.locator(`button:has-text("${filterLabel}")`).first();
      const isVisible = await filterButton.isVisible().catch(() => false);

      if (isVisible) {
        console.log(`PASS: Filter button "${filterLabel}" is visible`);

        // Click the filter button
        await filterButton.click();
        await page.waitForTimeout(500);
        console.log(`  - Clicked "${filterLabel}" filter`);
      } else {
        console.log(`INFO: Filter button "${filterLabel}" not found`);
      }
    }

    // Take screenshot after clicking filters
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-recherches-after-filters.png',
      fullPage: true
    });
    console.log('Screenshot saved: test-recherches-after-filters.png');

    // Test 4: Empty state
    console.log('\n--- Test 4: Empty state ---');

    // Check for empty state message
    const emptyStateText = await page.locator('text=Aucune recherche').first();
    const emptyStateVisible = await emptyStateText.isVisible().catch(() => false);

    if (emptyStateVisible) {
      console.log('PASS: Empty state message is visible');
    } else {
      // Check if there are results instead
      const resultsCount = await page.locator('text=/\\d+ recherche/').first();
      const hasResults = await resultsCount.isVisible().catch(() => false);

      if (hasResults) {
        const countText = await resultsCount.textContent();
        console.log(`INFO: Page shows results: ${countText}`);
      } else {
        console.log('INFO: Neither empty state nor results visible (may require auth)');
      }
    }

    // Test 5: Check navigation menu entry
    console.log('\n--- Test 5: Navigation menu entry ---');

    const navLink = await page.locator('a[href="/recherches"]').first();
    const navVisible = await navLink.isVisible().catch(() => false);

    if (navVisible) {
      console.log('PASS: Navigation menu entry for "Mes Recherches" exists');
    } else {
      console.log('FAIL: Navigation menu entry not found');
    }

    // Final screenshot
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-recherches-final.png',
      fullPage: true
    });
    console.log('Screenshot saved: test-recherches-final.png');

    console.log('\n=== E2E Test Complete ===');

  } catch (error) {
    console.error('Test error:', error.message);
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-recherches-error.png',
      fullPage: true
    });
  } finally {
    await browser.close();
  }
})();
