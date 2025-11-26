// Robustness Tests - Randomized Data
// Valide que le systeme fonctionne avec donnees variees
const { test, expect } = require('@playwright/test');
const { getRandomASIN, getRandomASINs, getRandomJobConfig } = require('../test-utils/random-data');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

// Minimum token balance required for tests
const MIN_TOKENS_FOR_ROBUSTNESS = 200;

test.describe('Robustness Tests - Randomized Data', () => {
  test('Should handle multiple random ASINs in batch', async ({ request }) => {
    console.log('Testing batch analysis with 5 random ASINs...');

    // Check token balance first
    const healthResponse = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    if (healthResponse.status() === 200) {
      const health = await healthResponse.json();
      const tokenBalance = health.tokens_balance || 0;

      if (tokenBalance < MIN_TOKENS_FOR_ROBUSTNESS) {
        console.log(`Skipping test - insufficient tokens (${tokenBalance} < ${MIN_TOKENS_FOR_ROBUSTNESS})`);
        return;
      }

      console.log(`Proceeding with robustness test (balance: ${tokenBalance})`);
    }

    // Generate 5 random ASINs from different categories
    const testSeed = `robustness-${Date.now()}`;
    const randomASINs = [
      getRandomASIN(`${testSeed}-1`, 'books_low_bsr'),
      getRandomASIN(`${testSeed}-2`, 'books_medium_bsr'),
      getRandomASIN(`${testSeed}-3`, 'electronics'),
      getRandomASIN(`${testSeed}-4`, 'books_low_bsr'),
      getRandomASIN(`${testSeed}-5`, 'media')
    ];

    console.log('Testing ASINs:', randomASINs);

    const response = await request.post(`${BACKEND_URL}/api/v1/keepa/ingest`, {
      data: {
        identifiers: randomASINs,
        config_profile: 'default',
        force_refresh: false
      },
      timeout: 120000
    });

    console.log('Batch ingest response status:', response.status());

    if (response.status() === 429) {
      console.log('HTTP 429 - tokens depleted during test execution');
      const data = await response.json();
      expect(data).toHaveProperty('detail');
      return;
    }

    expect(response.status()).toBe(200);

    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('batch_id');
    expect(data).toHaveProperty('total_items');
    expect(data.total_items).toBe(randomASINs.length);

    console.log(`Batch processed: ${data.successful}/${data.total_items} successful`);
  });

  test('Should handle random job configuration variations', async ({ request }) => {
    console.log('Testing AutoSourcing with random job config...');

    // Check token balance first
    const healthResponse = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    if (healthResponse.status() === 200) {
      const health = await healthResponse.json();
      const tokenBalance = health.tokens_balance || 0;

      if (tokenBalance < MIN_TOKENS_FOR_ROBUSTNESS) {
        console.log(`Skipping test - insufficient tokens (${tokenBalance} < ${MIN_TOKENS_FOR_ROBUSTNESS})`);
        return;
      }
    }

    // Generate random job config
    const jobConfig = getRandomJobConfig(`robustness-job-${Date.now()}`);

    console.log('Testing job config:', {
      categories: jobConfig.discovery_config.categories,
      price_range: jobConfig.discovery_config.price_range,
      bsr_range: jobConfig.discovery_config.bsr_range,
      roi_min: jobConfig.scoring_config.roi_min,
      velocity_min: jobConfig.scoring_config.velocity_min
    });

    const response = await request.post(`${BACKEND_URL}/api/v1/autosourcing/run-custom`, {
      data: jobConfig,
      timeout: 120000
    });

    console.log('AutoSourcing response status:', response.status());

    if (response.status() === 429) {
      console.log('HTTP 429 - tokens depleted during test');
      return;
    }

    if (response.status() === 401 || response.status() === 403) {
      console.log('Authentication required - skipping test');
      return;
    }

    // Accept 200 or 202 (async job)
    expect([200, 202]).toContain(response.status());

    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('profile_name');

    console.log(`Job created: ${data.id}, status: ${data.status}`);
  });

  test('Should handle edge case ASINs across BSR spectrum', async ({ request }) => {
    console.log('Testing edge case ASINs (low, medium, high BSR)...');

    const healthResponse = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    if (healthResponse.status() === 200) {
      const health = await healthResponse.json();
      const tokenBalance = health.tokens_balance || 0;

      if (tokenBalance < MIN_TOKENS_FOR_ROBUSTNESS) {
        console.log(`Skipping test - insufficient tokens (${tokenBalance} < ${MIN_TOKENS_FOR_ROBUSTNESS})`);
        return;
      }
    }

    const testSeed = `edge-case-${Date.now()}`;
    const edgeCaseASINs = [
      getRandomASIN(`${testSeed}-low`, 'books_low_bsr'),
      getRandomASIN(`${testSeed}-medium`, 'books_medium_bsr'),
      getRandomASIN(`${testSeed}-high`, 'books_high_bsr')
    ];

    console.log('Testing edge case ASINs:', edgeCaseASINs);

    for (const asin of edgeCaseASINs) {
      const response = await request.get(`${BACKEND_URL}/api/v1/keepa/${asin}/metrics`, {
        params: {
          config_profile: 'default',
          force_refresh: false
        },
        timeout: 60000
      });

      console.log(`ASIN ${asin} response: ${response.status()}`);

      if (response.status() === 429) {
        console.log('HTTP 429 - stopping edge case testing');
        break;
      }

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('asin');
        expect(data.asin).toBe(asin);

        console.log(`ASIN ${asin} analyzed successfully`);
      }
    }
  });
});
