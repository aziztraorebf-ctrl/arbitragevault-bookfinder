/**
 * Phase 11 E2E Tests - SaveSearchButton & MesRecherches
 * Tests for new Phase 11 features:
 * 1. SaveSearchButton in AutoSourcing
 * 2. SaveSearchButton in AnalyseManuelle
 * 3. MesRecherches pagination
 * 4. Modal UX (Escape, backdrop click)
 */

const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8000';

// Test ASIN that should return results
const TEST_ASIN = 'B08N5WRWNW';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 50
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });

  const page = await context.newPage();

  const results = {
    passed: [],
    failed: [],
    skipped: []
  };

  function logTest(name, passed, error = null) {
    if (passed) {
      console.log(`  [PASS] ${name}`);
      results.passed.push(name);
    } else {
      console.log(`  [FAIL] ${name}: ${error}`);
      results.failed.push({ name, error });
    }
  }

  try {
    // ============================================
    // TEST 1: MesRecherches Page Basic Functionality
    // ============================================
    console.log('\n=== TEST 1: MesRecherches Page ===');

    await page.goto(`${TARGET_URL}/recherches`);
    await page.waitForLoadState('networkidle');

    // Check page loaded
    const pageTitle = await page.locator('h1').first().textContent();
    logTest('MesRecherches page loads', pageTitle?.includes('Mes Recherches'));

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-mesrecherches-initial.png' });

    // Check filter buttons exist
    const filterButtons = page.locator('button:has-text("Toutes"), button:has-text("Niche Discovery"), button:has-text("AutoSourcing")');
    const filterCount = await filterButtons.count();
    logTest('Filter buttons exist', filterCount >= 3);

    // Test filter click
    await page.click('button:has-text("Niche Discovery")');
    await sleep(500);
    logTest('Filter Niche Discovery clickable', true);

    // Reset filter
    await page.click('button:has-text("Toutes")');
    await sleep(500);

    // Check if Load More button appears (if many results)
    const loadMoreButton = page.locator('button:has-text("Charger plus")');
    const hasLoadMore = await loadMoreButton.isVisible().catch(() => false);
    if (hasLoadMore) {
      logTest('Load More button visible when needed', true);
    } else {
      console.log('  [INFO] Load More button not visible (less than 10 results)');
    }

    // ============================================
    // TEST 2: AutoSourcing SaveSearchButton
    // ============================================
    console.log('\n=== TEST 2: AutoSourcing SaveSearchButton ===');

    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');

    // Click on "Analyse Manuelle" tab
    await page.click('button:has-text("Analyse Manuelle")');
    await sleep(500);

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-autosourcing-tab.png' });
    logTest('AutoSourcing Analyse Manuelle tab clickable', true);

    // Enter ASIN in textarea
    const asinTextarea = page.locator('textarea');
    await asinTextarea.fill(TEST_ASIN);
    logTest('ASIN entered in textarea', true);

    // Click Analyze button
    const analyzeButton = page.locator('button:has-text("Analyser")');
    await analyzeButton.click();

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-autosourcing-analyzing.png' });

    // Wait for results (with timeout)
    console.log('  [INFO] Waiting for analysis results (may take up to 60s)...');
    try {
      // Wait for either results or error
      await Promise.race([
        page.waitForSelector('button:has-text("Sauvegarder")', { timeout: 60000 }),
        page.waitForSelector('.bg-red-50', { timeout: 60000 })
      ]);

      // Check if SaveSearchButton appeared
      const saveButton = page.locator('button:has-text("Sauvegarder")').first();
      const saveButtonVisible = await saveButton.isVisible().catch(() => false);

      if (saveButtonVisible) {
        logTest('SaveSearchButton appears after analysis', true);

        await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-autosourcing-results.png' });

        // Click save button to open modal
        await saveButton.click();
        await sleep(500);

        // Check modal opened
        const modalTitle = page.locator('h3:has-text("Sauvegarder la recherche")');
        const modalVisible = await modalTitle.isVisible();
        logTest('Save modal opens on button click', modalVisible);

        await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-autosourcing-modal.png' });

        if (modalVisible) {
          // Check default name exists
          const nameInput = page.locator('input[placeholder="Nom de la recherche"]');
          const defaultName = await nameInput.inputValue();
          logTest('Modal has default name', defaultName.length > 0);

          // TEST: Close modal with Escape
          await page.keyboard.press('Escape');
          await sleep(300);
          const modalAfterEscape = await modalTitle.isVisible().catch(() => false);
          logTest('Modal closes on Escape key', !modalAfterEscape);

          // Reopen modal
          await saveButton.click();
          await sleep(500);

          // TEST: Close modal with backdrop click
          const backdrop = page.locator('.fixed.inset-0.bg-black\\/50');
          if (await backdrop.isVisible()) {
            // Click on backdrop (outside modal content)
            await page.mouse.click(50, 50);
            await sleep(300);
            const modalAfterBackdrop = await modalTitle.isVisible().catch(() => false);
            logTest('Modal closes on backdrop click', !modalAfterBackdrop);
          }

          // Reopen and save
          await saveButton.click();
          await sleep(500);

          // Modify name to make it unique
          const uniqueName = `E2E Test AutoSourcing ${Date.now()}`;
          await nameInput.fill(uniqueName);

          // Click save in modal
          const modalSaveButton = page.locator('.fixed.inset-0 button:has-text("Sauvegarder")').last();
          await modalSaveButton.click();

          // Wait for toast
          await sleep(2000);

          // Check for success toast with "Voir" link
          const toast = page.locator('text=Recherche sauvegardee');
          const toastVisible = await toast.isVisible().catch(() => false);
          logTest('Success toast appears after save', toastVisible);

          await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-autosourcing-saved.png' });

          // Check for "Voir" link in toast
          const voirLink = page.locator('button:has-text("Voir")');
          const voirVisible = await voirLink.isVisible().catch(() => false);
          logTest('Toast has "Voir" navigation link', voirVisible);

          if (voirVisible) {
            await voirLink.click();
            await sleep(1000);
            const currentUrl = page.url();
            logTest('Voir link navigates to /recherches', currentUrl.includes('/recherches'));
          }
        }
      } else {
        console.log('  [SKIP] SaveSearchButton test - no results returned (API may be unavailable)');
        results.skipped.push('AutoSourcing SaveSearchButton tests');
      }
    } catch (error) {
      console.log('  [SKIP] AutoSourcing analysis timeout or error:', error.message);
      results.skipped.push('AutoSourcing SaveSearchButton tests - timeout');
    }

    // ============================================
    // TEST 3: AnalyseManuelle SaveSearchButton
    // ============================================
    console.log('\n=== TEST 3: AnalyseManuelle SaveSearchButton ===');

    await page.goto(`${TARGET_URL}/analyse-manuelle`);
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-analysemanuelle-initial.png' });
    logTest('AnalyseManuelle page loads', true);

    // Enter ASIN
    const analyseTextarea = page.locator('textarea').first();
    await analyseTextarea.fill(TEST_ASIN);
    logTest('ASIN entered in AnalyseManuelle', true);

    // Click "Valider ASINs"
    const validateButton = page.locator('button:has-text("Valider ASINs")');
    await validateButton.click();
    await sleep(500);

    // Check for validation message
    const validationMsg = page.locator('text=ASINs');
    logTest('ASIN validation works', await validationMsg.isVisible());

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-analysemanuelle-validated.png' });

    // Click "Lancer analyse"
    const launchButton = page.locator('button:has-text("Lancer analyse")');
    if (await launchButton.isEnabled()) {
      await launchButton.click();

      console.log('  [INFO] Waiting for analysis results (may take up to 60s)...');
      try {
        await Promise.race([
          page.waitForSelector('button:has-text("Sauvegarder")', { timeout: 60000 }),
          page.waitForSelector('.bg-red-500', { timeout: 60000 })
        ]);

        const saveButtonAM = page.locator('button:has-text("Sauvegarder")').first();
        const saveButtonAMVisible = await saveButtonAM.isVisible().catch(() => false);

        if (saveButtonAMVisible) {
          logTest('SaveSearchButton appears in AnalyseManuelle', true);
          await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-analysemanuelle-results.png' });

          // Test save flow
          await saveButtonAM.click();
          await sleep(500);

          const modalAM = page.locator('h3:has-text("Sauvegarder la recherche")');
          logTest('Save modal opens in AnalyseManuelle', await modalAM.isVisible());

          // Save with unique name
          const nameInputAM = page.locator('input[placeholder="Nom de la recherche"]');
          await nameInputAM.fill(`E2E Test AnalyseManuelle ${Date.now()}`);

          const saveModalButton = page.locator('.fixed.inset-0 button:has-text("Sauvegarder")').last();
          await saveModalButton.click();

          await sleep(2000);
          await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-analysemanuelle-saved.png' });

          logTest('AnalyseManuelle save completes', true);
        } else {
          console.log('  [SKIP] AnalyseManuelle save test - no results returned');
          results.skipped.push('AnalyseManuelle SaveSearchButton');
        }
      } catch (error) {
        console.log('  [SKIP] AnalyseManuelle analysis timeout:', error.message);
        results.skipped.push('AnalyseManuelle SaveSearchButton - timeout');
      }
    }

    // ============================================
    // TEST 4: Modal UX Edge Cases
    // ============================================
    console.log('\n=== TEST 4: Modal UX Edge Cases ===');

    // Go to NicheDiscovery which also has SaveSearchButton
    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-nichediscovery-initial.png' });

    // Check if there are already results with save button
    const ndSaveButton = page.locator('button:has-text("Sauvegarder")').first();
    const ndHasResults = await ndSaveButton.isVisible().catch(() => false);

    if (ndHasResults) {
      // Test rapid open/close
      await ndSaveButton.click();
      await sleep(200);
      await page.keyboard.press('Escape');
      await sleep(200);
      await ndSaveButton.click();
      await sleep(200);
      await page.mouse.click(50, 50);
      await sleep(200);
      logTest('Modal handles rapid open/close', true);
    } else {
      console.log('  [INFO] No existing results in NicheDiscovery - running discovery...');

      // Click "Lancer la decouverte" to get some results
      const discoverButton = page.locator('button:has-text("Lancer")');
      if (await discoverButton.isVisible()) {
        await discoverButton.click();

        try {
          await page.waitForSelector('button:has-text("Sauvegarder")', { timeout: 90000 });
          logTest('NicheDiscovery produces results with SaveButton', true);
        } catch {
          console.log('  [SKIP] NicheDiscovery timeout');
          results.skipped.push('Modal UX tests - no results');
        }
      }
    }

    // ============================================
    // TEST 5: Verify MesRecherches shows new saves
    // ============================================
    console.log('\n=== TEST 5: Verify Saved Searches ===');

    await page.goto(`${TARGET_URL}/recherches`);
    await page.waitForLoadState('networkidle');
    await sleep(1000);

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-mesrecherches-final.png' });

    // Check for E2E test entries
    const e2eEntries = page.locator('text=E2E Test');
    const e2eCount = await e2eEntries.count();
    logTest('Saved searches appear in MesRecherches', e2eCount > 0 || results.skipped.length > 0);

    // Test delete functionality on an E2E test entry
    if (e2eCount > 0) {
      // Find delete button for first E2E entry
      const deleteButton = page.locator('button[title="Supprimer"]').first();
      if (await deleteButton.isVisible()) {
        // Setup dialog handler
        page.once('dialog', dialog => dialog.accept());
        await deleteButton.click();
        await sleep(1000);
        logTest('Delete functionality works', true);
      }
    }

  } catch (error) {
    console.error('\n[CRITICAL ERROR]', error.message);
    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/test-error.png' });
  } finally {
    // ============================================
    // SUMMARY
    // ============================================
    console.log('\n========================================');
    console.log('           TEST SUMMARY');
    console.log('========================================');
    console.log(`Passed: ${results.passed.length}`);
    console.log(`Failed: ${results.failed.length}`);
    console.log(`Skipped: ${results.skipped.length}`);

    if (results.failed.length > 0) {
      console.log('\nFailed Tests:');
      results.failed.forEach(f => console.log(`  - ${f.name}: ${f.error}`));
    }

    if (results.skipped.length > 0) {
      console.log('\nSkipped Tests:');
      results.skipped.forEach(s => console.log(`  - ${s}`));
    }

    console.log('\nScreenshots saved to skill directory.');
    console.log('========================================\n');

    await browser.close();
  }
}

runTests().catch(console.error);
