/**
 * Unified Product Type
 * Normalizes ProductScore (Analyse Manuelle/AutoSourcing) and NicheProduct (Niche Discovery)
 * into a single displayable format for UnifiedProductTable
 */

import type { ProductScore, StrategyProfile, VelocityBreakdown } from './views'

// Source type discriminator
export type ProductSource = 'product_score' | 'niche_product'

// Recommendation values from Niche Discovery
export type Recommendation = 'STRONG_BUY' | 'BUY' | 'CONSIDER' | 'SKIP'

/**
 * NicheProduct - Type for products from Niche Discovery
 * Matches ProductsTable interface in niche-discovery/ProductsTable.tsx
 */
export interface NicheProduct {
  asin: string
  title?: string
  roi_percent: number
  velocity_score: number
  recommendation: string
  current_price?: number
  bsr?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
  fba_seller_count?: number
}

/**
 * DisplayableProduct - Unified type for all product displays
 * Contains all possible fields from both sources with optional flags
 */
export interface DisplayableProduct {
  // Core identity (required)
  asin: string
  title: string | null
  source: ProductSource

  // Metrics (common to both, normalized)
  roi_percent: number
  velocity_score: number
  bsr?: number

  // ProductScore-specific fields (optional)
  score?: number
  rank?: number
  strategy_profile?: StrategyProfile
  weights_applied?: {
    roi: number
    velocity: number
    stability: number
  }
  components?: {
    roi_contribution: number
    velocity_contribution: number
    stability_contribution: number
  }
  stability_score?: number
  amazon_on_listing?: boolean
  amazon_buybox?: boolean
  market_sell_price?: number
  market_buy_price?: number
  current_roi_pct?: number
  max_buy_price_35pct?: number
  velocity_breakdown?: VelocityBreakdown
  last_updated_at?: string | null
  pricing?: ProductScore['pricing']

  // NicheProduct-specific fields (optional)
  recommendation?: Recommendation | string
  current_price?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
  fba_seller_count?: number
}

/**
 * Normalize a ProductScore to DisplayableProduct
 */
export function normalizeProductScore(product: ProductScore): DisplayableProduct {
  return {
    // Core
    asin: product.asin,
    title: product.title,
    source: 'product_score',

    // Metrics (normalized field names)
    roi_percent: product.raw_metrics?.roi_pct ?? 0,
    velocity_score: product.raw_metrics?.velocity_score ?? 0,
    bsr: product.current_bsr ?? undefined,

    // ProductScore-specific
    score: product.score,
    rank: product.rank,
    strategy_profile: product.strategy_profile,
    weights_applied: product.weights_applied,
    components: product.components,
    stability_score: product.raw_metrics?.stability_score,
    amazon_on_listing: product.amazon_on_listing,
    amazon_buybox: product.amazon_buybox,
    market_sell_price: product.market_sell_price,
    market_buy_price: product.market_buy_price,
    current_roi_pct: product.current_roi_pct,
    max_buy_price_35pct: product.max_buy_price_35pct,
    velocity_breakdown: product.velocity_breakdown,
    last_updated_at: product.last_updated_at,
    pricing: product.pricing,
  }
}

/**
 * Normalize a NicheProduct to DisplayableProduct
 */
export function normalizeNicheProduct(product: NicheProduct): DisplayableProduct {
  return {
    // Core
    asin: product.asin,
    title: product.title ?? null,
    source: 'niche_product',

    // Metrics (already normalized in NicheProduct)
    roi_percent: product.roi_percent,
    velocity_score: product.velocity_score,
    bsr: product.bsr,

    // NicheProduct-specific
    recommendation: product.recommendation as Recommendation,
    current_price: product.current_price,
    category_name: product.category_name,
    fba_fees: product.fba_fees,
    estimated_profit: product.estimated_profit,
    fba_seller_count: product.fba_seller_count,
  }
}

/**
 * Type guard to check if product has ProductScore-specific fields
 */
export function hasScoreData(product: DisplayableProduct): boolean {
  return product.source === 'product_score' && product.score !== undefined
}

/**
 * Type guard to check if product has NicheProduct-specific fields
 */
export function hasRecommendation(product: DisplayableProduct): boolean {
  return product.recommendation !== undefined
}
