/**
 * Debug horizontal scroll source
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
  console.log('DEBUG: HORIZONTAL SCROLL SOURCE FINDER');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const page = await browser.newPage();
  await page.setViewportSize(MOBILE_VIEWPORT);

  // Go to niche discovery
  await page.goto(`${TARGET_URL}/niche-discovery`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1500);
  await closeModal(page);

  // Click strategy
  const stratBtn = page.locator('button:has-text("Textbook Standard")').first();
  if (await stratBtn.isVisible({ timeout: 3000 })) {
    await stratBtn.click();
    await page.waitForTimeout(3000);
    await page.waitForSelector('text=/Explorer/i', { timeout: 60000 }).catch(() => {});
  }

  // Click Explorer
  const explorerBtn = page.locator('button:has-text("Explorer")').first();
  if (await explorerBtn.isVisible({ timeout: 5000 })) {
    await explorerBtn.click();
    await page.waitForTimeout(3000);
  }

  // Now debug scroll
  console.log('\n--- SCROLL DEBUG ---\n');

  const scrollInfo = await page.evaluate(() => {
    const body = document.body;
    const html = document.documentElement;

    const result = {
      documentScrollWidth: html.scrollWidth,
      documentClientWidth: html.clientWidth,
      bodyScrollWidth: body.scrollWidth,
      bodyClientWidth: body.clientWidth,
      overflow: html.scrollWidth - html.clientWidth,
      offendingElements: []
    };

    // Find all elements that extend beyond viewport
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > html.clientWidth + 5) {
        // Get a readable selector
        let selector = el.tagName.toLowerCase();
        if (el.id) selector += '#' + el.id;
        if (el.className && typeof el.className === 'string') {
          selector += '.' + el.className.split(' ').slice(0, 3).join('.');
        }

        result.offendingElements.push({
          selector: selector,
          right: Math.round(rect.right),
          overflow: Math.round(rect.right - html.clientWidth),
          text: el.textContent?.slice(0, 50) || ''
        });
      }
    });

    // Sort by overflow amount
    result.offendingElements.sort((a, b) => b.overflow - a.overflow);

    // Keep only top 10
    result.offendingElements = result.offendingElements.slice(0, 10);

    return result;
  });

  console.log(`Document scroll width: ${scrollInfo.documentScrollWidth}`);
  console.log(`Document client width: ${scrollInfo.documentClientWidth}`);
  console.log(`Overflow: ${scrollInfo.overflow}px`);

  console.log('\nTop offending elements:');
  scrollInfo.offendingElements.forEach((el, i) => {
    console.log(`${i + 1}. ${el.selector}`);
    console.log(`   Right: ${el.right}px, Overflow: ${el.overflow}px`);
    console.log(`   Text: "${el.text.slice(0, 40)}..."`);
  });

  await page.screenshot({ path: 'C:/Users/azizt/AppData/Local/Temp/pw-debug-scroll.png', fullPage: true });
  console.log('\nScreenshot saved to: C:/Users/azizt/AppData/Local/Temp/pw-debug-scroll.png');

  await browser.close();
})();
