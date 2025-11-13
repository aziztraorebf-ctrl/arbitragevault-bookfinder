const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('1. Navigating to Netlify production site...');
  await page.goto('https://arbitragevault.netlify.app/niche-discovery');

  console.log('2. Waiting for page to load...');
  await page.waitForLoadState('networkidle');

  console.log('3. Clicking "Surprise Me" button...');
  const surpriseButton = page.locator('button:has-text("Surprise Me")');
  await surpriseButton.click();

  console.log('4. Waiting 15 seconds for API response...');
  await page.waitForTimeout(15000);

  console.log('5. Checking results...');

  // Check for niche cards
  const nicheCards = await page.locator('[class*="NicheCard"]').count();
  console.log(`   Niche cards found: ${nicheCards}`);

  // Check for loading indicators
  const loadingElements = await page.locator('text=/loading|spinner/i').count();
  console.log(`   Loading indicators: ${loadingElements}`);

  // Check for error messages
  const errorElements = await page.locator('text=/error|failed|something went wrong/i').count();
  console.log(`   Error messages: ${errorElements}`);

  // Capture network requests
  const requests = [];
  page.on('response', response => {
    if (response.url().includes('arbitragevault-backend-v2.onrender.com')) {
      requests.push({
        status: response.status(),
        url: response.url()
      });
    }
  });

  // Take screenshot
  await page.screenshot({ path: 'netlify-surprise-me-result.png', fullPage: true });
  console.log('   Screenshot saved: netlify-surprise-me-result.png');

  // Summary
  console.log('\n=== TEST RESULTS ===');
  if (nicheCards > 0 && loadingElements === 0 && errorElements === 0) {
    console.log('SUCCESS: Niches displayed correctly!');
    console.log(`Found ${nicheCards} niche cards`);
  } else if (loadingElements > 0) {
    console.log('HANGING: Page still loading after 15 seconds');
  } else if (errorElements > 0) {
    console.log('ERROR: Error message displayed on page');
  } else {
    console.log('UNKNOWN: No niches, no loading, no errors');
  }

  await browser.close();
})();
