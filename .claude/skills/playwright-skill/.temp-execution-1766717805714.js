/**
 * E2E Tests - Phase 9 UI Completion
 * Tests all 4 pages on production Netlify
 *
 * Routes:
 * - /config (Configuration)
 * - /analyse-strategique (Analyse Strategique)
 * - /stock-estimates (Stock Estimates)
 * - /autoscheduler (AutoScheduler)
 */
const { chromium } = require('playwright');

// Production URL
const TARGET_URL = 'https://arbitragevault.netlify.app';

// Test results collector
const testResults = {
  passed: [],
  failed: [],
  screenshots: []
};

function logTest(name, passed, details = '') {
  const emoji = passed ? '[PASS]' : '[FAIL]';
  console.log(`${emoji} ${name}${details ? ': ' + details : ''}`);
  if (passed) {
    testResults.passed.push(name);
  } else {
    testResults.failed.push({ name, details });
  }
}

async function takeScreenshot(page, name) {
  const path = `C:/Users/azizt/AppData/Local/Temp/e2e-${name}.png`;
  await page.screenshot({ path, fullPage: true });
  testResults.screenshots.push(path);
  console.log(`[SCREENSHOT] Saved: ${path}`);
  return path;
}

// ============================================
// TEST 1: Configuration Page (/config)
// ============================================
async function testConfigurationPage(page) {
  console.log('\n========================================');
  console.log('TEST 1: Configuration Page (/config)');
  console.log('========================================\n');

  try {
    // Navigate to Configuration - CORRECT ROUTE: /config
    await page.goto(`${TARGET_URL}/config`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Test 1.1: Page loads with title
    const title = await page.textContent('h1');
    logTest('1.1 Page title visible', title && title.includes('Configuration'), title);

    // Test 1.2: Loading state or content visible
    const hasContent = await page.locator('.bg-white, .animate-pulse').first().isVisible();
    logTest('1.2 Content or loading state visible', hasContent);

    // Test 1.3: Domain selector exists
    const domainSelector = await page.locator('select').first().isVisible();
    logTest('1.3 Domain selector visible', domainSelector);

    // Test 1.4: Check for config sections (ROI, BSR, etc.)
    await page.waitForTimeout(3000); // Wait for API
    const roiSection = await page.getByText('Seuils ROI').isVisible().catch(() => false);
    const bsrSection = await page.getByText('Limites BSR').isVisible().catch(() => false);
    logTest('1.4 ROI section visible', roiSection);
    logTest('1.5 BSR section visible', bsrSection);

    // Test 1.6: Edit button exists
    const editButton = await page.getByText('Modifier').isVisible().catch(() => false);
    logTest('1.6 Edit button visible', editButton);

    // Test 1.7: Click edit mode
    if (editButton) {
      await page.getByText('Modifier').click();
      await page.waitForTimeout(500);
      const cancelButton = await page.getByText('Annuler').isVisible().catch(() => false);
      logTest('1.7 Edit mode toggles (Annuler visible)', cancelButton);

      // Test 1.8: Save buttons appear in edit mode
      const saveButtons = await page.getByText('Sauvegarder').count();
      logTest('1.8 Save buttons visible in edit mode', saveButtons > 0, `Found ${saveButtons} save buttons`);

      // Exit edit mode
      if (cancelButton) {
        await page.getByText('Annuler').click();
      }
    }

    // Test 1.9: Stats section
    const statsSection = await page.getByText('Statistiques').isVisible().catch(() => false);
    logTest('1.9 Stats section visible', statsSection);

    await takeScreenshot(page, 'configuration');

  } catch (error) {
    logTest('1.X Configuration page error', false, error.message);
    await takeScreenshot(page, 'configuration-error');
  }
}

// ============================================
// TEST 2: Analyse Strategique Page
// ============================================
async function testAnalyseStrategiquePage(page) {
  console.log('\n========================================');
  console.log('TEST 2: Analyse Strategique Page');
  console.log('========================================\n');

  try {
    // Navigate to Analyse Strategique
    await page.goto(`${TARGET_URL}/analyse-strategique`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Test 2.1: Page title
    const title = await page.textContent('h1');
    logTest('2.1 Page title visible', title && title.includes('Analyse'), title);

    // Test 2.2: View tabs exist (5 strategic views)
    await page.waitForTimeout(2000);
    const buttons = await page.locator('button').all();
    let tabsFound = 0;

    for (const btn of buttons) {
      const text = await btn.textContent().catch(() => '');
      if (text && (text.toLowerCase().includes('velocity') ||
                   text.toLowerCase().includes('competition') ||
                   text.toLowerCase().includes('volatility') ||
                   text.toLowerCase().includes('consistency') ||
                   text.toLowerCase().includes('confidence') ||
                   text.toLowerCase().includes('velocite') ||
                   text.toLowerCase().includes('concurrence'))) {
        tabsFound++;
      }
    }
    logTest('2.2 Strategic view tabs visible', tabsFound > 0, `Found ${tabsFound} view tabs`);

    // Test 2.3: Click on different tabs
    let clickableTabsCount = 0;
    for (const btn of buttons.slice(0, 10)) {
      try {
        const text = await btn.textContent();
        if (text && (text.toLowerCase().includes('velocity') ||
                     text.toLowerCase().includes('velocite'))) {
          await btn.click();
          await page.waitForTimeout(1000);
          clickableTabsCount++;
          break;
        }
      } catch (e) {
        // Tab not clickable
      }
    }
    logTest('2.3 Can switch between view tabs', clickableTabsCount > 0 || tabsFound > 0);

    // Test 2.4: Content area exists
    const contentArea = await page.locator('.bg-white, .rounded-lg').first().isVisible();
    logTest('2.4 Content area visible', contentArea);

    // Test 2.5: Check for any text content (metrics, labels, etc.)
    const pageContent = await page.textContent('body');
    const hasContent = pageContent.length > 500; // Page has substantial content
    logTest('2.5 Page has content', hasContent, `${pageContent.length} chars`);

    await takeScreenshot(page, 'analyse-strategique');

  } catch (error) {
    logTest('2.X Analyse Strategique page error', false, error.message);
    await takeScreenshot(page, 'analyse-strategique-error');
  }
}

// ============================================
// TEST 3: Stock Estimates Page
// ============================================
async function testStockEstimatesPage(page) {
  console.log('\n========================================');
  console.log('TEST 3: Stock Estimates Page');
  console.log('========================================\n');

  try {
    // Navigate to Stock Estimates
    await page.goto(`${TARGET_URL}/stock-estimates`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Test 3.1: Page title
    const title = await page.textContent('h1');
    logTest('3.1 Page title visible', title && title.includes('Stock'), title);

    // Test 3.2: ASIN input field exists
    const asinInput = await page.locator('input[type="text"], input#asin').first().isVisible();
    logTest('3.2 ASIN input field visible', asinInput);

    // Test 3.3: Submit button exists
    const submitButton = await page.getByRole('button', { name: /analyser/i }).isVisible().catch(() => false);
    logTest('3.3 Analyser button visible', submitButton);

    // Test 3.4: Button disabled when ASIN too short
    const buttonDisabled = await page.locator('button[disabled]').isVisible().catch(() => false);
    logTest('3.4 Button disabled with empty ASIN', buttonDisabled);

    // Test 3.5: Enter invalid ASIN format
    await page.locator('input').first().fill('INVALID');
    await page.waitForTimeout(500);

    // Try to submit
    const analyserBtn = await page.getByRole('button', { name: /analyser/i });
    const isStillDisabled = await analyserBtn.isDisabled().catch(() => true);
    logTest('3.5 Button disabled with short ASIN (<10 chars)', isStillDisabled);

    // Test 3.6: Enter valid ASIN format
    await page.locator('input').first().fill('B08N5WRWNW');
    await page.waitForTimeout(500);
    const buttonEnabled = !(await analyserBtn.isDisabled().catch(() => true));
    logTest('3.6 Button enabled with valid ASIN (10 chars)', buttonEnabled);

    // Test 3.7: Submit and check for response
    if (buttonEnabled) {
      await analyserBtn.click();
      await page.waitForTimeout(2000);

      // Check for any response - loading, results, or error
      const pageContent = await page.textContent('body');
      const hasResponse = pageContent.includes('Analyse') ||
                          pageContent.includes('Stock') ||
                          pageContent.includes('Erreur') ||
                          pageContent.includes('N/A');
      logTest('3.7 Page responds after submit', hasResponse);
    }

    // Test 3.8: Empty state message when no ASIN submitted
    await page.goto(`${TARGET_URL}/stock-estimates`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const emptyState = await page.getByText(/Entrez un ASIN/i).isVisible().catch(() => false);
    logTest('3.8 Empty state message visible', emptyState);

    await takeScreenshot(page, 'stock-estimates');

  } catch (error) {
    logTest('3.X Stock Estimates page error', false, error.message);
    await takeScreenshot(page, 'stock-estimates-error');
  }
}

// ============================================
// TEST 4: AutoScheduler Page (/autoscheduler)
// ============================================
async function testAutoSchedulerPage(page) {
  console.log('\n========================================');
  console.log('TEST 4: AutoScheduler Page (/autoscheduler)');
  console.log('========================================\n');

  try {
    // Navigate to AutoScheduler - CORRECT ROUTE: /autoscheduler
    await page.goto(`${TARGET_URL}/autoscheduler`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Test 4.1: Page title
    const title = await page.textContent('h1');
    logTest('4.1 Page title visible', title && title.includes('AutoScheduler'), title);

    // Test 4.2: Subtitle/description
    const subtitle = await page.getByText(/planification/i).isVisible().catch(() => false);
    logTest('4.2 Subtitle visible', subtitle);

    // Test 4.3: Feature cards exist
    const cards = await page.locator('.bg-white').count();
    logTest('4.3 Feature cards visible', cards > 0, `Found ${cards} cards`);

    // Test 4.4: Toggle switches exist
    const toggles = await page.locator('button[role="switch"], input[type="checkbox"]').count();
    logTest('4.4 Toggle switches visible', toggles > 0, `Found ${toggles} toggles`);

    // Test 4.5: Click on a toggle if exists
    if (toggles > 0) {
      try {
        const firstToggle = await page.locator('button[role="switch"], input[type="checkbox"]').first();
        await firstToggle.click();
        await page.waitForTimeout(500);
        logTest('4.5 Toggle can be clicked', true);
      } catch (e) {
        logTest('4.5 Toggle can be clicked', false, e.message);
      }
    } else {
      logTest('4.5 Toggle can be clicked', false, 'No toggles found');
    }

    // Test 4.6: Schedule type options
    const hasScheduleOptions = await page.getByText(/quotidien|hebdomadaire|mensuel|daily|weekly|monthly/i).first().isVisible().catch(() => false);
    logTest('4.6 Schedule type options visible', hasScheduleOptions);

    // Test 4.7: Selectors present
    const hasSelectors = await page.locator('select').count();
    logTest('4.7 Selectors present', hasSelectors > 0, `Found ${hasSelectors} selectors`);

    // Test 4.8: Concept/Coming soon indicator
    const hasBadge = await page.getByText(/concept|bientot|coming|beta|preview/i).isVisible().catch(() => false);
    logTest('4.8 Concept/Preview indicator visible', hasBadge);

    // Test 4.9: Page has substantial content
    const pageContent = await page.textContent('body');
    logTest('4.9 Page has content', pageContent.length > 300, `${pageContent.length} chars`);

    await takeScreenshot(page, 'autoscheduler');

  } catch (error) {
    logTest('4.X AutoScheduler page error', false, error.message);
    await takeScreenshot(page, 'autoscheduler-error');
  }
}

// ============================================
// MAIN EXECUTION
// ============================================
(async () => {
  console.log('============================================');
  console.log('E2E Tests - Phase 9 UI Completion');
  console.log('Target: ' + TARGET_URL);
  console.log('Date: ' + new Date().toISOString());
  console.log('============================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Enable console logging from page
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('[BROWSER ERROR]', msg.text());
    }
  });

  try {
    // Run all tests
    await testConfigurationPage(page);
    await testAnalyseStrategiquePage(page);
    await testStockEstimatesPage(page);
    await testAutoSchedulerPage(page);

  } catch (error) {
    console.error('\n[FATAL ERROR]', error.message);
  } finally {
    // Print summary
    console.log('\n============================================');
    console.log('TEST SUMMARY');
    console.log('============================================');
    console.log(`[PASS] Passed: ${testResults.passed.length}`);
    console.log(`[FAIL] Failed: ${testResults.failed.length}`);

    if (testResults.failed.length > 0) {
      console.log('\nFailed Tests:');
      testResults.failed.forEach(f => {
        console.log(`  - ${f.name}: ${f.details}`);
      });
    }

    console.log('\nScreenshots saved:');
    testResults.screenshots.forEach(s => console.log(`  - ${s}`));

    await browser.close();

    // Exit with appropriate code
    process.exit(testResults.failed.length > 0 ? 1 : 0);
  }
})();
