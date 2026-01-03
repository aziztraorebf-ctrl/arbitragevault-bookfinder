const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  // Listen to network requests
  page.on('request', request => {
    if (request.url().includes('api')) {
      console.log('>> REQUEST:', request.method(), request.url());
    }
  });

  page.on('response', response => {
    if (response.url().includes('api')) {
      console.log('<< RESPONSE:', response.status(), response.url());
    }
  });

  page.on('requestfailed', request => {
    console.log('XX FAILED:', request.url(), request.failure()?.errorText);
  });

  console.log('Navigating to Analyse Manuelle...');
  await page.goto('http://localhost:5173/analyse');
  await page.waitForLoadState('networkidle');

  // Enter ASIN and click
  const textarea = page.locator('textarea');
  await textarea.fill('0593655036');
  await page.waitForTimeout(500);

  const validerButton = page.locator('button:has-text("Valider")');
  await validerButton.click();
  await page.waitForTimeout(500);

  console.log('Clicking Lancer analyse...');
  const lancerButton = page.locator('button:has-text("Lancer")');
  await lancerButton.click();

  // Wait and capture network
  await page.waitForTimeout(15000);

  await page.screenshot({ path: 'check-api-result.png', fullPage: true });
  console.log('Screenshot saved');

  await browser.close();
})();
