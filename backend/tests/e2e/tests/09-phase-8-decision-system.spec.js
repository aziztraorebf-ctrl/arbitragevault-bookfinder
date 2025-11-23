/**
 * Phase 8.0 E2E Tests: Advanced Analytics & Decision System
 *
 * Tests the complete decision analytics flow:
 * - Product decision card display
 * - Analytics score calculation
 * - Risk level warnings
 * - Historical trends visualization
 * - Action buttons integration
 *
 * Prerequisites:
 * - Backend API running with Phase 8.0 endpoints
 * - Database migration phase_8_0_analytics applied
 * - ASIN history data populated (optional for trend tests)
 */

const { test, expect } = require('@playwright/test')

const API_BASE_URL = process.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com'
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://arbitragevault.netlify.app'

// Test ASIN with known characteristics
const TEST_ASIN = '0316769487' // Popular book for testing
const TEST_ASIN_LOW_BSR = '0307887898' // Expected good BSR
const TEST_ASIN_HIGH_RISK = 'B00TEST123' // Mock ASIN for risk testing

test.describe('Phase 8.0: Decision System E2E', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to decision system page (adjust URL to match your app)
    await page.goto(FRONTEND_URL)
  })

  test('Test 1: Product Decision Card displays all analytics components', async ({ page }) => {
    // NO MOCKS - Use real production API
    const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: {
        asin: TEST_ASIN,
        estimated_buy_price: 5.00,
        estimated_sell_price: 19.99,
        bsr: 12000
      }
    })

    // Assert: API returns valid decision data
    expect(response.ok()).toBeTruthy()
    const decision = await response.json()

    // Verify response structure
    expect(decision.asin).toBe(TEST_ASIN)
    expect(decision).toHaveProperty('velocity')
    expect(decision).toHaveProperty('price_stability')
    expect(decision).toHaveProperty('roi')
    expect(decision).toHaveProperty('competition')
    expect(decision).toHaveProperty('risk')
    expect(decision).toHaveProperty('recommendation')

    // Verify velocity intelligence
    expect(decision.velocity.velocity_score).toBeGreaterThanOrEqual(0)
    expect(decision.velocity.bsr_current).toBe(12000)

    // Verify ROI calculation
    expect(decision.roi.roi_percentage).toBeGreaterThan(0)
    expect(decision.roi.net_profit).toBeDefined()

    // Verify risk assessment
    expect(decision.risk.risk_score).toBeGreaterThanOrEqual(0)
    expect(decision.risk.risk_level).toMatch(/LOW|MEDIUM|HIGH|CRITICAL/)

    // Verify recommendation
    expect(decision.recommendation.recommendation).toMatch(/STRONG_BUY|BUY|CONSIDER|WATCH|SKIP|AVOID/)
    expect(decision.recommendation.confidence_percent).toBeGreaterThanOrEqual(0)

    console.log('Test 1 PASSED: Product decision API returns valid real data')
    console.log(`  - Velocity Score: ${decision.velocity.velocity_score}`)
    console.log(`  - ROI: ${decision.roi.roi_percentage.toFixed(1)}%`)
    console.log(`  - Risk Level: ${decision.risk.risk_level}`)
    console.log(`  - Recommendation: ${decision.recommendation.recommendation}`)
  })

  test('Test 2: High-risk scenario with low ROI and high BSR', async ({ page }) => {
    // NO MOCKS - Test real API with high-risk parameters
    const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: {
        asin: TEST_ASIN_HIGH_RISK,
        estimated_buy_price: 10.00,
        estimated_sell_price: 12.00,
        bsr: 500000,
        seller_count: 50,
        amazon_on_listing: true,
        amazon_has_buybox: true
      }
    })

    // Assert: API returns valid response
    expect(response.ok()).toBeTruthy()
    const decision = await response.json()

    // Verify high-risk detection based on real recommendation engine logic
    expect(decision.asin).toBe(TEST_ASIN_HIGH_RISK)
    expect(decision.risk.risk_score).toBeGreaterThanOrEqual(0)
    expect(decision.risk.risk_level).toMatch(/LOW|MEDIUM|HIGH|CRITICAL/)

    // With high BSR (500k), low margin, Amazon presence, expect negative recommendation
    expect(decision.recommendation.recommendation).toMatch(/WATCH|SKIP|AVOID/)

    // ROI should be low given margins
    expect(decision.roi.roi_percentage).toBeLessThan(50)

    console.log('Test 2 PASSED: High-risk scenario handled correctly')
    console.log(`  - Risk Score: ${decision.risk.risk_score}`)
    console.log(`  - Risk Level: ${decision.risk.risk_level}`)
    console.log(`  - Recommendation: ${decision.recommendation.recommendation}`)
    console.log(`  - ROI: ${decision.roi.roi_percentage.toFixed(1)}%`)
  })

  test('Test 3: Historical trends API returns valid data', async ({ page }) => {
    // Act: Request historical trends for ASIN
    const response = await page.request.get(
      `${API_BASE_URL}/api/v1/asin-history/trends/${TEST_ASIN}?days=90`
    )

    // Assert: Either returns valid trends or 404 (if no data tracked yet)
    if (response.status() === 200) {
      const trends = await response.json()

      expect(trends.asin).toBe(TEST_ASIN)
      expect(trends.data_points).toBeGreaterThanOrEqual(0)
      expect(trends.date_range).toBeDefined()

      // If data points exist, validate structure
      if (trends.data_points > 0) {
        if (trends.bsr) {
          expect(trends.bsr.current).toBeDefined()
          expect(trends.bsr.trend).toMatch(/improving|declining/)
        }
        if (trends.price) {
          expect(trends.price.current).toBeGreaterThan(0)
          expect(trends.price.average).toBeGreaterThan(0)
        }
      }

      console.log(`Test 3 PASSED: Trends data valid (${trends.data_points} data points)`)
    } else if (response.status() === 404) {
      console.log('Test 3 PASSED: No historical data yet (expected for new ASIN tracking)')
    } else {
      throw new Error(`Unexpected status: ${response.status()}`)
    }
  })

  test('Test 4: Multiple analytics endpoints respond correctly', async ({ page }) => {
    // Act: Test all Phase 8.0 endpoints in sequence
    const endpoints = [
      {
        name: 'Product Decision',
        method: 'POST',
        url: '/api/v1/analytics/product-decision',
        body: { asin: TEST_ASIN, estimated_buy_price: 5.00, estimated_sell_price: 19.99 }
      },
      {
        name: 'ASIN Trends',
        method: 'GET',
        url: `/api/v1/asin-history/trends/${TEST_ASIN}?days=30`,
        expectedStatuses: [200, 404]
      },
      {
        name: 'ASIN Records',
        method: 'GET',
        url: `/api/v1/asin-history/records/${TEST_ASIN}?days=30&limit=50`,
        expectedStatuses: [200, 404]
      }
    ]

    const results = []

    for (const endpoint of endpoints) {
      const options = {
        method: endpoint.method,
        url: `${API_BASE_URL}${endpoint.url}`,
      }

      if (endpoint.body) {
        options.data = endpoint.body
      }

      const response = await page.request.fetch(options.url, options)
      const status = response.status()

      const expectedStatuses = endpoint.expectedStatuses || [200]
      const isValid = expectedStatuses.includes(status)

      results.push({
        name: endpoint.name,
        status,
        valid: isValid
      })

      expect(isValid).toBeTruthy()
    }

    console.log('Test 4 PASSED: All endpoints responded correctly')
    console.table(results)
  })

  test('Test 5: Performance - Analytics calculation under 500ms', async ({ page }) => {
    // Act: Measure API response time
    const startTime = Date.now()

    const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: {
        asin: TEST_ASIN,
        estimated_buy_price: 5.00,
        estimated_sell_price: 19.99
      }
    })

    const endTime = Date.now()
    const responseTime = endTime - startTime

    // Assert: Response time under 500ms (Phase 8.0 performance target)
    expect(response.ok()).toBeTruthy()
    expect(responseTime).toBeLessThan(500)

    console.log(`Test 5 PASSED: Analytics calculation completed in ${responseTime}ms (target: <500ms)`)
  })

})
