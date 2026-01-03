const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  console.log('='.repeat(60));
  console.log('TEST 1: Niche Discovery - Verifier Button');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');
    console.log('Page Niche Discovery chargee');

    // Screenshot initial
    await page.screenshot({ path: 'test1-niche-initial.png', fullPage: true });
    console.log('Screenshot: test1-niche-initial.png');

    // Chercher un bouton de strategie Textbook
    const textbookButton = page.locator('button:has-text("Textbook")').first();
    if (await textbookButton.isVisible({ timeout: 5000 })) {
      console.log('Bouton Textbook trouve, clic...');
      await textbookButton.click();

      // Attendre le chargement (spinner ou resultats)
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'test1-niche-after-click.png', fullPage: true });
      console.log('Screenshot apres clic: test1-niche-after-click.png');

      // Attendre que les produits apparaissent (table ou cards)
      try {
        await page.waitForSelector('table tbody tr, [data-testid="product-card"]', { timeout: 30000 });
        console.log('Produits charges!');

        // Chercher le bouton Verifier
        const verifierButton = page.locator('button:has-text("Verifier")').first();
        if (await verifierButton.isVisible({ timeout: 5000 })) {
          console.log('Bouton Verifier trouve, clic...');
          await verifierButton.click();
          await page.waitForTimeout(3000);
          await page.screenshot({ path: 'test1-niche-verification.png', fullPage: true });
          console.log('Screenshot apres verification: test1-niche-verification.png');
          console.log('TEST 1 RESULT: PASSE - Bouton Verifier clique');
        } else {
          console.log('TEST 1 RESULT: ECHEC - Bouton Verifier non trouve');
        }
      } catch (e) {
        console.log('TEST 1 RESULT: ECHEC - Produits non charges apres 30s');
        await page.screenshot({ path: 'test1-niche-error.png', fullPage: true });
      }
    } else {
      console.log('TEST 1 RESULT: ECHEC - Bouton Textbook non trouve');
    }
  } catch (e) {
    console.log('TEST 1 ERROR:', e.message);
    await page.screenshot({ path: 'test1-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TEST 2: AutoSourcing - Onglet Analyse Manuelle');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');
    console.log('Page AutoSourcing chargee');

    await page.screenshot({ path: 'test2-autosourcing-initial.png', fullPage: true });
    console.log('Screenshot: test2-autosourcing-initial.png');

    // Cliquer sur l'onglet "Analyse Manuelle"
    const analyseTab = page.locator('button:has-text("Analyse Manuelle")');
    if (await analyseTab.isVisible({ timeout: 5000 })) {
      console.log('Onglet Analyse Manuelle trouve, clic...');
      await analyseTab.click();
      await page.waitForTimeout(1000);

      // Entrer un ASIN dans le textarea
      const textarea = page.locator('textarea');
      if (await textarea.isVisible({ timeout: 3000 })) {
        console.log('Textarea trouve, saisie ASIN...');
        await textarea.fill('0593655036');
        await page.waitForTimeout(500);

        await page.screenshot({ path: 'test2-autosourcing-asin-entered.png', fullPage: true });
        console.log('Screenshot: test2-autosourcing-asin-entered.png');

        // Chercher le bouton Analyser
        const analyzerButton = page.locator('button:has-text("Analyser")');
        if (await analyzerButton.isVisible({ timeout: 3000 })) {
          const isDisabled = await analyzerButton.isDisabled();
          console.log('Bouton Analyser trouve, disabled=' + isDisabled);

          if (!isDisabled) {
            console.log('Clic sur Analyser...');
            await analyzerButton.click();
            await page.waitForTimeout(5000);
            await page.screenshot({ path: 'test2-autosourcing-after-analyze.png', fullPage: true });
            console.log('Screenshot apres analyse: test2-autosourcing-after-analyze.png');
            console.log('TEST 2 RESULT: PASSE - Analyse lancee');
          } else {
            console.log('TEST 2 RESULT: ECHEC - Bouton Analyser desactive');
          }
        } else {
          console.log('TEST 2 RESULT: ECHEC - Bouton Analyser non trouve');
        }
      } else {
        console.log('TEST 2 RESULT: ECHEC - Textarea non trouve');
      }
    } else {
      console.log('TEST 2 RESULT: ECHEC - Onglet Analyse Manuelle non trouve');
    }
  } catch (e) {
    console.log('TEST 2 ERROR:', e.message);
    await page.screenshot({ path: 'test2-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TEST 3: Analyse Manuelle - Valider ASINs puis Lancer analyse');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/analyse-manuelle`);
    await page.waitForLoadState('networkidle');
    console.log('Page Analyse Manuelle chargee');

    await page.screenshot({ path: 'test3-analyse-initial.png', fullPage: true });
    console.log('Screenshot: test3-analyse-initial.png');

    // Chercher le textarea pour les ASINs
    const textarea = page.locator('textarea');
    if (await textarea.isVisible({ timeout: 5000 })) {
      console.log('Textarea trouve, saisie ASIN...');
      await textarea.fill('0593655036, B08PGW1HW');
      await page.waitForTimeout(500);

      // Chercher le bouton "Valider ASINs"
      const validerButton = page.locator('button:has-text("Valider")');
      if (await validerButton.isVisible({ timeout: 3000 })) {
        const isDisabled = await validerButton.isDisabled();
        console.log('Bouton Valider trouve, disabled=' + isDisabled);

        if (!isDisabled) {
          console.log('Clic sur Valider ASINs...');
          await validerButton.click();
          await page.waitForTimeout(1000);

          await page.screenshot({ path: 'test3-analyse-after-valider.png', fullPage: true });
          console.log('Screenshot apres validation: test3-analyse-after-valider.png');

          // Verifier si le bouton "Lancer analyse" est maintenant actif
          const lancerButton = page.locator('button:has-text("Lancer analyse")');
          if (await lancerButton.isVisible({ timeout: 3000 })) {
            const lancerDisabled = await lancerButton.isDisabled();
            console.log('Bouton Lancer analyse trouve, disabled=' + lancerDisabled);

            if (!lancerDisabled) {
              console.log('Clic sur Lancer analyse...');
              await lancerButton.click();
              await page.waitForTimeout(5000);
              await page.screenshot({ path: 'test3-analyse-after-lancer.png', fullPage: true });
              console.log('Screenshot apres lancement: test3-analyse-after-lancer.png');
              console.log('TEST 3 RESULT: PASSE - Analyse lancee');
            } else {
              console.log('TEST 3 RESULT: ECHEC - Bouton Lancer analyse toujours desactive apres validation');
            }
          } else {
            console.log('TEST 3 RESULT: ECHEC - Bouton Lancer analyse non trouve');
          }
        } else {
          console.log('TEST 3 RESULT: ECHEC - Bouton Valider desactive');
        }
      } else {
        console.log('TEST 3 RESULT: ECHEC - Bouton Valider non trouve');
      }
    } else {
      console.log('TEST 3 RESULT: ECHEC - Textarea non trouve');
    }
  } catch (e) {
    console.log('TEST 3 ERROR:', e.message);
    await page.screenshot({ path: 'test3-error.png', fullPage: true });
  }

  console.log('\n' + '='.repeat(60));
  console.log('TESTS TERMINES');
  console.log('='.repeat(60));

  await browser.close();
})();
