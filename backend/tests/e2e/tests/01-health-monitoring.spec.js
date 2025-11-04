// Health Monitoring Tests - Phase 5 Token Control System
// Verifie que production est accessible et fonctionnelle
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Production Health Monitoring', () => {
  test('Backend /health/ready should return 200', async ({ request }) => {
    console.log('Testing backend health endpoint...');

    const response = await request.get(`${BACKEND_URL}/api/v1/health/ready`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log('Backend health:', body);

    expect(body).toHaveProperty('status');
  });

  test('Frontend should load and render React app', async ({ page }) => {
    console.log('Testing frontend loads...');

    await page.goto(FRONTEND_URL);

    // Verifier que React app est monte
    const root = page.locator('#root');
    await expect(root).toBeVisible({ timeout: 10000 });

    // Verifier que navigation est presente
    const nav = page.locator('nav');
    await expect(nav).toBeVisible({ timeout: 5000 });

    console.log('Frontend loaded successfully');
  });

  test('Keepa token balance should be accessible', async ({ request }) => {
    console.log('Checking Keepa token balance...');

    const CRITICAL_THRESHOLD = -1; // Allow 0 tokens, just verify endpoint works

    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    console.log('Keepa health:', data);

    expect(data).toHaveProperty('tokens');
    expect(data.tokens).toHaveProperty('remaining');

    const tokensLeft = data.tokens.remaining;

    // Assertion critique
    expect(tokensLeft).toBeGreaterThan(CRITICAL_THRESHOLD);

    // Warning si proche du seuil
    if (tokensLeft < 50) {
      console.warn(`WARNING: Token balance low: ${tokensLeft} tokens remaining`);
    } else {
      console.log(`Token balance healthy: ${tokensLeft} tokens`);
    }
  });

  test('Backend response time should be acceptable', async ({ request }) => {
    console.log('Testing backend response time...');

    const startTime = Date.now();
    const response = await request.get(`${BACKEND_URL}/api/v1/health/ready`);
    const endTime = Date.now();

    const responseTime = endTime - startTime;

    console.log(`Backend response time: ${responseTime}ms`);

    expect(response.status()).toBe(200);

    // Response time should be under 5 seconds
    expect(responseTime).toBeLessThan(5000);

    // Warning if slow
    if (responseTime > 2000) {
      console.warn(`WARNING: Slow response time: ${responseTime}ms`);
    }
  });
});
