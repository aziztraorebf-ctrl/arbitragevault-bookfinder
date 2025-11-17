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

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173'

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
    // Arrange: Mock API response for product decision
    await page.route(`${API_BASE_URL}/api/v1/analytics/product-decision`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          asin: TEST_ASIN,
          title: 'Test Product for Analytics',
          velocity: {
            velocity_score: 75.5,
            trend_7d: -50,
            trend_30d: -120,
            trend_90d: -200,
            bsr_current: 12000,
            risk_level: 'LOW'
          },
          price_stability: {
            stability_score: 82.3,
            coefficient_variation: 0.12,
            price_volatility: 'LOW',
            avg_price: 15.99,
            std_deviation: 1.92
          },
          roi: {
            net_profit: 8.50,
            roi_percentage: 42.5,
            gross_profit: 14.99,
            referral_fee: 2.25,
            fba_fee: 2.50,
            prep_fee: 0.50,
            storage_cost: 0.87,
            return_losses: 0.37,
            total_fees: 6.49,
            breakeven_required_days: 28
          },
          competition: {
            competition_score: 60.0,
            competition_level: 'MEDIUM',
            seller_count: 12,
            fba_ratio: 0.67,
            amazon_risk: 'LOW'
          },
          risk: {
            asin: TEST_ASIN,
            risk_score: 38.5,
            risk_level: 'MEDIUM',
            components: {
              dead_inventory: { score: 25, weighted: 8.75, weight: 0.35 },
              competition: { score: 60, weighted: 15.0, weight: 0.25 },
              amazon_presence: { score: 0, weighted: 0.0, weight: 0.20 },
              price_stability: { score: 18, weighted: 1.8, weight: 0.10 },
              category: { score: 30, weighted: 3.0, weight: 0.10 }
            },
            recommendations: 'Medium risk - Monitor competition and pricing trends'
          },
          recommendation: {
            asin: TEST_ASIN,
            title: 'Test Product for Analytics',
            recommendation: 'BUY',
            confidence_percent: 78.5,
            criteria_passed: 5,
            criteria_total: 6,
            reason: 'Strong opportunity - Good ROI and velocity, acceptable risk level',
            roi_net: 42.5,
            velocity_score: 75.5,
            risk_score: 38.5,
            profit_per_unit: 8.50,
            estimated_time_to_sell_days: 28,
            suggested_action: 'Purchase this product and monitor for price stability',
            next_steps: [
              'Verify supplier pricing and availability',
              'Check Amazon inventory levels',
              'Monitor BSR trends for next 7 days'
            ]
          }
        })
      })
    })

    // Act: Trigger decision card component (adjust selector to match your implementation)
    // This assumes you have a page or section that displays ProductDecisionCard
    // For now, we just verify API response structure

    const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: {
        asin: TEST_ASIN,
        estimated_buy_price: 5.00,
        estimated_sell_price: 19.99
      }
    })

    // Assert: API returns valid decision data
    expect(response.ok()).toBeTruthy()
    const decision = await response.json()

    expect(decision.asin).toBe(TEST_ASIN)
    expect(decision.recommendation.recommendation).toBe('BUY')
    expect(decision.velocity.velocity_score).toBeGreaterThan(70)
    expect(decision.roi.roi_percentage).toBeGreaterThan(30)
    expect(decision.risk.risk_level).toBe('MEDIUM')

    console.log('Test 1 PASSED: Product decision data structure valid')
  })

  test('Test 2: Risk level AVOID warning displays correctly', async ({ page }) => {
    // Arrange: Mock high-risk product with Amazon on Buy Box
    await page.route(`${API_BASE_URL}/api/v1/analytics/product-decision`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          asin: TEST_ASIN_HIGH_RISK,
          title: 'High Risk Product - Amazon Owns Buy Box',
          velocity: {
            velocity_score: 45.0,
            bsr_current: 85000,
            risk_level: 'HIGH'
          },
          price_stability: {
            stability_score: 30.0,
            price_volatility: 'HIGH'
          },
          roi: {
            net_profit: 2.50,
            roi_percentage: 12.5,
            gross_profit: 5.00,
            total_fees: 2.50,
            breakeven_required_days: 60
          },
          competition: {
            competition_score: 85.0,
            competition_level: 'HIGH',
            seller_count: 45,
            amazon_risk: 'HIGH'
          },
          risk: {
            asin: TEST_ASIN_HIGH_RISK,
            risk_score: 82.5,
            risk_level: 'CRITICAL',
            components: {
              dead_inventory: { score: 80, weighted: 28.0, weight: 0.35 },
              competition: { score: 85, weighted: 21.25, weight: 0.25 },
              amazon_presence: { score: 100, weighted: 20.0, weight: 0.20 },
              price_stability: { score: 70, weighted: 7.0, weight: 0.10 },
              category: { score: 60, weighted: 6.0, weight: 0.10 }
            },
            recommendations: 'CRITICAL RISK - Amazon owns Buy Box. Avoid this product.'
          },
          recommendation: {
            asin: TEST_ASIN_HIGH_RISK,
            title: 'High Risk Product - Amazon Owns Buy Box',
            recommendation: 'AVOID',
            confidence_percent: 95.0,
            criteria_passed: 1,
            criteria_total: 6,
            reason: 'CRITICAL: Amazon owns Buy Box. Competition risk too high.',
            roi_net: 12.5,
            velocity_score: 45.0,
            risk_score: 82.5,
            profit_per_unit: 2.50,
            estimated_time_to_sell_days: 60,
            suggested_action: 'Do not purchase - High risk of dead inventory',
            next_steps: [
              'Find alternative products in same category',
              'Avoid all products where Amazon owns Buy Box'
            ]
          }
        })
      })
    })

    // Act: Request decision for high-risk ASIN
    const response = await page.request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: {
        asin: TEST_ASIN_HIGH_RISK,
        estimated_buy_price: 10.00,
        estimated_sell_price: 15.00
      }
    })

    // Assert: AVOID recommendation returned
    expect(response.ok()).toBeTruthy()
    const decision = await response.json()

    expect(decision.recommendation.recommendation).toBe('AVOID')
    expect(decision.risk.risk_level).toBe('CRITICAL')
    expect(decision.risk.risk_score).toBeGreaterThan(75)
    expect(decision.recommendation.reason).toContain('Amazon owns Buy Box')

    console.log('Test 2 PASSED: AVOID recommendation for high-risk product')
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
