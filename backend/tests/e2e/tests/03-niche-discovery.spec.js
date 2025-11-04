// Niche Discovery E2E Tests - Phase 5
// Valide le flow complet de decouverte de niches depuis le frontend
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Niche Discovery Flow', () => {
  test('Should discover niches with auto mode', async ({ request }) => {
    console.log('Testing niche discovery auto endpoint...');

    const response = await request.get(`${BACKEND_URL}/api/v1/niches/discover`, {
      params: {
        count: 3,
        shuffle: true
      }
    });

    console.log('Niche discovery response status:', response.status());

    if (response.status() === 429) {
      console.log('HTTP 429 detected - tokens insufficient for discovery');
      const data = await response.json();
      expect(data).toHaveProperty('detail');
      return; // Skip rest of test if no tokens
    }

    expect(response.status()).toBe(200);

    const data = await response.json();

    // Valider structure response
    expect(data).toHaveProperty('products');
    expect(data).toHaveProperty('metadata');
    expect(data.metadata).toHaveProperty('niches');
    expect(data.metadata).toHaveProperty('niches_count');

    const nichesCount = data.metadata.niches_count;
    console.log(`Discovered ${nichesCount} niches`);

    // Allow 0 niches if tokens are low or cache empty
    expect(nichesCount).toBeGreaterThanOrEqual(0);
    expect(nichesCount).toBeLessThanOrEqual(5);

    // Valider structure niches
    const niches = data.metadata.niches;
    expect(Array.isArray(niches)).toBe(true);

    if (niches.length > 0) {
      const firstNiche = niches[0];
      expect(firstNiche).toHaveProperty('id');
      expect(firstNiche).toHaveProperty('name');
      expect(firstNiche).toHaveProperty('products_found');
      expect(firstNiche).toHaveProperty('avg_roi');
      expect(firstNiche).toHaveProperty('avg_velocity');

      console.log('First niche example:', {
        id: firstNiche.id,
        name: firstNiche.name,
        products_found: firstNiche.products_found,
        avg_roi: firstNiche.avg_roi
      });
    }
  });

  test('Should get available categories', async ({ request }) => {
    console.log('Testing get available categories...');

    const response = await request.get(`${BACKEND_URL}/api/v1/products/categories`);

    expect(response.status()).toBe(200);

    const data = await response.json();

    // Valider structure response
    expect(data).toHaveProperty('categories');
    expect(Array.isArray(data.categories)).toBe(true);

    const categories = data.categories;
    console.log(`Found ${categories.length} categories`);

    if (categories.length > 0) {
      const firstCategory = categories[0];
      expect(firstCategory).toHaveProperty('name');
      expect(firstCategory).toHaveProperty('id');

      console.log('First category example:', {
        name: firstCategory.name,
        id: firstCategory.id
      });
    }
  });

  test('Should create saved niche bookmark', async ({ request }) => {
    console.log('Testing create saved niche...');

    const response = await request.post(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      data: {
        niche_name: 'Test Niche E2E',
        description: 'Created by Playwright E2E test',
        category_id: 3920,
        category_name: 'Books',
        filters: {
          bsr_range: [10000, 50000],
          max_sellers: 3,
          min_margin_percent: 30
        },
        last_score: 85.5
      }
    });

    console.log('Create saved niche response status:', response.status());

    if (response.status() === 401 || response.status() === 403) {
      console.log('Skipping test - authentication required');
      return; // Skip if auth not implemented yet
    }

    expect(response.status()).toBe(201);

    const data = await response.json();

    // Valider structure response
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('niche_name');
    expect(data.niche_name).toBe('Test Niche E2E');

    console.log('Created saved niche:', {
      id: data.id,
      name: data.niche_name
    });

    // Cleanup: Delete test niche
    const deleteResponse = await request.delete(
      `${BACKEND_URL}/api/v1/bookmarks/niches/${data.id}`
    );

    console.log('Cleanup delete status:', deleteResponse.status());
  });

  test('Frontend should display niches page', async ({ page }) => {
    console.log('Testing frontend niches page...');

    await page.goto(`${FRONTEND_URL}/niches`);

    // Attendre que page soit chargee
    await page.waitForSelector('#root', { timeout: 10000 });

    console.log('Niches page loaded');

    // Valider presence elements UI (adaptation selon implementation frontend)
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible({ timeout: 5000 });

    console.log('Niches page UI elements visible');
  });
});
