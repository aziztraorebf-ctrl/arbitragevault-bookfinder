const { chromium } = require('playwright');

(async () => {
  console.log('=== TEST 1: SURPRISE ME FLOW ===\n');

  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();

  try {
    console.log('1. Loading http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 15000 });
    console.log('OK: Page loaded\n');

    console.log('2. Taking screenshot of homepage...');
    await page.screenshot({ path: 'step1-homepage.png' });
    console.log('OK: Saved to step1-homepage.png\n');

    console.log('3. Looking for Niche Discovery link...');
    const links = await page.locator('a').allTextContents();
    console.log('Available links:', links);

    console.log('\n4. Navigating to /niche-discovery...');
    await page.goto('http://localhost:5173/niche-discovery', { waitUntil: 'networkidle', timeout: 15000 });
    console.log('OK: On Niche Discovery page\n');

    console.log('5. Taking screenshot before click...');
    await page.screenshot({ path: 'step2-before-surprise.png' });
    console.log('OK: Saved\n');

    console.log('6. Looking for Surprise Me button...');
    const buttons = await page.locator('button').allTextContents();
    console.log('Buttons found:', buttons);

    const surpriseBtn = await page.locator('button', { hasText: 'Surprise Me' });
    if (await surpriseBtn.count() > 0) {
      console.log('OK: Found Surprise Me button\n');
      console.log('7. Clicking Surprise Me...');
      await surpriseBtn.click();
      console.log('OK: Clicked\n');

      console.log('8. Waiting 5 seconds for results...');
      await page.waitForTimeout(5000);

      console.log('9. Taking screenshot after click...');
      await page.screenshot({ path: 'step3-after-surprise.png' });
      console.log('OK: Saved\n');

      const cards = await page.locator('.niche-card, [class*="Card"]').count();
      console.log('RESULT: Found', cards, 'niche cards\n');

    } else {
      console.log('ERROR: Surprise Me button not found\n');
    }

  } catch (error) {
    console.error('ERROR:', error.message);
    await page.screenshot({ path: 'error.png' });
  } finally {
    await browser.close();
    console.log('=== TEST COMPLETE ===');
  }
})();
