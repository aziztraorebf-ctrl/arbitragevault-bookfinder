/**
 * Phase 11 E2E Tests - Focus on SaveSearchButton flow
 * More detailed test with better toast detection
 */

const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';
const TEST_ASIN = 'B08N5WRWNW';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });

  const page = await context.newPage();

  // Listen to console for debugging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('  [BROWSER ERROR]', msg.text());
    }
  });

  try {
    console.log('\n=== SaveSearchButton E2E Test ===\n');

    // Go to AutoSourcing
    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');
    console.log('[1] Page loaded: AutoSourcing');

    // Click Analyse Manuelle tab
    await page.click('button:has-text("Analyse Manuelle")');
    await sleep(500);
    console.log('[2] Clicked Analyse Manuelle tab');

    // Enter ASIN
    const textarea = page.locator('textarea');
    await textarea.fill(TEST_ASIN);
    console.log('[3] Entered ASIN:', TEST_ASIN);

    // Click Analyze
    await page.click('button:has-text("Analyser")');
    console.log('[4] Clicked Analyser, waiting for results...');

    // Wait for results
    await page.waitForSelector('button:has-text("Sauvegarder")', { timeout: 90000 });
    console.log('[5] SaveSearchButton appeared');

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-results.png' });

    // Click Save button
    const saveButton = page.locator('button:has-text("Sauvegarder")').first();
    await saveButton.click();
    console.log('[6] Clicked SaveSearchButton');

    await sleep(500);

    // Verify modal opened
    const modalTitle = page.locator('h3:has-text("Sauvegarder la recherche")');
    if (await modalTitle.isVisible()) {
      console.log('[7] Modal opened successfully');

      await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-modal.png' });

      // Test Escape close
      await page.keyboard.press('Escape');
      await sleep(300);
      console.log('[8] Tested Escape key - Modal closed:', !(await modalTitle.isVisible()));

      // Reopen
      await saveButton.click();
      await sleep(500);

      // Test backdrop click
      await page.mouse.click(10, 10);
      await sleep(300);
      console.log('[9] Tested backdrop click - Modal closed:', !(await modalTitle.isVisible()));

      // Reopen for save
      await saveButton.click();
      await sleep(500);

      // Enter unique name
      const uniqueName = `E2E Save Test ${Date.now()}`;
      const nameInput = page.locator('input[placeholder="Nom de la recherche"]');
      await nameInput.fill(uniqueName);
      console.log('[10] Entered unique name:', uniqueName);

      // Click modal save button (the one inside the modal, not the trigger button)
      const modalSaveBtn = page.locator('.fixed.inset-0 button:has-text("Sauvegarder"):not([title])');
      await modalSaveBtn.click();
      console.log('[11] Clicked modal Save button');

      // Wait for toast to appear
      await sleep(3000);

      await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-after-save.png' });

      // Check for toast - react-hot-toast uses role="status"
      const toastContainer = page.locator('[role="status"], .go3958317564, div[class*="toast"]');
      const toastCount = await toastContainer.count();
      console.log('[12] Toast elements found:', toastCount);

      // Try different selectors for the toast content
      const toastText = await page.locator('body').textContent();
      const hasSuccessText = toastText.includes('sauvegardee') || toastText.includes('produits');
      console.log('[13] Success message in page:', hasSuccessText);

      // Look for Voir button in toast
      const voirButton = page.locator('button:has-text("Voir")');
      const voirCount = await voirButton.count();
      console.log('[14] "Voir" buttons found:', voirCount);

      if (voirCount > 0) {
        await voirButton.first().click();
        await sleep(1000);
        console.log('[15] Clicked Voir - Current URL:', page.url());

        await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-navigated.png' });

        if (page.url().includes('/recherches')) {
          console.log('\n[SUCCESS] Full save flow works correctly!');
        }
      } else {
        console.log('[WARNING] Voir button not found in toast');

        // Navigate manually to verify save worked
        await page.goto(`${TARGET_URL}/recherches`);
        await page.waitForLoadState('networkidle');
        await sleep(1000);

        await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-recherches.png' });

        // Check if our save appears
        const savedEntry = page.locator(`text=${uniqueName.substring(0, 20)}`);
        if (await savedEntry.isVisible()) {
          console.log('\n[SUCCESS] Save worked - entry found in MesRecherches!');
        } else {
          console.log('\n[PARTIAL] Toast issue but checking if entry was saved...');

          // List all visible entries
          const entries = await page.locator('h3').allTextContents();
          console.log('Entries in MesRecherches:', entries.slice(0, 5));
        }
      }

    } else {
      console.log('[ERROR] Modal did not open');
    }

  } catch (error) {
    console.error('\n[ERROR]', error.message);
    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/save-test-error.png' });
  } finally {
    console.log('\n=== Test Complete ===\n');
    await browser.close();
  }
}

runTests().catch(console.error);
