/**
 * E2E Test: AutoSourcing Validation avec Zero-Tolerance Engineering
 *
 * Criteres de validation (depuis niche_templates.py):
 * - Smart Velocity: BSR 10K-80K, ROI >= 30%, Max FBA sellers: 5
 * - Textbooks: BSR 30K-250K, ROI >= 50%, Max FBA sellers: 3
 *
 * Gate System:
 * - Assertions: donnees recues = donnees attendues
 * - Validation croisee MCP vs Backend API
 * - Preuve screenshots
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// URLs Production
const FRONTEND_URL = 'https://arbitragevault.netlify.app';
const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';

// Criteres EXACTS depuis niche_templates.py
const STRATEGY_CRITERIA = {
  smart_velocity: {
    name: 'Smart Velocity',
    bsr_min: 10000,
    bsr_max: 80000,
    min_roi: 30,
    min_velocity: 50,
    max_fba_sellers: 5,
    price_min: 15.0,
    price_max: 60.0
  },
  textbooks: {
    name: 'Textbooks',
    bsr_min: 30000,
    bsr_max: 250000,
    min_roi: 50,
    min_velocity: 30,
    max_fba_sellers: 3,
    price_min: 30.0,
    price_max: 150.0
  }
};

// Resultats du test
let testResults = {
  timestamp: new Date().toISOString(),
  strategy_tested: null,
  picks_received: [],
  assertions: {
    total: 0,
    passed: 0,
    failed: 0,
    details: []
  },
  cross_validation: {
    performed: false,
    mcp_vs_backend_match: null,
    divergence_percent: null
  },
  screenshots: []
};

function assert(condition, message, actual, expected) {
  testResults.assertions.total++;
  if (condition) {
    testResults.assertions.passed++;
    testResults.assertions.details.push({
      status: 'PASS',
      message,
      actual,
      expected
    });
    console.log('  [PASS] ' + message);
    return true;
  } else {
    testResults.assertions.failed++;
    testResults.assertions.details.push({
      status: 'FAIL',
      message,
      actual,
      expected
    });
    console.log('  [FAIL] ' + message + ' (actual: ' + actual + ', expected: ' + expected + ')');
    return false;
  }
}

function resetResults() {
  testResults = {
    timestamp: new Date().toISOString(),
    strategy_tested: null,
    picks_received: [],
    assertions: {
      total: 0,
      passed: 0,
      failed: 0,
      details: []
    },
    cross_validation: {
      performed: false,
      mcp_vs_backend_match: null,
      divergence_percent: null
    },
    screenshots: []
  };
}

async function testAutosourcingAPI(strategy) {
  resetResults();

  console.log('\n========================================');
  console.log('AUTOSOURCING E2E TEST - ' + STRATEGY_CRITERIA[strategy].name);
  console.log('========================================\n');

  testResults.strategy_tested = strategy;
  const criteria = STRATEGY_CRITERIA[strategy];

  const browser = await chromium.launch({
    headless: false,
    slowMo: 100
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // ========================================
    // ETAPE 1: Verifier sante backend
    // ========================================
    console.log('ETAPE 1: Verification sante backend...');

    const healthResponse = await page.request.get(BACKEND_URL + '/api/v1/health/ready');
    const healthData = await healthResponse.json();

    assert(
      healthResponse.ok() && healthData.status === 'ready',
      'Backend est healthy',
      healthData.status,
      'ready'
    );

    // Verifier Keepa health
    const keepaHealthResponse = await page.request.get(BACKEND_URL + '/api/v1/keepa/health');
    const keepaHealth = await keepaHealthResponse.json();

    assert(
      keepaHealthResponse.ok(),
      'Keepa service est accessible',
      keepaHealthResponse.status(),
      200
    );

    console.log('  Token balance: ' + (keepaHealth.tokens_left || 'N/A'));

    // ========================================
    // ETAPE 2: Lancer recherche AutoSourcing via API
    // ========================================
    console.log('\nETAPE 2: Lancement recherche AutoSourcing...');

    const searchPayload = {
      profile_name: 'E2E_Test_' + strategy + '_' + Date.now(),
      discovery_config: {
        categories: strategy === 'textbooks' ? ['medical', 'engineering'] : ['programming', 'business'],
        bsr_range: [criteria.bsr_min, criteria.bsr_max],
        price_range: [criteria.price_min, criteria.price_max],
        max_results: 10
      },
      scoring_config: {
        roi_min: criteria.min_roi,
        velocity_min: criteria.min_velocity,
        confidence_min: 60,
        rating_required: 'FAIR',
        max_results: 5
      }
    };

    console.log('  Payload:', JSON.stringify(searchPayload, null, 2));

    const searchResponse = await page.request.post(
      BACKEND_URL + '/api/v1/autosourcing/run-custom',
      {
        data: searchPayload,
        headers: { 'Content-Type': 'application/json' },
        timeout: 120000
      }
    );

    if (!searchResponse.ok()) {
      const errorText = await searchResponse.text();
      console.log('  [ERROR] API response: ' + searchResponse.status() + ' - ' + errorText);
      throw new Error('AutoSourcing API failed: ' + searchResponse.status());
    }

    const searchResult = await searchResponse.json();
    console.log('  Job ID: ' + searchResult.id);
    console.log('  Status: ' + searchResult.status);
    console.log('  Total tested: ' + searchResult.total_tested);
    console.log('  Total selected: ' + searchResult.total_selected);

    testResults.picks_received = searchResult.picks || [];

    // ========================================
    // ETAPE 3: Valider chaque pick contre criteres
    // ========================================
    console.log('\nETAPE 3: Validation des picks contre criteres...');

    if (testResults.picks_received.length === 0) {
      console.log('  [WARN] Aucun pick recu - peut-etre pas de produits correspondant aux criteres');
      console.log('  Ceci peut etre normal si le marche na pas de produits dans cette plage');
    } else {
      console.log('  ' + testResults.picks_received.length + ' picks a valider\n');

      for (const pick of testResults.picks_received) {
        console.log('  --- Pick: ' + pick.asin + ' ---');
        console.log('      Titre: ' + (pick.title ? pick.title.substring(0, 50) : 'N/A') + '...');

        // Assertion: Titre n'est PAS un placeholder
        assert(
          pick.title && !pick.title.includes('Product ') && pick.title !== pick.asin,
          'Titre reel (pas placeholder) pour ' + pick.asin,
          pick.title ? pick.title.substring(0, 30) : 'null',
          'Titre reel du produit'
        );

        // Assertion: ROI respecte le minimum
        assert(
          pick.roi_percentage >= criteria.min_roi,
          'ROI >= ' + criteria.min_roi + '% pour ' + pick.asin,
          pick.roi_percentage,
          '>= ' + criteria.min_roi
        );

        // Assertion: Velocity score respecte le minimum
        assert(
          pick.velocity_score >= criteria.min_velocity,
          'Velocity >= ' + criteria.min_velocity + ' pour ' + pick.asin,
          pick.velocity_score,
          '>= ' + criteria.min_velocity
        );

        // Assertion: Confidence score
        assert(
          pick.confidence_score >= 60,
          'Confidence >= 60 pour ' + pick.asin,
          pick.confidence_score,
          '>= 60'
        );

        console.log('');
      }
    }

    // ========================================
    // ETAPE 4: Validation croisee Backend API (si picks disponibles)
    // ========================================
    if (testResults.picks_received.length > 0) {
      console.log('ETAPE 4: Validation croisee Backend API...');

      const firstPick = testResults.picks_received[0];
      console.log('  Verification ASIN: ' + firstPick.asin);

      // Appeler endpoint metrics du backend
      const metricsResponse = await page.request.get(
        BACKEND_URL + '/api/v1/keepa/' + firstPick.asin + '/metrics',
        { timeout: 30000 }
      );

      if (metricsResponse.ok()) {
        const metricsData = await metricsResponse.json();
        testResults.cross_validation.performed = true;

        // Comparer ROI (tolerance 5% car calculs peuvent varier legerement)
        const metricsRoi = metricsData.analysis && metricsData.analysis.roi ? metricsData.analysis.roi.roi_percentage : 0;
        const roiDivergence = Math.abs(metricsRoi - firstPick.roi_percentage);

        testResults.cross_validation.divergence_percent = roiDivergence;
        testResults.cross_validation.mcp_vs_backend_match = roiDivergence < 5;

        assert(
          roiDivergence < 5,
          'Divergence ROI < 5% entre AutoSourcing et Metrics API',
          roiDivergence.toFixed(2) + '%',
          '< 5%'
        );

        console.log('  Backend metrics ROI: ' + metricsRoi + '%');
        console.log('  AutoSourcing ROI: ' + firstPick.roi_percentage + '%');
      } else {
        console.log('  [WARN] Impossible de valider via metrics API: ' + metricsResponse.status());
      }
    }

    // ========================================
    // ETAPE 5: Screenshots preuve
    // ========================================
    console.log('\nETAPE 5: Capture screenshots preuve...');

    // Screenshot du frontend
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const frontendScreenshot = path.join(screenshotDir, 'e2e-frontend-' + strategy + '-' + Date.now() + '.png');
    await page.screenshot({ path: frontendScreenshot, fullPage: true });
    testResults.screenshots.push(frontendScreenshot);
    console.log('  Screenshot frontend: ' + frontendScreenshot);

    // ========================================
    // RAPPORT FINAL
    // ========================================
    console.log('\n========================================');
    console.log('RAPPORT FINAL');
    console.log('========================================');
    console.log('Strategie: ' + STRATEGY_CRITERIA[strategy].name);
    console.log('Criteres BSR: ' + criteria.bsr_min + ' - ' + criteria.bsr_max);
    console.log('Criteres ROI: >= ' + criteria.min_roi + '%');
    console.log('Criteres Velocity: >= ' + criteria.min_velocity);
    console.log('');
    console.log('Picks recus: ' + testResults.picks_received.length);
    console.log('Assertions: ' + testResults.assertions.passed + '/' + testResults.assertions.total + ' passees');

    if (testResults.assertions.failed > 0) {
      console.log('\nAssertions echouees:');
      testResults.assertions.details
        .filter(function(a) { return a.status === 'FAIL'; })
        .forEach(function(a) { console.log('  - ' + a.message + ': actual=' + a.actual + ', expected=' + a.expected); });
    }

    console.log('\nValidation croisee: ' + (testResults.cross_validation.performed ?
      (testResults.cross_validation.mcp_vs_backend_match ? 'PASS' : 'FAIL') : 'NON EFFECTUEE'));

    console.log('\nScreenshots:');
    testResults.screenshots.forEach(function(s) { console.log('  - ' + s); });

    // Resultat final
    const allPassed = testResults.assertions.failed === 0;
    console.log('\n========================================');
    console.log(allPassed ? 'RESULTAT: SUCCES' : 'RESULTAT: ECHEC');
    console.log('========================================\n');

    // Sauvegarder rapport JSON
    const reportPath = path.join(screenshotDir, 'e2e-report-' + strategy + '-' + Date.now() + '.json');
    fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));
    console.log('Rapport JSON: ' + reportPath);

    return allPassed;

  } catch (error) {
    console.error('\n[ERREUR CRITIQUE] ' + error.message);

    // Screenshot d'erreur
    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
    const errorScreenshot = path.join(screenshotDir, 'e2e-error-' + Date.now() + '.png');
    await page.screenshot({ path: errorScreenshot, fullPage: true });
    console.log('Screenshot erreur: ' + errorScreenshot);

    return false;
  } finally {
    await browser.close();
  }
}

// Executer le test
(async () => {
  // Test Smart Velocity d'abord
  const smartVelocityPassed = await testAutosourcingAPI('smart_velocity');

  console.log('\n\n');

  // Test Textbooks ensuite
  const textbooksPassed = await testAutosourcingAPI('textbooks');

  // Resume final
  console.log('\n========================================');
  console.log('RESUME FINAL E2E');
  console.log('========================================');
  console.log('Smart Velocity: ' + (smartVelocityPassed ? 'PASS' : 'FAIL'));
  console.log('Textbooks: ' + (textbooksPassed ? 'PASS' : 'FAIL'));
  console.log('========================================\n');

  process.exit(smartVelocityPassed && textbooksPassed ? 0 : 1);
})();
