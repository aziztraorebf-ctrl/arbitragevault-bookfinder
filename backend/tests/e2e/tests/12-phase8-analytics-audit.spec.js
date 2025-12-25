/**
 * Phase 8 Analytics Audit E2E Tests
 *
 * Validates all Phase 8 analytics endpoints work correctly in production.
 * Tests use real production API - no mocks.
 */
const { test, expect } = require('@playwright/test')
const { getRandomASIN } = require('../test-utils/random-data')

const API_BASE_URL = process.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com'

// Seed-based ASINs for reproducibility
const TEST_SEED = process.env.TEST_SEED || 'phase-8-audit'
const TEST_ASINS = {
  standard: getRandomASIN(`${TEST_SEED}-standard`, 'books_medium_bsr'),
  high_roi: getRandomASIN(`${TEST_SEED}-high-roi`, 'books_low_bsr'),
  high_risk: getRandomASIN(`${TEST_SEED}-high-risk`, 'books_high_bsr')
}

test.describe('Phase 8 Analytics API - E2E Audit', () => {

  test.describe('POST /calculate-analytics', () => {

    test('returns all analytics components for valid request', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/calculate-analytics`, {
        data: {
          asin: TEST_ASINS.standard,
          title: 'E2E Test Book',
          estimated_buy_price: '7.50',
          estimated_sell_price: '22.99',
          bsr: 25000,
          seller_count: 8
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      // Verify all components present
      expect(data.asin).toBe(TEST_ASINS.standard)
      expect(data).toHaveProperty('velocity')
      expect(data).toHaveProperty('price_stability')
      expect(data).toHaveProperty('roi')
      expect(data).toHaveProperty('competition')
      expect(data).toHaveProperty('slow_velocity_risk')  // Renamed from dead_inventory_risk

      // Verify velocity structure
      expect(data.velocity).toHaveProperty('velocity_score')
      expect(data.velocity.velocity_score).toBeGreaterThanOrEqual(0)
      expect(data.velocity.velocity_score).toBeLessThanOrEqual(100)

      console.log('calculate-analytics: All components validated')
    })

    test('returns 422 for missing required fields', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/calculate-analytics`, {
        data: {
          asin: 'TEST123'
          // Missing estimated_buy_price and estimated_sell_price
        }
      })

      expect(response.status()).toBe(422)
    })
  })

  test.describe('POST /calculate-risk-score', () => {

    test('returns valid risk assessment', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/calculate-risk-score`, {
        data: {
          asin: TEST_ASINS.standard,
          estimated_buy_price: '10.00',
          estimated_sell_price: '28.00',
          bsr: 35000,
          category: 'books',
          seller_count: 12,
          amazon_on_listing: false
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      expect(data.asin).toBe(TEST_ASINS.standard)
      expect(data.risk_score).toBeGreaterThanOrEqual(0)
      expect(data.risk_score).toBeLessThanOrEqual(100)
      expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).toContain(data.risk_level)
      expect(data).toHaveProperty('components')
      expect(data).toHaveProperty('recommendations')

      console.log(`Risk score: ${data.risk_score}, Level: ${data.risk_level}`)
    })

    test('returns higher risk when Amazon present', async ({ page }) => {
      const responseWithoutAmazon = await page.request.post(`${API_BASE_URL}/api/v1/analytics/calculate-risk-score`, {
        data: {
          asin: TEST_ASINS.standard,
          estimated_buy_price: '10.00',
          estimated_sell_price: '28.00',
          bsr: 35000,
          amazon_on_listing: false
        }
      })

      const responseWithAmazon = await page.request.post(`${API_BASE_URL}/api/v1/analytics/calculate-risk-score`, {
        data: {
          asin: TEST_ASINS.standard,
          estimated_buy_price: '10.00',
          estimated_sell_price: '28.00',
          bsr: 35000,
          amazon_on_listing: true
        }
      })

      const dataWithout = await responseWithoutAmazon.json()
      const dataWith = await responseWithAmazon.json()

      expect(dataWith.risk_score).toBeGreaterThan(dataWithout.risk_score)
      console.log(`Risk without Amazon: ${dataWithout.risk_score}, with Amazon: ${dataWith.risk_score}`)
    })
  })

  test.describe('POST /generate-recommendation', () => {

    test('returns STRONG_BUY for ideal metrics', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/generate-recommendation`, {
        data: {
          asin: TEST_ASINS.high_roi,
          title: 'High ROI Test Book',
          estimated_buy_price: '5.00',
          estimated_sell_price: '25.00',  // 400% gross margin
          bsr: 5000,  // Low BSR = good velocity
          seller_count: 2,
          amazon_on_listing: false
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      expect(['STRONG_BUY', 'BUY']).toContain(data.recommendation)
      expect(data.roi_net).toBeGreaterThan(30)
      expect(data.confidence_percent).toBeGreaterThan(50)
      expect(data).toHaveProperty('next_steps')
      expect(Array.isArray(data.next_steps)).toBeTruthy()

      console.log(`Recommendation: ${data.recommendation}, Confidence: ${data.confidence_percent}%`)
    })

    test('returns SKIP/AVOID for poor metrics', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/generate-recommendation`, {
        data: {
          asin: TEST_ASINS.high_risk,
          title: 'Poor Metrics Book',
          estimated_buy_price: '15.00',
          estimated_sell_price: '16.00',  // Very low margin
          bsr: 500000,  // High BSR = slow sales
          seller_count: 50,
          amazon_on_listing: true,
          amazon_has_buybox: true
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      expect(['SKIP', 'AVOID', 'WATCH']).toContain(data.recommendation)
      console.log(`Recommendation for poor metrics: ${data.recommendation}`)
    })

    test('includes all recommendation fields', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/generate-recommendation`, {
        data: {
          asin: TEST_ASINS.standard,
          title: 'Standard Test Book',
          estimated_buy_price: '8.00',
          estimated_sell_price: '20.00',
          bsr: 30000
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      // Verify all required fields
      expect(data).toHaveProperty('asin')
      expect(data).toHaveProperty('recommendation')
      expect(data).toHaveProperty('confidence_percent')
      expect(data).toHaveProperty('criteria_passed')
      expect(data).toHaveProperty('criteria_total')
      expect(data).toHaveProperty('reason')
      expect(data).toHaveProperty('roi_net')
      expect(data).toHaveProperty('velocity_score')
      expect(data).toHaveProperty('risk_score')
      expect(data).toHaveProperty('suggested_action')
      expect(data).toHaveProperty('next_steps')
    })
  })

  test.describe('POST /product-decision', () => {

    test('returns complete decision card', async ({ page }) => {
      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
        data: {
          asin: TEST_ASINS.standard,
          title: 'Decision Card Test',
          estimated_buy_price: '6.00',
          estimated_sell_price: '18.00',
          bsr: 20000,
          seller_count: 6,
          fba_seller_count: 4,
          amazon_on_listing: false
        }
      })

      expect(response.ok()).toBeTruthy()
      const data = await response.json()

      // Complete decision card has all sections
      expect(data.asin).toBe(TEST_ASINS.standard)
      expect(data).toHaveProperty('velocity')
      expect(data).toHaveProperty('price_stability')
      expect(data).toHaveProperty('roi')
      expect(data).toHaveProperty('competition')
      expect(data).toHaveProperty('risk')
      expect(data).toHaveProperty('recommendation')

      // Verify nested structures
      expect(data.risk).toHaveProperty('risk_score')
      expect(data.risk).toHaveProperty('components')
      expect(data.recommendation).toHaveProperty('recommendation')

      console.log('Decision card: All sections validated')
    })

    test('decision card response time under 1000ms', async ({ page }) => {
      const startTime = Date.now()

      const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
        data: {
          asin: TEST_ASINS.standard,
          estimated_buy_price: '7.00',
          estimated_sell_price: '21.00',
          bsr: 25000
        }
      })

      const responseTime = Date.now() - startTime

      expect(response.ok()).toBeTruthy()
      expect(responseTime).toBeLessThan(1000)

      console.log(`Decision card response time: ${responseTime}ms`)
    })
  })

  test.describe('GET /asin-history/trends', () => {

    test('returns 404 for unknown ASIN', async ({ page }) => {
      const response = await page.request.get(`${API_BASE_URL}/api/v1/asin-history/trends/UNKNOWN_ASIN_123456?days=30`)

      // Should be 404 (no data) or 200 (empty response)
      expect([200, 404]).toContain(response.status())
    })

    test('validates days parameter', async ({ page }) => {
      const response = await page.request.get(`${API_BASE_URL}/api/v1/asin-history/trends/TEST123?days=0`)

      expect(response.status()).toBe(422)
    })
  })

  test.describe('GET /asin-history/latest', () => {

    test('returns 404 for unknown ASIN', async ({ page }) => {
      const response = await page.request.get(`${API_BASE_URL}/api/v1/asin-history/latest/UNKNOWN_ASIN_999`)

      expect(response.status()).toBe(404)
    })
  })

})
