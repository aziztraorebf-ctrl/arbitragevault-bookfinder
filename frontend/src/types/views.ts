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
 */
export interface RawMetrics {
  roi_percentage: number
  velocity_score: number
  stability_score: number
}

/**
 * Score calculé pour un produit
 */
export interface ProductScore {
  asin: string
  title: string | null
  score: number
  view_type: ViewType
  weights_applied: ViewWeights
  components: ScoreComponents
  raw_metrics: RawMetrics
  strategy_boost?: number
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
 */
export interface ViewScoreMetadata {
  view_type: ViewType
  total_products: number
  successful: number
  failed: number
  timestamp: string
  feature_flags: {
    view_specific_scoring: boolean
    scoring_shadow_mode: boolean
  }
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
