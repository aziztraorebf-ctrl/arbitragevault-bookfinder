/**
 * Test horizontal scroll only - no API dependencies
 */

const { chromium } = require('playwright');

const TARGET_URL = 'https://arbitragevault.netlify.app';
const MOBILE_VIEWPORT = { width: 375, height: 667 };

async function closeModal(page) {
  try {
    const btn = page.locator('button:has-text("Passer")').first();
    if (await btn.isVisible({ timeout: 2000 })) {
      await btn.click();
      await page.waitForTimeout(500);
    }
  } catch {}
}

(async () => {
  console.log('='.repeat(60));
  console.log('TEST: HORIZONTAL SCROLL CHECK (NO API)');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();
  await page.setViewportSize(MOBILE_VIEWPORT);

  const results = { passed: 0, failed: 0 };

  // Test pages without API calls
  const pages = [
    { name: 'Dashboard', url: '/' },
    { name: 'Analyse Manuelle', url: '/analyse' },
    { name: 'Niche Discovery', url: '/niche-discovery' },
    { name: 'Configuration', url: '/config' },
  ];

  for (const p of pages) {
    await page.goto(`${TARGET_URL}${p.url}`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
    await closeModal(page);

    const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientW = await page.evaluate(() => document.documentElement.clientWidth);
    const hasScroll = scrollW > clientW + 5;

    if (hasScroll) {
      console.log(`[FAIL] ${p.name}: scroll=${scrollW}, client=${clientW}, overflow=${scrollW - clientW}px`);
      results.failed++;
      await page.screenshot({ path: `C:/Users/azizt/AppData/Local/Temp/pw-scroll-${p.name.replace(/\s/g, '-')}.png`, fullPage: true });
    } else {
      console.log(`[OK] ${p.name}: no horizontal scroll`);
      results.passed++;
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`RESULTS: ${results.passed}/${results.passed + results.failed} passed`);
  console.log('='.repeat(60));

  await browser.close();
})();
