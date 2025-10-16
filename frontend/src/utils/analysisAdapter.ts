/**
 * Adapter pour convertir AnalysisResult (API Keepa) → ProductScore (format views)
 * Permet d'utiliser ViewResultsTable pour afficher les résultats de Keepa
 */

import type { AnalysisResult } from '../types/keepa'
import type { ProductScore, RawMetrics } from '../types/views'

/**
 * Convertit un AnalysisResult de l'API Keepa en ProductScore pour ViewResultsTable
 *
 * Extension de ProductScore pour inclure BSR:
 * Nous ajoutons `current_bsr` comme champ custom pour éviter de modifier l'interface
 */
export interface ProductScoreWithBSR extends ProductScore {
  current_bsr?: number | null;
}

/**
 * Convertit un AnalysisResult de l'API Keepa en ProductScore pour ViewResultsTable
 */
export function analysisResultToProductScore(
  analysis: AnalysisResult,
  rank: number
): ProductScoreWithBSR {
  // Extract ROI percentage
  const roiPct = analysis.roi && 'roi_percentage' in analysis.roi
    ? parseFloat(analysis.roi.roi_percentage)
    : 0

  // Calculate score basé sur overall_rating
  const ratingScores: Record<string, number> = {
    'EXCELLENT': 90,
    'GOOD': 70,
    'FAIR': 50,
    'PASS': 30,
    'ERROR': 0
  }
  const score = ratingScores[analysis.overall_rating] || 30

  // Extract velocity breakdown from backend velocity object
  const velocityBreakdown = analysis.velocity && 'error' not in analysis.velocity
    ? {
        bsr_score: analysis.velocity.rank_percentile_30d,
        rank_drops_30d: analysis.velocity.rank_drops_30d,
        buybox_uptime_pct: analysis.velocity.buybox_uptime_30d,
        velocity_tier: analysis.velocity.velocity_tier as 'fast' | 'medium' | 'low'
      }
    : undefined

  return {
    asin: analysis.asin,
    title: analysis.title,
    score: score,
    rank: rank,
    strategy_profile: analysis.strategy_profile as any || 'balanced',

    weights_applied: {
      roi: 0.6, // Default weights (can be adjusted)
      velocity: 0.4,
      stability: 0.0
    },

    components: {
      roi_contribution: roiPct * 0.6,
      velocity_contribution: analysis.velocity_score * 0.4,
      stability_contribution: analysis.price_stability_score * 0.0
    },

    raw_metrics: {
      roi_pct: roiPct,
      velocity_score: analysis.velocity_score,
      stability_score: analysis.price_stability_score
    },

    // Amazon check fields (defaults - Keepa doesn't provide this)
    amazon_on_listing: false,
    amazon_buybox: false,

    // Market analysis
    market_sell_price: analysis.current_price || undefined,
    market_buy_price: analysis.pricing?.used?.current_price || undefined,
    current_roi_pct: analysis.pricing?.used?.roi_percentage || roiPct,
    max_buy_price_35pct: analysis.pricing?.used?.target_buy_price || undefined,
    velocity_breakdown: velocityBreakdown,

    // Timestamp (pas disponible directement, on met undefined)
    last_updated_at: undefined,

    // BSR - Extension custom
    current_bsr: analysis.current_bsr
  }
}

/**
 * Convertit un array de BatchResultItem en ProductScore[]
 */
export function batchResultsToProductScores(
  results: Array<{ analysis: AnalysisResult | null; status: string }>
): ProductScore[] {
  return results
    .filter(r => r.status === 'success' && r.analysis !== null)
    .map((r, index) => analysisResultToProductScore(r.analysis!, index + 1))
}
