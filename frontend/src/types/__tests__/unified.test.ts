// frontend/src/types/__tests__/unified.test.ts
import { describe, it, expect } from 'vitest'
import {
  normalizeProductScore,
  normalizeNicheProduct,
} from '../unified'
import type { ProductScore } from '../views'

describe('DisplayableProduct normalization', () => {
  it('should normalize ProductScore to DisplayableProduct', () => {
    const productScore: ProductScore = {
      asin: 'B08TEST123',
      title: 'Test Product',
      score: 85.5,
      rank: 1,
      strategy_profile: 'textbook',
      weights_applied: { roi: 0.6, velocity: 0.3, stability: 0.1 },
      components: { roi_contribution: 40, velocity_contribution: 30, stability_contribution: 15 },
      raw_metrics: { roi_pct: 45.2, velocity_score: 72, stability_score: 65 },
      amazon_on_listing: true,
      amazon_buybox: false,
      current_bsr: 12500,
      market_sell_price: 24.99,
      market_buy_price: 15.50,
    }

    const result = normalizeProductScore(productScore)

    expect(result.asin).toBe('B08TEST123')
    expect(result.title).toBe('Test Product')
    expect(result.score).toBe(85.5)
    expect(result.rank).toBe(1)
    expect(result.roi_percent).toBe(45.2)
    expect(result.velocity_score).toBe(72)
    expect(result.bsr).toBe(12500)
    expect(result.source).toBe('product_score')
  })

  it('should normalize NicheProduct to DisplayableProduct', () => {
    const nicheProduct = {
      asin: 'B08NICHE99',
      title: 'Niche Product',
      roi_percent: 38.5,
      velocity_score: 55,
      recommendation: 'BUY',
      current_price: 19.99,
      bsr: 25000,
      category_name: 'Books',
      fba_fees: 5.50,
      estimated_profit: 8.25,
      fba_seller_count: 12,
    }

    const result = normalizeNicheProduct(nicheProduct)

    expect(result.asin).toBe('B08NICHE99')
    expect(result.title).toBe('Niche Product')
    expect(result.roi_percent).toBe(38.5)
    expect(result.velocity_score).toBe(55)
    expect(result.recommendation).toBe('BUY')
    expect(result.bsr).toBe(25000)
    expect(result.source).toBe('niche_product')
    // score and rank should be undefined for niche products
    expect(result.score).toBeUndefined()
    expect(result.rank).toBeUndefined()
  })

  it('should handle null/undefined values gracefully', () => {
    const minimalProduct: ProductScore = {
      asin: 'B08MIN0001',
      title: null,
      score: 0,
      rank: 1,
      strategy_profile: null,
      weights_applied: { roi: 0, velocity: 0, stability: 0 },
      components: { roi_contribution: 0, velocity_contribution: 0, stability_contribution: 0 },
      raw_metrics: { roi_pct: 0, velocity_score: 0, stability_score: 0 },
      amazon_on_listing: false,
      amazon_buybox: false,
    }

    const result = normalizeProductScore(minimalProduct)

    expect(result.asin).toBe('B08MIN0001')
    expect(result.title).toBeNull()
    expect(result.bsr).toBeUndefined()
    expect(result.market_sell_price).toBeUndefined()
  })
})
