const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  console.log('=== TEST 3: Niche Discovery ===\n');

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
          console.log(`   Response: ${body.substring(0, 300)}`);
        } catch (e) {}
      } else {
        console.log(`   [API OK] ${status} - ${url}`);
      }
    }
  });

  let result = { status: 'pending', error: null };

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
      throw new Error('No Textbook Standard button found');
    }

    // Wait for loading to complete
    console.log('   Waiting for niches to load (this may take up to 60s)...');

    // Use separate locators to avoid regex issues
    const spinnerLocator = page.locator('.animate-spin');
    const explorationTextLocator = page.locator('text=Exploration');
    const nichesHeader = page.locator('text=Niches Decouvertes');
    const nicheCards = page.locator('.grid .rounded-xl');
    const errorMessage = page.locator('.bg-red-50');

    let loaded = false;
    for (let i = 0; i < 30; i++) {
      // Check if spinner is gone
      const spinnerVisible = await spinnerLocator.count() > 0 && await spinnerLocator.first().isVisible().catch(() => false);

      if (!spinnerVisible) {
        // Check for niche cards
        const cardsCount = await nicheCards.count();
        if (cardsCount > 0) {
          console.log(`   Found ${cardsCount} niche cards!`);
          loaded = true;
          break;
        }

        // Check for error
        if (await errorMessage.count() > 0) {
          const errText = await errorMessage.first().textContent();
          throw new Error(`API error displayed: ${errText}`);
        }
      }

      await page.waitForTimeout(2000);
      console.log(`   Still loading... (${(i+1)*2}s)`);
    }

    if (loaded) {
      result.status = 'PASS';
      console.log('   SUCCESS: Niche cards loaded correctly');

      // Try to find "Verifier" button
      const verifyButton = page.locator('button:has-text("Verifier")');
      if (await verifyButton.count() > 0) {
        console.log('   Verifier button found on products');
      }
    } else {
      result.status = 'TIMEOUT';
      result.error = 'Loading did not complete within 60s';
      console.log('   TIMEOUT: Loading did not complete');
    }

    await page.screenshot({ path: '/tmp/test3-niche-discovery-fixed.png', fullPage: true });
    console.log('   Screenshot: /tmp/test3-niche-discovery-fixed.png');

  } catch (err) {
    result.status = 'FAIL';
    result.error = err.message;
    console.log(`   ERROR: ${err.message}`);
    await page.screenshot({ path: '/tmp/test3-niche-discovery-error.png', fullPage: true });
  }

  console.log('\n========================================');
  console.log('           TEST 3 RESULT              ');
  console.log('========================================');
  console.log(`Status: ${result.status}`);
  if (result.error) {
    console.log(`Error: ${result.error}`);
  }

  await browser.close();
})();
