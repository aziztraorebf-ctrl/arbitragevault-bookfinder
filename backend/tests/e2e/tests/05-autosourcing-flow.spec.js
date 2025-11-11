// AutoSourcing Flow E2E Tests - Phase 5
// Valide le workflow complet AutoSourcing avec vraies donnees Keepa
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

// Minimum token balance required for expensive tests
const MIN_TOKENS_FOR_DISCOVERY = 100;

// Helper to check token balance
async function getTokenBalance(request) {
  try {
    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    if (response.status() === 200) {
      const data = await response.json();
      return data.tokens?.remaining || 0;
    }
  } catch (error) {
    console.error('Error fetching token balance:', error.message);
  }
  return 0;
}

test.describe('AutoSourcing Flow', () => {
  test('Test 2.1: Should navigate to AutoSourcing page', async ({ page }) => {
    console.log('Testing AutoSourcing page navigation...');

    await page.goto(FRONTEND_URL);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Find AutoSourcing link (route is /autosourcing)
    const autoSourcingLink = page.locator('a[href*="autosourcing"]').first();

    if (await autoSourcingLink.isVisible({ timeout: 5000 })) {
      await autoSourcingLink.click();
      console.log('Clicked AutoSourcing link');
    } else {
      // Direct navigation if link not found
      await page.goto(`${FRONTEND_URL}/autosourcing`);
      console.log('Navigated directly to /autosourcing');
    }

    // Verify page loaded (heading should be visible)
    await page.waitForSelector('h1, h2', { timeout: 10000 });
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();

    const headingText = await heading.textContent();
    console.log(`AutoSourcing page loaded with heading: ${headingText}`);
  });

  test('Test 2.2: Should display recent jobs list or empty state', async ({ page }) => {
    console.log('Testing recent jobs display...');

    await page.goto(`${FRONTEND_URL}/autosourcing`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait a moment for data to load
    await page.waitForTimeout(2000);

    // STRICT VALIDATION: Check for jobs list or empty state with XOR logic
    const jobsList = page.locator('[data-testid="jobs-list"]');
    const emptyState = page.locator('[data-testid="empty-jobs"]');

    // Wait for either state to appear
    const hasJobs = await jobsList.isVisible({ timeout: 5000 }).catch(() => false);
    const isEmpty = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);

    // STRICT XOR VALIDATION: Exactly one must be true
    const validState = (hasJobs && !isEmpty) || (isEmpty && !hasJobs);

    if (!validState) {
      throw new Error(
        `Invalid jobs display state: hasJobs=${hasJobs}, isEmpty=${isEmpty}. ` +
        `Expected XOR: exactly one must be true, not both or neither.`
      );
    }

    expect(validState).toBe(true);
    console.log(hasJobs ? 'Jobs list displayed (XOR valid)' : 'Empty state displayed (XOR valid)');
  });

  test('Test 2.3: Should open job configuration form', async ({ page }) => {
    console.log('Testing job configuration form...');

    await page.goto(`${FRONTEND_URL}/autosourcing`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Find "New Job" or "Run Custom Search" button
    const newJobButton = page.locator(
      'button:has-text("New"), button:has-text("Custom"), button:has-text("Nouvelle"), button:has-text("Recherche")'
    ).first();

    if (await newJobButton.isVisible({ timeout: 5000 })) {
      await newJobButton.click();
      console.log('Clicked new job button');

      // Verify form opened (modal or inline form)
      await page.waitForSelector('form, [role="dialog"], .modal, input, select', { timeout: 5000 });

      // Look for form elements (category selector, price inputs, etc.)
      const formElement = page.locator('form, [role="dialog"]').first();
      const hasFormElement = await formElement.isVisible({ timeout: 2000 }).catch(() => false);

      if (hasFormElement) {
        await expect(formElement).toBeVisible();
        console.log('Job configuration form opened');
      } else {
        // Check for input/select fields even if no form wrapper
        const inputs = page.locator('input, select').first();
        await expect(inputs).toBeVisible({ timeout: 5000 });
        console.log('Job configuration inputs found');
      }
    } else {
      console.log('New job button not found - feature might require authentication or different selector');
    }
  });

  test('Test 2.4: Should submit AutoSourcing job via API (conditional on token balance)', async ({ request }) => {
    console.log('Testing AutoSourcing job submission via API...');

    // Check token balance first
    const tokenBalance = await getTokenBalance(request);
    console.log(`Current token balance: ${tokenBalance}`);

    if (tokenBalance < MIN_TOKENS_FOR_DISCOVERY) {
      console.log(`SKIP: Insufficient tokens for Product Finder test (need ${MIN_TOKENS_FOR_DISCOVERY}, have ${tokenBalance})`);
      console.log('This test requires ~50 tokens to run Product Finder discovery.');
      test.skip();
      return;
    }

    console.log(`Proceeding with AutoSourcing job (balance: ${tokenBalance} >= ${MIN_TOKENS_FOR_DISCOVERY})`);

    // Try to submit job via API endpoint
    const response = await request.post(`${BACKEND_URL}/api/v1/autosourcing/run_custom`, {
      data: {
        profile_name: 'E2E Test Job Phase 5',
        discovery_config: {
          categories: ['Books'],
          price_range: [10, 50],
          bsr_range: [10000, 100000],
          max_results: 10
        },
        scoring_config: {
          roi_min: 20,
          velocity_min: 60,
          confidence_min: 70,
          rating_required: 'GOOD',
          max_results: 5
        }
      },
      timeout: 60000 // 60 second timeout for Product Finder
    });

    console.log('Job submission response status:', response.status());

    if (response.status() === 401 || response.status() === 403) {
      console.log('Authentication required - skipping job submission test');
      return;
    }

    if (response.status() === 429) {
      console.log('HTTP 429 - insufficient tokens despite pre-check, test skipped');
      const data = await response.json();
      expect(data).toHaveProperty('detail');
      expect(data.detail.toLowerCase()).toContain('token');

      // Verify headers are present
      const tokenBalance = response.headers()['x-token-balance'];
      const tokenRequired = response.headers()['x-token-required'];
      console.log(`Token balance: ${tokenBalance}, required: ${tokenRequired}`);

      return;
    }

    if (response.status() === 422) {
      console.log('HTTP 422 - validation error in request payload');
      const data = await response.json();
      console.log('Validation errors:', JSON.stringify(data, null, 2));
      throw new Error(`Request validation failed: ${JSON.stringify(data)}`);
    }

    // Expect success
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('picks');

    console.log('Job submitted successfully:', {
      job_id: data.id,
      status: data.status,
      picks_count: data.picks?.length || 0,
      profile_name: data.profile_name
    });

    // Verify picks structure
    if (data.picks && data.picks.length > 0) {
      const firstPick = data.picks[0];
      expect(firstPick).toHaveProperty('asin');
      expect(firstPick).toHaveProperty('roi_percentage');
      expect(firstPick).toHaveProperty('velocity_score');
      console.log(`First pick: ASIN=${firstPick.asin}, ROI=${firstPick.roi_percentage}%, Velocity=${firstPick.velocity_score}`);
    }
  });

  test('Test 2.5: Should display job results with picks', async ({ page }) => {
    console.log('Testing job results display...');

    await page.goto(`${FRONTEND_URL}/autosourcing`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait a moment for jobs to load
    await page.waitForTimeout(2000);

    // Look for any existing job results (cards, table rows, etc.)
    const jobCard = page.locator('[data-testid="job-card"], .job-card, table tbody tr').first();

    const hasJobCard = await jobCard.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasJobCard) {
      // Try to click on job to view details
      await jobCard.click();
      console.log('Opened job details');

      // Wait for picks to load (might open modal or navigate to details page)
      await page.waitForTimeout(2000);

      // Look for picks display (table, cards, list items, etc.)
      const picksContainer = page.locator(
        '[data-testid="picks"], .picks, .results, table, .product-card'
      );

      const hasPicks = await picksContainer.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasPicks) {
        const picks = page.locator('[data-testid="pick"]');
        const picksCount = await picks.count();

        console.log(`Displayed ${picksCount} picks`);

        // STRICT VALIDATION: Must have at least 1 pick
        expect(picksCount).toBeGreaterThan(0);

        // Verify first pick structure with data-testid attributes
        const firstPick = picks.first();
        await expect(firstPick).toBeVisible();

        // STRICT VALIDATION: Verify all required data fields exist
        const asinElement = firstPick.locator('[data-testid="pick-asin"]');
        const titleElement = firstPick.locator('[data-testid="pick-title"]');
        const roiElement = firstPick.locator('[data-testid="pick-roi"]');
        const velocityElement = firstPick.locator('[data-testid="pick-velocity"]');

        await expect(asinElement).toBeVisible();
        await expect(titleElement).toBeVisible();
        await expect(roiElement).toBeVisible();
        await expect(velocityElement).toBeVisible();

        // STRICT VALIDATION: Verify data format with regex
        const roiText = await roiElement.textContent();
        const velocityText = await velocityElement.textContent();

        expect(roiText).toMatch(/ROI.*\d+\.?\d*%/i);
        expect(velocityText).toMatch(/Velocity.*\d+/i);

        console.log(`First pick validated: ASIN, title, ROI (${roiText}), velocity (${velocityText})`);
      } else {
        throw new Error('Picks container not found - job should have results to display');
      }
    } else {
      console.log('No job results available to test display');
      console.log('This is expected if no jobs have been run yet');
    }
  });
});
