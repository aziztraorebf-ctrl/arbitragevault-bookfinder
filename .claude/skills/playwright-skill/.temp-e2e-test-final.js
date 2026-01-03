const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  console.log('=== E2E TEST SUITE - 3 Critical Flows ===\n');

  const browser = await chromium.launch({ headless: false, slowMo: 200 });
  const page = await browser.newPage();

  // Listen to API calls
  page.on('response', async response => {
    if (response.url().includes('/api/v1/')) {
      const status = response.status();
      const url = response.url().split('/api/v1/')[1];
      if (status >= 400) {
        console.log(`   [API ERROR] ${status} - ${url}`);
        try {
          const body = await response.text();
          console.log(`   Response: ${body.substring(0, 200)}`);
        } catch (e) {}
      } else {
        console.log(`   [API OK] ${status} - ${url}`);
      }
    }
  });

  const results = {
    test1: { name: 'Analyse Manuelle', status: 'pending', error: null },
    test2: { name: 'AutoSourcing - Analyse Onglet', status: 'pending', error: null },
    test3: { name: 'Niche Discovery', status: 'pending', error: null },
  };

  // ============== TEST 1: Analyse Manuelle ==============
  console.log('\n--- TEST 1: Analyse Manuelle (/analyse) ---');
  try {
    await page.goto(`${TARGET_URL}/analyse`);
    await page.waitForLoadState('networkidle');
    console.log('   Page loaded');

    // Find textarea and enter ASIN
    const textarea = page.locator('textarea');
    await textarea.fill('0593655036');
    console.log('   ASIN entered: 0593655036');

    // Click Valider ASINs button
    const validerButton = page.locator('button:has-text("Valider")');
    if (await validerButton.count() > 0) {
      await validerButton.click();
      console.log('   Clicked Valider button');
      await page.waitForTimeout(500);
    }

    // Click Lancer analyse button
    const lancerButton = page.locator('button:has-text("Lancer")');
    if (await lancerButton.count() > 0) {
      await lancerButton.click();
      console.log('   Clicked Lancer analyse button');
    } else {
      // Try clicking Analyser button instead
      const analyserButton = page.locator('button:has-text("Analyser")');
      if (await analyserButton.count() > 0) {
        await analyserButton.click();
        console.log('   Clicked Analyser button');
      }
    }

    // Wait for results
    console.log('   Waiting for API response...');
    await page.waitForTimeout(10000);

    // Check for score display
    const scoreElement = page.locator('text=/Score.*[0-9]/i');
    if (await scoreElement.count() > 0) {
      const scoreText = await scoreElement.first().textContent();
      console.log(`   Score found: ${scoreText}`);
      results.test1.status = 'PASS';
    } else {
      // Check for any product card/row
      const productRow = page.locator('[data-testid="product-row"], .product-card, tr:has(td)');
      if (await productRow.count() > 0) {
        console.log('   Product row found in results');
        results.test1.status = 'PASS';
      } else {
        results.test1.status = 'PARTIAL';
        results.test1.error = 'No score or product rows visible';
      }
    }

    await page.screenshot({ path: '/tmp/test1-analyse-manuelle.png', fullPage: true });
    console.log('   Screenshot: /tmp/test1-analyse-manuelle.png');

  } catch (err) {
    results.test1.status = 'FAIL';
    results.test1.error = err.message;
    console.log(`   ERROR: ${err.message}`);
  }

  // ============== TEST 2: AutoSourcing - Analyse Tab ==============
  console.log('\n--- TEST 2: AutoSourcing - Analyse Tab (/autosourcing) ---');
  try {
    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');
    console.log('   Page loaded');

    // Click on "Analyse Manuelle" tab
    const analyseTab = page.locator('button:has-text("Analyse Manuelle")');
    if (await analyseTab.count() > 0) {
      await analyseTab.click();
      console.log('   Clicked Analyse Manuelle tab');
      await page.waitForTimeout(500);
    } else {
      console.log('   Warning: Analyse Manuelle tab not found');
    }

    // Find textarea and enter ASIN
    const textarea = page.locator('textarea');
    await textarea.fill('0593655036');
    console.log('   ASIN entered: 0593655036');

    // Click the Analyze button
    const analyzeButton = page.locator('button:has-text("Analyser")');
    if (await analyzeButton.count() > 0) {
      await analyzeButton.click();
      console.log('   Clicked Analyser button');
    }

    // Wait for results
    console.log('   Waiting for API response...');
    await page.waitForTimeout(10000);

    // Check for score or product display
    const scoreElement = page.locator('text=/Score.*[0-9]/i');
    if (await scoreElement.count() > 0) {
      const scoreText = await scoreElement.first().textContent();
      console.log(`   Score found: ${scoreText}`);
      results.test2.status = 'PASS';
    } else {
      const productRow = page.locator('[data-testid="product-row"], .product-card');
      if (await productRow.count() > 0) {
        console.log('   Product results found');
        results.test2.status = 'PASS';
      } else {
        results.test2.status = 'PARTIAL';
        results.test2.error = 'No score or product rows visible';
      }
    }

    await page.screenshot({ path: '/tmp/test2-autosourcing.png', fullPage: true });
    console.log('   Screenshot: /tmp/test2-autosourcing.png');

  } catch (err) {
    results.test2.status = 'FAIL';
    results.test2.error = err.message;
    console.log(`   ERROR: ${err.message}`);
  }

  // ============== TEST 3: Niche Discovery ==============
  console.log('\n--- TEST 3: Niche Discovery (/niche-discovery) ---');
  try {
    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');
    console.log('   Page loaded');

    // Click on "Textbook Standard" button
    const textbookButton = page.locator('button:has-text("Textbook Standard")');
    if (await textbookButton.count() > 0) {
      console.log('   Found Textbook Standard button');
      await textbookButton.click();
      console.log('   Clicked Textbook Standard button');
    } else {
      // Try alternative: any button containing "Textbook"
      const altButton = page.locator('button:has-text("Textbook")');
      if (await altButton.count() > 0) {
        await altButton.first().click();
        console.log('   Clicked first Textbook button');
      } else {
        throw new Error('No Textbook strategy button found');
      }
    }

    // Wait for loading to complete (up to 60 seconds for API)
    console.log('   Waiting for niches to load (this may take up to 60s)...');

    // Wait for either:
    // 1. Loading indicator to disappear
    // 2. Niche cards to appear
    // 3. Error message
    const loadingIndicator = page.locator('text=/Exploration.*en cours/i, .animate-spin');
    const nicheCard = page.locator('[class*="NicheCard"], .grid .rounded-xl, text="Niches Découvertes"');
    const errorMsg = page.locator('.text-red-500, .bg-red-50, text=/erreur/i');

    let loaded = false;
    for (let i = 0; i < 30; i++) {
      // Check if loading is done
      if (await loadingIndicator.count() === 0 || !(await loadingIndicator.isVisible())) {
        // Check for results or error
        if (await nicheCard.count() > 0) {
          console.log('   Niche cards loaded');
          loaded = true;
          break;
        }
        if (await errorMsg.count() > 0) {
          const errText = await errorMsg.first().textContent();
          throw new Error(`API error: ${errText}`);
        }
      }
      await page.waitForTimeout(2000);
      console.log(`   Still loading... (${(i+1)*2}s)`);
    }

    if (loaded) {
      results.test3.status = 'PASS';

      // Try to click "Explorer" on first niche card
      const exploreButton = page.locator('button:has-text("Explorer"), button:has-text("Voir")');
      if (await exploreButton.count() > 0) {
        console.log('   Found Explorer button on niche card');
        // Don't click to avoid consuming more API tokens
      }
    } else {
      results.test3.status = 'TIMEOUT';
      results.test3.error = 'Loading did not complete within 60s';
    }

    await page.screenshot({ path: '/tmp/test3-niche-discovery.png', fullPage: true });
    console.log('   Screenshot: /tmp/test3-niche-discovery.png');

  } catch (err) {
    results.test3.status = 'FAIL';
    results.test3.error = err.message;
    console.log(`   ERROR: ${err.message}`);
  }

  // ============== SUMMARY ==============
  console.log('\n\n========================================');
  console.log('           E2E TEST RESULTS            ');
  console.log('========================================\n');

  for (const [key, result] of Object.entries(results)) {
    const icon = result.status === 'PASS' ? '[PASS]' :
                 result.status === 'PARTIAL' ? '[PARTIAL]' :
                 result.status === 'TIMEOUT' ? '[TIMEOUT]' : '[FAIL]';
    console.log(`${icon} ${result.name}`);
    if (result.error) {
      console.log(`       Error: ${result.error}`);
    }
  }

  const passed = Object.values(results).filter(r => r.status === 'PASS').length;
  const total = Object.keys(results).length;
  console.log(`\nTotal: ${passed}/${total} tests passed`);
  console.log('\nScreenshots saved to /tmp/');

  await browser.close();
})();
