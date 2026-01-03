const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  console.log('='.repeat(60));
  console.log('TEST 1: AutoSourcing - Strategies Tab');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');
    console.log('Page AutoSourcing loaded');

    // Click on a strategy button (Textbook)
    const strategyButton = page.locator('button:has-text("Textbook")').first();
    if (await strategyButton.isVisible({ timeout: 5000 })) {
      console.log('Textbook strategy button found, clicking...');
      await strategyButton.click();

      // Wait for products to load
      await page.waitForTimeout(5000);
      await page.screenshot({ path: 'e2e-test1-autosourcing-after-click.png', fullPage: true });

      // Check if products appear
      const productRows = page.locator('table tbody tr');
      const count = await productRows.count();
      if (count > 0) {
        console.log(`TEST 1 RESULT: PASS - ${count} products loaded`);
      } else {
        // Check for loading or error state
        const errorEl = page.locator('text=Une erreur est survenue');
        if (await errorEl.isVisible({ timeout: 2000 })) {
          console.log('TEST 1 RESULT: FAIL - Error message displayed');
        } else {
          console.log('TEST 1 RESULT: FAIL - No products and no error');
        }
      }
    } else {
      console.log('TEST 1 RESULT: FAIL - Textbook button not found');
    }
  } catch (e) {
    console.log('TEST 1 ERROR:', e.message);
    await page.screenshot({ path: 'e2e-test1-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TEST 2: Analyse Manuelle - Enter ASIN and Analyze');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/analyse`);
    await page.waitForLoadState('networkidle');
    console.log('Page Analyse Manuelle loaded');

    await page.screenshot({ path: 'e2e-test2-analyse-initial.png', fullPage: true });

    // Find textarea for ASINs
    const textarea = page.locator('textarea');
    if (await textarea.isVisible({ timeout: 5000 })) {
      console.log('Textarea found, entering ASIN...');
      await textarea.fill('0593655036');
      await page.waitForTimeout(500);

      // Find and click Valider button
      const validerButton = page.locator('button:has-text("Valider")');
      if (await validerButton.isVisible({ timeout: 3000 })) {
        console.log('Clicking Valider button...');
        await validerButton.click();
        await page.waitForTimeout(1000);

        await page.screenshot({ path: 'e2e-test2-after-valider.png', fullPage: true });

        // Find and click Lancer analyse
        const lancerButton = page.locator('button:has-text("Lancer")');
        if (await lancerButton.isVisible({ timeout: 3000 })) {
          const isDisabled = await lancerButton.isDisabled();
          console.log('Lancer button disabled=' + isDisabled);

          if (!isDisabled) {
            console.log('Clicking Lancer analyse...');
            await lancerButton.click();
            await page.waitForTimeout(10000); // Wait for API call

            await page.screenshot({ path: 'e2e-test2-after-analyse.png', fullPage: true });

            // Check for results
            const resultTable = page.locator('table tbody tr');
            const count = await resultTable.count();
            if (count > 0) {
              console.log(`TEST 2 RESULT: PASS - ${count} products analyzed`);
            } else {
              console.log('TEST 2 RESULT: PARTIAL - Analysis launched but no results visible');
            }
          } else {
            console.log('TEST 2 RESULT: FAIL - Lancer button is disabled');
          }
        } else {
          console.log('TEST 2 RESULT: FAIL - Lancer button not found');
        }
      } else {
        console.log('TEST 2 RESULT: FAIL - Valider button not found');
      }
    } else {
      console.log('TEST 2 RESULT: FAIL - Textarea not found');
    }
  } catch (e) {
    console.log('TEST 2 ERROR:', e.message);
    await page.screenshot({ path: 'e2e-test2-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TEST 3: Niche Discovery - Select strategy and view products');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');
    console.log('Page Niche Discovery loaded');

    await page.screenshot({ path: 'e2e-test3-niche-initial.png', fullPage: true });

    // Find strategy button
    const strategyBtn = page.locator('button:has-text("Textbook")').first();
    if (await strategyBtn.isVisible({ timeout: 5000 })) {
      console.log('Textbook button found, clicking...');
      await strategyBtn.click();

      // Wait for products to load
      await page.waitForTimeout(15000);
      await page.screenshot({ path: 'e2e-test3-after-strategy.png', fullPage: true });

      // Check for products
      const products = page.locator('table tbody tr');
      const count = await products.count();
      if (count > 0) {
        console.log(`TEST 3 RESULT: PASS - ${count} products found`);
      } else {
        const errorEl = page.locator('text=Une erreur est survenue');
        if (await errorEl.isVisible({ timeout: 2000 })) {
          console.log('TEST 3 RESULT: FAIL - Error message displayed');
        } else {
          console.log('TEST 3 RESULT: FAIL - No products loaded');
        }
      }
    } else {
      console.log('TEST 3 RESULT: FAIL - Textbook button not found');
    }
  } catch (e) {
    console.log('TEST 3 ERROR:', e.message);
    await page.screenshot({ path: 'e2e-test3-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TESTS COMPLETED');
  console.log('='.repeat(60));

  await browser.close();
})();
