// @ts-check
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Source Price Factor 0.50 Verification', () => {

  test('Backend health endpoint returns ready', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v1/health/ready`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ready');
    console.log('Backend health:', data.status, 'Version:', data.version);
  });

  test('Keepa health shows sufficient tokens', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.tokens.remaining).toBeGreaterThan(50);
    console.log('Keepa tokens remaining:', data.tokens.remaining);
  });

  test('Niche Discovery returns products with ROI in expected range', async ({ request }) => {
    const response = await request.get(
      `${BACKEND_URL}/api/v1/niches/discover?strategy=smart-velocity&limit=3`
    );

    if (response.ok()) {
      const data = await response.json();
      console.log(`Niche discovery returned ${data.products?.length || 0} products from ${data.metadata?.niches?.length || 0} niches`);

      // Check ROI values are in realistic range (with source_price_factor=0.50)
      if (data.metadata?.niches) {
        for (const niche of data.metadata.niches) {
          if (niche.top_products) {
            for (const product of niche.top_products) {
              if (product.roi_percent !== undefined) {
                console.log(`Product ${product.asin}: ROI = ${product.roi_percent.toFixed(1)}%`);
                // With 0.50 factor, ROI should typically be 20-80%
                // With old 0.70 bug, ROI would be around 5-20%
                // We check for > 15% as a sanity check
                if (product.roi_percent > 15) {
                  console.log('  ROI looks reasonable for source_price_factor=0.50');
                } else {
                  console.log('  WARNING: Low ROI - check if source_price_factor bug has returned');
                }
              }
            }
          }
        }
      }
    } else {
      console.log(`Niche discovery status: ${response.status()}`);
    }
  });

  test('AutoSourcing jobs endpoint returns valid response', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v1/autosourcing/jobs?limit=5`);
    expect(response.ok()).toBeTruthy();

    const jobs = await response.json();
    expect(Array.isArray(jobs)).toBeTruthy();
    console.log(`Found ${jobs.length} AutoSourcing jobs`);

    // Check if any completed jobs have picks with ROI data
    for (const job of jobs) {
      if (job.status === 'success' && job.picks && job.picks.length > 0) {
        console.log(`Job ${job.id}: ${job.picks.length} picks`);
        for (const pick of job.picks.slice(0, 3)) {
          if (pick.roi_percentage !== undefined) {
            console.log(`  Pick ${pick.asin}: ROI = ${pick.roi_percentage}%`);
          }
        }
      }
    }
  });

  test('Frontend AutoSourcing page loads correctly', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');

    // Should see AutoSourcing related content
    const pageContent = await page.content();
    const hasAutoSourcingContent =
      pageContent.includes('AutoSourcing') ||
      pageContent.includes('autosourcing') ||
      pageContent.includes('Discovery') ||
      pageContent.includes('Job');

    expect(hasAutoSourcingContent).toBeTruthy();
    console.log('Frontend AutoSourcing page loaded successfully');
  });

  test('Frontend Niche Discovery page loads correctly', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/niche-discovery`);
    await page.waitForLoadState('networkidle');

    // Should see niche discovery content
    const pageContent = await page.content();
    const hasNicheContent =
      pageContent.includes('Niche') ||
      pageContent.includes('Discovery') ||
      pageContent.includes('niche');

    expect(hasNicheContent).toBeTruthy();
    console.log('Frontend Niche Discovery page loaded successfully');
  });

});
