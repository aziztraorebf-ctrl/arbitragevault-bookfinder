/**
 * Debug horizontal scroll source for Analyse Manuelle
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
  console.log('DEBUG: Analyse Manuelle scroll');

  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();
  await page.setViewportSize(MOBILE_VIEWPORT);

  await page.goto(`${TARGET_URL}/analyse`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1000);
  await closeModal(page);

  const scrollInfo = await page.evaluate(() => {
    const html = document.documentElement;
    const result = {
      documentScrollWidth: html.scrollWidth,
      documentClientWidth: html.clientWidth,
      overflow: html.scrollWidth - html.clientWidth,
      offendingElements: []
    };

    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > html.clientWidth + 2) {
        let selector = el.tagName.toLowerCase();
        if (el.id) selector += '#' + el.id;
        if (el.className && typeof el.className === 'string') {
          selector += '.' + el.className.split(' ').slice(0, 3).join('.');
        }

        result.offendingElements.push({
          selector: selector,
          right: Math.round(rect.right),
          overflow: Math.round(rect.right - html.clientWidth),
          width: Math.round(rect.width),
          text: el.textContent?.slice(0, 30) || ''
        });
      }
    });

    result.offendingElements.sort((a, b) => b.overflow - a.overflow);
    result.offendingElements = result.offendingElements.slice(0, 10);

    return result;
  });

  console.log(`Overflow: ${scrollInfo.overflow}px`);
  console.log('\nTop offending elements:');
  scrollInfo.offendingElements.forEach((el, i) => {
    console.log(`${i + 1}. ${el.selector}`);
    console.log(`   Right: ${el.right}px, Width: ${el.width}px, Overflow: ${el.overflow}px`);
  });

  await browser.close();
})();
