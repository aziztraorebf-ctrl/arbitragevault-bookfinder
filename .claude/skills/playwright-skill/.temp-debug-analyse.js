const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto('http://localhost:5173/analyse-manuelle');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({
    path: 'c:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/skills/playwright-skill/debug-analyse.png',
    fullPage: true
  });

  console.log('Current URL:', page.url());

  // Get page content
  const content = await page.content();
  console.log('Page has h1:', content.includes('<h1'));
  console.log('Page has textarea:', content.includes('<textarea'));
  console.log('Page has "Analyse":', content.includes('Analyse'));

  // List all visible text
  const bodyText = await page.locator('body').textContent();
  console.log('\nFirst 500 chars of page text:');
  console.log(bodyText?.substring(0, 500));

  await browser.close();
})();
