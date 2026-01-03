const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:5173';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  console.log('='.repeat(60));
  console.log('TEST: Analyse Manuelle (route /analyse)');
  console.log('='.repeat(60));

  try {
    await page.goto(`${TARGET_URL}/analyse`);
    await page.waitForLoadState('networkidle');
    console.log('Page Analyse chargee');

    await page.screenshot({ path: 'test-analyse-page.png', fullPage: true });
    console.log('Screenshot: test-analyse-page.png');

    // Chercher le textarea pour les ASINs
    const textarea = page.locator('textarea');
    if (await textarea.isVisible({ timeout: 5000 })) {
      console.log('Textarea trouve, saisie ASIN...');
      await textarea.fill('0593655036');
      await page.waitForTimeout(500);

      await page.screenshot({ path: 'test-analyse-asin-entered.png', fullPage: true });

      // Chercher le bouton "Valider ASINs"
      const validerButton = page.locator('button:has-text("Valider")');
      if (await validerButton.isVisible({ timeout: 3000 })) {
        const isDisabled = await validerButton.isDisabled();
        console.log('Bouton Valider trouve, disabled=' + isDisabled);

        if (!isDisabled) {
          console.log('Clic sur Valider ASINs...');
          await validerButton.click();
          await page.waitForTimeout(1000);

          await page.screenshot({ path: 'test-analyse-after-valider.png', fullPage: true });
          console.log('Screenshot apres validation: test-analyse-after-valider.png');

          // Verifier si le bouton "Lancer analyse" est maintenant actif
          const lancerButton = page.locator('button:has-text("Lancer analyse")');
          if (await lancerButton.isVisible({ timeout: 3000 })) {
            const lancerDisabled = await lancerButton.isDisabled();
            console.log('Bouton Lancer analyse trouve, disabled=' + lancerDisabled);

            if (!lancerDisabled) {
              console.log('Clic sur Lancer analyse...');
              await lancerButton.click();

              // Attendre plus longtemps pour l'API
              console.log('Attente de la reponse API (15s max)...');
              await page.waitForTimeout(15000);

              await page.screenshot({ path: 'test-analyse-after-lancer.png', fullPage: true });
              console.log('Screenshot apres lancement: test-analyse-after-lancer.png');
              console.log('TEST RESULT: PASSE - Analyse lancee');
            } else {
              console.log('TEST RESULT: ECHEC - Bouton Lancer analyse toujours desactive');
            }
          } else {
            console.log('TEST RESULT: ECHEC - Bouton Lancer analyse non trouve');
          }
        } else {
          console.log('TEST RESULT: ECHEC - Bouton Valider desactive');
        }
      } else {
        console.log('Bouton Valider non trouve, cherchons ce qui existe...');
        const buttons = await page.locator('button').allTextContents();
        console.log('Boutons sur la page:', buttons);
      }
    } else {
      console.log('Textarea non trouve, cherchons ce qui existe...');
      const inputs = await page.locator('input, textarea').count();
      console.log('Nombre d\'inputs/textareas:', inputs);
    }
  } catch (e) {
    console.log('TEST ERROR:', e.message);
    await page.screenshot({ path: 'test-analyse-error.png', fullPage: true });
  }

  await browser.close();
})();
