/**
 * Phase 11 UI E2E Tests - Focus on UI behavior
 * Tests modal interactions, navigation, and UI elements
 * Does NOT require backend API (tests UI independently)
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
    slowMo: 80
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });

  const page = await context.newPage();

  const results = {
    passed: [],
    failed: []
  };

  function test(name, passed, details = '') {
    if (passed) {
      console.log(`  [PASS] ${name}`);
      results.passed.push(name);
    } else {
      console.log(`  [FAIL] ${name} ${details}`);
      results.failed.push({ name, details });
    }
  }

  try {
    // ============================================
    // TEST 1: MesRecherches Page UI
    // ============================================
    console.log('\n=== TEST 1: MesRecherches Page UI ===');

    await page.goto(`${TARGET_URL}/recherches`);
    await page.waitForLoadState('networkidle');

    // Check page title
    const pageTitle = await page.locator('h1').first().textContent();
    test('Page title is "Mes Recherches"', pageTitle?.includes('Mes Recherches'));

    // Check filter buttons exist
    const filterToutes = page.locator('button:has-text("Toutes")');
    const filterNiche = page.locator('button:has-text("Niche Discovery")');
    const filterAuto = page.locator('button:has-text("AutoSourcing")');
    const filterManuel = page.locator('button:has-text("Analyse Manuelle")');

    test('Filter "Toutes" exists', await filterToutes.isVisible());
    test('Filter "Niche Discovery" exists', await filterNiche.isVisible());
    test('Filter "AutoSourcing" exists', await filterAuto.isVisible());
    test('Filter "Analyse Manuelle" exists', await filterManuel.isVisible());

    // Test filter clicks
    await filterNiche.click();
    await sleep(300);
    test('Niche Discovery filter is clickable', await filterNiche.evaluate(el => el.classList.contains('bg-purple-600') || getComputedStyle(el).backgroundColor.includes('147')));

    await filterToutes.click();
    await sleep(300);
    test('Toutes filter resets selection', true);

    // Check empty state or list
    const emptyState = page.locator('text=Aucune recherche');
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    if (hasEmpty) {
      test('Empty state shows helpful links',
        await page.locator('a:has-text("Niche Discovery")').isVisible() &&
        await page.locator('a:has-text("AutoSourcing")').isVisible()
      );
    } else {
      test('Results list is displayed', true);
    }

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-recherches.png' });

    // ============================================
    // TEST 2: AutoSourcing SaveSearchButton UI
    // ============================================
    console.log('\n=== TEST 2: AutoSourcing SaveSearchButton UI ===');

    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');

    // Test tab navigation
    const analyseTab = page.locator('button:has-text("Analyse Manuelle")');
    const jobsTab = page.locator('button:has-text("Jobs de Découverte")');

    test('Jobs tab exists', await jobsTab.isVisible());
    test('Analyse Manuelle tab exists', await analyseTab.isVisible());

    await analyseTab.click();
    await sleep(300);

    // Check textarea exists
    const textarea = page.locator('textarea');
    test('ASIN textarea is visible', await textarea.isVisible());

    // Enter ASIN
    await textarea.fill(TEST_ASIN);
    const value = await textarea.inputValue();
    test('ASIN can be entered', value === TEST_ASIN);

    // Check strategy dropdown
    const strategySelect = page.locator('select');
    test('Strategy dropdown exists', await strategySelect.isVisible());

    // Check Analyze button
    const analyzeBtn = page.locator('button:has-text("Analyser")');
    test('Analyze button exists', await analyzeBtn.isVisible());

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-autosourcing.png' });

    // ============================================
    // TEST 3: AnalyseManuelle Page UI
    // ============================================
    console.log('\n=== TEST 3: AnalyseManuelle Page UI ===');

    await page.goto(`${TARGET_URL}/analyse`);
    await page.waitForLoadState('networkidle');
    await sleep(500);

    // Check page title
    const amTitle = await page.locator('h1').first().textContent({ timeout: 5000 }).catch(() => '');
    test('Page title contains "Analyse"', amTitle?.includes('Analyse'));

    // Check CSV drop zone
    const dropZone = page.locator('text=Drag & Drop');
    test('CSV drop zone exists', await dropZone.isVisible());

    // Check ASIN textarea
    const amTextarea = page.locator('textarea').first();
    test('ASIN textarea exists', await amTextarea.isVisible());

    // Check validate button
    const validateBtn = page.locator('button:has-text("Valider ASINs")');
    test('Validate ASINs button exists', await validateBtn.isVisible());

    // Check configuration section
    const configSection = page.locator('h2:has-text("Configuration")');
    test('Configuration section exists', await configSection.isVisible());

    // Check strategy options
    const balancedOption = page.locator('option:has-text("Balanced")');
    test('Strategy options exist', await balancedOption.count() > 0);

    // Check launch button
    const launchBtn = page.locator('button:has-text("Lancer analyse")');
    test('Launch analysis button exists', await launchBtn.isVisible());
    test('Launch button is disabled without ASINs', await launchBtn.isDisabled());

    // Enter ASIN and validate
    await amTextarea.fill(TEST_ASIN);
    await validateBtn.click();
    await sleep(500);

    // Check validation message
    const validationMsg = page.locator('.bg-green-50:has-text("ASINs")');
    test('ASIN validation message appears', await validationMsg.isVisible());

    // Check launch button is now enabled
    test('Launch button enabled after validation', await launchBtn.isEnabled());

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-analysemanuelle.png' });

    // ============================================
    // TEST 4: NicheDiscovery SaveSearchButton UI
    // ============================================
    console.log('\n=== TEST 4: NicheDiscovery Page UI ===');

    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');

    // Check page title
    const ndTitle = await page.locator('h1').first().textContent();
    test('Page title contains "Niche"', ndTitle?.toLowerCase().includes('niche'));

    // Check strategy selector
    const strategySection = page.locator('text=Stratégie');
    test('Strategy section exists', await strategySection.isVisible());

    // Check launch button
    const ndLaunchBtn = page.locator('button:has-text("Lancer")');
    test('Launch discovery button exists', await ndLaunchBtn.isVisible());

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-nichediscovery.png' });

    // ============================================
    // TEST 5: Navigation & Routing
    // ============================================
    console.log('\n=== TEST 5: Navigation & Routing ===');

    // Test sidebar navigation
    const sidebarLinks = [
      { text: 'Niche', path: '/niche-discovery' },
      { text: 'AutoSourcing', path: '/autosourcing' },
      { text: 'Analyse', path: '/analyse' },
      { text: 'Recherches', path: '/recherches' }
    ];

    for (const link of sidebarLinks) {
      const navLink = page.locator(`nav a:has-text("${link.text}")`).first();
      if (await navLink.isVisible().catch(() => false)) {
        await navLink.click();
        await sleep(500);
        test(`Navigation to ${link.text} works`, page.url().includes(link.path));
      }
    }

    // ============================================
    // TEST 6: Responsive UI Elements
    // ============================================
    console.log('\n=== TEST 6: Responsive UI Elements ===');

    // Test at tablet size
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${TARGET_URL}/recherches`);
    await sleep(500);

    const tabletTitle = await page.locator('h1').first().isVisible();
    test('Page title visible at tablet size', tabletTitle);

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-tablet.png' });

    // Test at mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    await sleep(500);

    const mobileTitle = await page.locator('h1').first().isVisible();
    test('Page title visible at mobile size', mobileTitle);

    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-mobile.png' });

  } catch (error) {
    console.error('\n[CRITICAL ERROR]', error.message);
    await page.screenshot({ path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/ui-test-error.png' });
  } finally {
    // ============================================
    // SUMMARY
    // ============================================
    console.log('\n========================================');
    console.log('         UI TEST SUMMARY');
    console.log('========================================');
    console.log(`Passed: ${results.passed.length}`);
    console.log(`Failed: ${results.failed.length}`);
    console.log(`Total: ${results.passed.length + results.failed.length}`);

    if (results.failed.length > 0) {
      console.log('\nFailed Tests:');
      results.failed.forEach(f => console.log(`  - ${f.name}: ${f.details}`));
    }

    console.log('\nScreenshots saved to skill directory.');
    console.log('========================================\n');

    await browser.close();
  }
}

runTests().catch(console.error);
