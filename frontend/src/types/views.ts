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
