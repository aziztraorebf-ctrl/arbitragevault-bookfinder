// Types pour Phase 2 - View-Specific Scoring
// Conformes aux schémas Pydantic backend (routers/views.py)

/**
 * Vue disponible dans l'application
 */
export type ViewType =
  | 'dashboard'
  | 'mes_niches'
  | 'analyse_strategique'
  | 'auto_sourcing'
  | 'stock_estimates'
  | 'niche_discovery'

/**
 * Profil de stratégie pour boost optionnel
 */
export type StrategyProfile = 'textbook' | 'velocity' | 'balanced' | null

/**
 * Poids appliqués pour une vue
 */
export interface ViewWeights {
  roi: number
  velocity: number
  stability: number
  description: string
}

/**
 * Composantes du score
 */
export interface ScoreComponents {
  roi_normalized: number
  velocity_normalized: number
  stability_normalized: number
}

/**
 * Métriques brutes extraites
 * Note: Backend retourne "roi_pct" (pas "roi_percentage")
 */
export interface RawMetrics {
  roi_pct: number  // Backend field name
  velocity_score: number
  stability_score: number
}

/**
 * Velocity breakdown (Phase 2.5A Hybrid)
 * Detailed components for tooltip display
 */
export interface VelocityBreakdown {
  bsr_score?: number
  bsr_avg?: number
  bsr_percentile?: number
  sales_activity_score?: number
  estimated_sales_30d?: number
  bsr_drops_30d?: number
  rank_drops_30d?: number  // Actual field name from backend
  buybox_score?: number
  buybox_uptime_pct?: number | null  // null if data not available
  stability_score?: number
  price_volatility_pct?: number
  price_range_30d?: { min: number; max: number }
  velocity_tier?: 'fast' | 'medium' | 'slow' | 'very_slow'
}

/**
 * Score calculé pour un produit
 * Phase 2.5A: Amazon Check fields added
 */
export interface ProductScore {
  asin: string
  title: string | null
  score: number
  rank: number  // Phase 2.5A: Rank within result set
  strategy_profile: StrategyProfile  // Phase 2.5A: Strategy applied
  weights_applied: {
    roi: number
    velocity: number
    stability: number
  }
  components: {
    roi_contribution: number
    velocity_contribution: number
    stability_contribution: number
  }
  raw_metrics: RawMetrics

  // Phase 2.5A - Amazon Check fields
  amazon_on_listing: boolean  // Amazon has any offer on this product
  amazon_buybox: boolean       // Amazon currently owns the Buy Box

  // Phase 2.5A HYBRID - Market Analysis + Recommendations
  market_sell_price?: number        // Current market sell price (Amazon/marketplace)
  market_buy_price?: number         // Current FBA buy price (3rd party sellers)
  current_roi_pct?: number          // ROI if buying/selling at current market prices
  max_buy_price_35pct?: number      // Recommended max buy price for 35% ROI target
  velocity_breakdown?: VelocityBreakdown  // Detailed velocity components for tooltip

  // Data freshness timestamp (ISO 8601 format)
  last_updated_at?: string | null   // Keepa lastUpdate converted to datetime

  error?: string
}

/**
 * Request pour scorer des produits dans une vue spécifique
 */
export interface ViewScoreRequest {
  identifiers: string[]
  strategy?: StrategyProfile
}

/**
 * Métadonnées de la réponse
 * Updated Phase 2.5A to match backend schema
 */
export interface ViewScoreMetadata {
  view_type: ViewType
  weights_used: {
    roi: number
    velocity: number
    stability: number
  }
  total_products: number
  successful_scores: number
  failed_scores: number
  avg_score: number
  strategy_requested?: StrategyProfile
}

/**
 * Réponse complète du scoring
 */
export interface ViewScoreResponse {
  products: ProductScore[]
  metadata: ViewScoreMetadata
}

/**
 * Informations sur une vue disponible
 */
export interface ViewInfo {
  id: ViewType
  name: string
  weights: ViewWeights
}

/**
 * Liste des vues disponibles
 */
export interface AvailableViewsResponse {
  views: ViewInfo[]
  total: number
}
