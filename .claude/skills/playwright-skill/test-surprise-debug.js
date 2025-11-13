const { chromium } = require('playwright');

(async () => {
  console.log('=== SURPRISE ME DEBUG TEST ===\n');

  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();

  const apiResponses = [];

  // Capture API
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('discover') || url.includes('niche') || url.includes('auto')) {
      const status = response.status();
      let body = '';
      try {
        body = await response.text();
      } catch (e) {
        body = '(unable to read)';
      }

      apiResponses.push({
        url: url,
        status: status,
        body: body.substring(0, 300)
      });

      console.log('API RESPONSE: ' + status + ' - ' + url.substring(url.lastIndexOf('/'), url.length));
      if (body && body !== '(unable to read)') {
        console.log('  ' + body.substring(0, 100) + '...');
      }
    }
  });

  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    if (type === 'error') {
      console.log('CONSOLE ERROR: ' + text);
    }
  });

  try {
    console.log('1. Loading http://localhost:5173\n');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 15000 });

    console.log('2. Navigating to /niche-discovery\n');
    await page.goto('http://localhost:5173/niche-discovery', { waitUntil: 'networkidle', timeout: 15000 });

    console.log('3. Clicking Surprise Me button\n');
    await page.click('button:has-text("Surprise Me")');

    console.log('4. Waiting 10 seconds for responses...\n');
    await page.waitForTimeout(10000);

    console.log('5. Checking results:\n');

    const niche = await page.locator('[class*="niche"], [class*="Card"]').count();
    console.log('   Niche elements: ' + niche);

    const loading = await page.locator('[class*="loading"], [class*="spinner"]').count();
    console.log('   Loading elements: ' + loading);

    const errors = await page.locator('[class*="error"]').count();
    console.log('   Error elements: ' + errors);

  } catch (error) {
    console.error('ERROR: ' + error.message);
  } finally {
    console.log('\nAPI Responses captured:');
    apiResponses.forEach(res => {
      console.log('  ' + res.status + ' ' + res.url);
      console.log('     ' + res.body);
    });

    await browser.close();
    console.log('\n=== TEST COMPLETE ===');
  }
})();
