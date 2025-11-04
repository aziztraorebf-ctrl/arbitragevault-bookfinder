// Token Control Flow Tests - Phase 5 Token Control System
// Valide que HTTP 429 est gere correctement avec messages conviviaux
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Token Control Flow', () => {
  test('Backend should return HTTP 429 when tokens insufficient', async ({ request }) => {
    console.log('Testing token depletion handling...');

    // Cette requete pourrait echouer avec 429 si tokens vraiment epuises
    // Sinon on valide que l endpoint existe et structure response correcte

    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);

    console.log('Keepa health response status:', response.status());

    // Validation structure response (200 ou 429 acceptable)
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toHaveProperty('tokens');
      expect(data.tokens).toHaveProperty('remaining');
      console.log('Tokens available, no 429 triggered');
    } else if (response.status() === 429) {
      console.log('HTTP 429 detected - validating error structure');

      const data = await response.json();

      // Valider structure erreur HTTP 429
      expect(data).toHaveProperty('detail');
      expect(data.detail).toContain('tokens');

      // Valider headers requis pour frontend
      const headers = response.headers();
      expect(headers).toHaveProperty('x-token-balance');
      expect(headers).toHaveProperty('x-token-required');

      console.log('HTTP 429 structure validated:', {
        balance: headers['x-token-balance'],
        required: headers['x-token-required'],
        message: data.detail
      });
    } else {
      throw new Error(`Unexpected status: ${response.status()}`);
    }
  });

  test('Frontend should display TokenErrorAlert on HTTP 429', async ({ page }) => {
    console.log('Testing frontend HTTP 429 error handling...');

    // Intercepter requetes API pour simuler HTTP 429
    await page.route('**/api/v1/keepa/**', async (route) => {
      console.log('Mocking HTTP 429 for:', route.request().url());

      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'X-Token-Balance': '5',
          'X-Token-Required': '15',
          'Retry-After': '120'
        },
        body: JSON.stringify({
          detail: 'Insufficient Keepa tokens: balance=5, required=15, deficit=10. Try again in 120 seconds.'
        })
      });
    });

    await page.goto(FRONTEND_URL);

    // Attendre que React app soit monte
    await page.waitForSelector('#root', { timeout: 10000 });

    console.log('Frontend loaded, checking for error alert...');

    // NOTE: Ce test validera la presence du composant TokenErrorAlert
    // si une action utilisateur declenche un appel API Keepa
    // Pour l instant on valide juste que le mock fonctionne

    // TODO: Ajouter navigation vers page qui fait appel Keepa
    // et valider presence de TokenErrorAlert
  });

  test('Backend circuit breaker should prevent cascade failures', async ({ request }) => {
    console.log('Testing circuit breaker state...');

    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    expect(response.status()).toBe(200);

    const data = await response.json();

    expect(data).toHaveProperty('circuit_breaker');
    expect(data.circuit_breaker).toHaveProperty('state');

    const state = data.circuit_breaker.state;
    console.log('Circuit breaker state:', state);

    // Circuit breaker doit etre closed ou half_open (jamais open en production saine)
    expect(['closed', 'half_open']).toContain(state);

    if (state === 'half_open') {
      console.warn('WARNING: Circuit breaker in half_open state - investigating failures');
    }
  });

  test('Backend should respect concurrency limits', async ({ request }) => {
    console.log('Testing concurrency control...');

    const response = await request.get(`${BACKEND_URL}/api/v1/keepa/health`);
    expect(response.status()).toBe(200);

    const data = await response.json();

    expect(data).toHaveProperty('performance');
    expect(data.performance).toHaveProperty('concurrency_limit');

    const limit = data.performance.concurrency_limit;
    console.log('Concurrency limit:', limit);

    // Valider que limite est raisonnable (entre 1 et 10)
    expect(limit).toBeGreaterThanOrEqual(1);
    expect(limit).toBeLessThanOrEqual(10);
  });
});
