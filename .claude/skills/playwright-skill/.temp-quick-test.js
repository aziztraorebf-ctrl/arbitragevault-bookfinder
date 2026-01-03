const { chromium } = require('playwright');

(async () => {
  console.log('=== Quick AutoSourcing Test ===\n');
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  page.on('response', async response => {
    if (response.url().includes('/api/v1/views/')) {
      console.log(`   [API] ${response.status()} - ${response.url().split('/api/v1/')[1]}`);
    }
  });

  await page.goto('http://localhost:5173/autosourcing');
  await page.waitForLoadState('networkidle');

  // Click Analyse Manuelle tab
  await page.locator('button:has-text("Analyse Manuelle")').click();
  await page.waitForTimeout(300);

  // Enter ASIN
  await page.locator('textarea').fill('0593655036');

  // Click Analyser
  await page.locator('button:has-text("Analyser")').click();
  console.log('   Clicked Analyser, waiting for response...');

  await page.waitForTimeout(8000);

  // Check for score
  const scoreText = await page.locator('text=/Score.*[0-9]/i').first().textContent().catch(() => null);
  console.log(`   Score found: ${scoreText ? 'YES' : 'NO'}`);

  if (scoreText) {
    console.log('\n   RESULT: PASS');
  } else {
    console.log('\n   RESULT: FAIL - No score displayed');
  }

  await browser.close();
})();
