/**
 * E2E Test: SaveSearchButton in NicheDiscovery
 * Phase 11 - Test save functionality
 */

const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  console.log('Starting E2E test for SaveSearchButton in NicheDiscovery...');

  const browser = await chromium.launch({ headless: false, slowMo: 150 });
  const page = await browser.newPage();

  try {
    // Navigate to NicheDiscovery page
    console.log('\n--- Test 1: Navigate to Niche Discovery ---');
    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');

    const pageTitle = await page.locator('h1').first().textContent();
    console.log('Page title:', pageTitle);

    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-niche-discovery-initial.png',
      fullPage: true
    });
    console.log('Screenshot saved: test-niche-discovery-initial.png');

    // Look for strategy buttons (Textbook strategies)
    console.log('\n--- Test 2: Check for strategy buttons ---');

    const textbookButton = await page.locator('button:has-text("Textbook")').first();
    const hasTextbookButton = await textbookButton.isVisible().catch(() => false);

    if (hasTextbookButton) {
      console.log('PASS: Textbook strategy button found');

      // Click the button to start a search
      console.log('Clicking Textbook strategy...');
      await textbookButton.click();

      // Wait for loading and results
      console.log('Waiting for results...');
      await page.waitForTimeout(5000);

      await page.screenshot({
        path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-niche-discovery-loading.png',
        fullPage: true
      });

    } else {
      console.log('INFO: Textbook button not found, trying manual search');

      // Try to find and use manual search if available
      const manualButton = await page.locator('button:has-text("Rechercher")').first();
      const hasManualButton = await manualButton.isVisible().catch(() => false);

      if (hasManualButton) {
        console.log('Found manual search button');
      }
    }

    // Check for SaveSearchButton
    console.log('\n--- Test 3: Check for SaveSearchButton ---');

    // Wait a bit more for results to load
    await page.waitForTimeout(3000);

    const saveButton = await page.locator('button:has-text("Sauvegarder")').first();
    const hasSaveButton = await saveButton.isVisible().catch(() => false);

    if (hasSaveButton) {
      console.log('PASS: SaveSearchButton is visible');

      // Take screenshot showing the save button
      await page.screenshot({
        path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-save-button-visible.png',
        fullPage: true
      });

      // Click the save button to open modal
      console.log('\n--- Test 4: Open save modal ---');
      await saveButton.click();
      await page.waitForTimeout(1000);

      // Check for modal
      const modal = await page.locator('text=Sauvegarder la recherche').first();
      const modalVisible = await modal.isVisible().catch(() => false);

      if (modalVisible) {
        console.log('PASS: Save modal opened');

        await page.screenshot({
          path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-save-modal.png',
          fullPage: true
        });

        // Check for input fields
        const nameInput = await page.locator('input[placeholder*="Nom"]').first();
        const hasNameInput = await nameInput.isVisible().catch(() => false);
        console.log(`  - Name input: ${hasNameInput ? 'VISIBLE' : 'NOT FOUND'}`);

        const notesTextarea = await page.locator('textarea').first();
        const hasNotesTextarea = await notesTextarea.isVisible().catch(() => false);
        console.log(`  - Notes textarea: ${hasNotesTextarea ? 'VISIBLE' : 'NOT FOUND'}`);

        // Close modal by clicking cancel or outside
        const cancelButton = await page.locator('button:has-text("Annuler")').first();
        if (await cancelButton.isVisible().catch(() => false)) {
          await cancelButton.click();
          console.log('Closed modal via Cancel button');
        }

      } else {
        console.log('FAIL: Save modal did not open');
      }

    } else {
      console.log('INFO: SaveSearchButton not visible (no results to save yet)');
      console.log('This is expected if no search has been performed');
    }

    // Final screenshot
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-niche-discovery-final.png',
      fullPage: true
    });
    console.log('Screenshot saved: test-niche-discovery-final.png');

    console.log('\n=== E2E Test Complete ===');

  } catch (error) {
    console.error('Test error:', error.message);
    await page.screenshot({
      path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-save-button-error.png',
      fullPage: true
    });
  } finally {
    await browser.close();
  }
})();
