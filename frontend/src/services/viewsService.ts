import type {
  ViewType,
  ViewScoreRequest,
  ViewScoreResponse,
  AvailableViewsResponse,
} from '../types/views'

const API_URL =
  import.meta.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com'

/**
 * Service pour l'intégration Phase 2 - View-Specific Scoring
 */
class ViewsService {
  private baseUrl: string

  constructor() {
    this.baseUrl = `${API_URL}/api/v1`
  }

  /**
   * Récupère la liste des vues disponibles avec leurs poids
   */
  async getAvailableViews(): Promise<AvailableViewsResponse> {
    const response = await fetch(`${this.baseUrl}/views`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Score des produits pour une vue spécifique
   *
   * @param viewType - Type de vue (dashboard, mes_niches, auto_sourcing, etc.)
   * @param request - Identifiers et stratégie optionnelle
   * @param enableFeatureFlag - Active le feature flag via header (dev/test only)
   */
  async scoreProductsForView(
    viewType: ViewType,
    request: ViewScoreRequest,
    enableFeatureFlag: boolean = true
  ): Promise<ViewScoreResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // DEV/TEST: Override feature flag via header
    if (enableFeatureFlag) {
      headers['X-Feature-Flags-Override'] = JSON.stringify({
        view_specific_scoring: true,
      })
    }

    const response = await fetch(`${this.baseUrl}/views/${viewType}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.text()

      // Handle specific error cases
      if (response.status === 403) {
        throw new Error('View-specific scoring not enabled. Contact admin to enable feature.')
      }

      throw new Error(error || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Valide si un view_type est supporté
   */
  validateViewType(viewType: string): viewType is ViewType {
    const validViews: ViewType[] = [
      'dashboard',
      'mes_niches',
      'analyse_strategique',
      'auto_sourcing',
      'stock_estimates',
      'niche_discovery',
    ]
    return validViews.includes(viewType as ViewType)
  }

  /**
   * Récupère le nom lisible d'une vue
   */
  getViewDisplayName(viewType: ViewType): string {
    const names: Record<ViewType, string> = {
      dashboard: 'Dashboard',
      mes_niches: 'Mes Niches',
      analyse_strategique: 'Analyse Stratégique',
      auto_sourcing: 'AutoSourcing',
      stock_estimates: 'Stock Estimates',
      niche_discovery: 'Niche Discovery',
    }
    return names[viewType]
  }

  /**
   * Récupère la description d'une vue
   */
  getViewDescription(viewType: ViewType): string {
    const descriptions: Record<ViewType, string> = {
      dashboard: 'Vue équilibrée pour un aperçu général',
      mes_niches: 'Priorise le ROI pour vos niches sauvegardées',
      analyse_strategique: 'Priorise la vélocité pour analyse rapide',
      auto_sourcing: 'Optimisé pour rotation rapide et liquidité',
      stock_estimates: 'Priorise la stabilité pour estimations',
      niche_discovery: 'Vue équilibrée pour découvrir de nouvelles opportunités',
    }
    return descriptions[viewType]
  }
}

export const viewsService = new ViewsService()
