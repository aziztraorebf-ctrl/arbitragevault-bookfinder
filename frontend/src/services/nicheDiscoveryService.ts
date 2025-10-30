/**
 * Phase 3 Day 9 - Niche Discovery Service
 * Service API pour découverte automatique de niches via templates curés
 */

import { api, ApiError } from './api'

/**
 * Validated Niche structure from backend
 */
export interface ValidatedNiche {
  id: string
  name: string
  description: string
  icon: string
  categories: number[]
  bsr_range: [number, number]
  price_range: [number, number]
  products_found: number
  avg_roi: number
  avg_velocity: number
  top_products: Array<{
    asin: string
    title?: string
    roi_percent: number
    velocity_score: number
    current_price?: number
    bsr?: number
  }>
}

/**
 * Niche Discovery Response
 */
export interface NicheDiscoveryResponse {
  products: [] // Always empty for auto mode
  total_count: 0
  cache_hit: boolean
  metadata: {
    mode: 'auto'
    niches: ValidatedNiche[]
    niches_count: number
    timestamp: string
    source: 'curated_templates'
  }
}

/**
 * Manual Discovery Filters
 */
export interface ManualDiscoveryFilters {
  category?: number
  bsr_min?: number
  bsr_max?: number
  price_min?: number
  price_max?: number
  min_roi?: number
  min_velocity?: number
  max_results?: number
}

/**
 * Manual Discovery Response (uses existing ProductScore)
 */
export interface ManualDiscoveryResponse {
  products: Array<{
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
  }>
  total_count: number
  cache_hit: boolean
  metadata: {
    mode: 'manual'
    filters_applied: ManualDiscoveryFilters
    timestamp: string
    source: string
  }
}

/**
 * Service Niche Discovery
 */
export const nicheDiscoveryService = {
  /**
   * Auto-discover curated niches
   * Endpoint: GET /api/v1/niches/discover
   *
   * @param count - Number of niches to discover (1-5, default 3)
   * @param shuffle - Randomize template selection (default true)
   * @returns List of validated niches with real-time Keepa validation
   */
  async discoverAuto(
    count: number = 3,
    shuffle: boolean = true
  ): Promise<NicheDiscoveryResponse> {
    try {
      console.log(`🎲 Auto-discovering ${count} niches (shuffle=${shuffle})`)

      const response = await api.get<NicheDiscoveryResponse>(
        '/api/v1/niches/discover',
        { params: { count, shuffle } }
      )

      console.log('✅ Auto-discovery completed:', {
        nichesCount: response.data.metadata.niches_count,
        totalProducts: response.data.metadata.niches.reduce(
          (sum, n) => sum + n.products_found,
          0
        ),
      })

      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        `Auto-discovery failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },

  /**
   * Manual discovery with user-specified filters
   * Endpoint: POST /api/v1/products/discover-with-scoring
   *
   * @param filters - Discovery filters (category, BSR, price, ROI, velocity)
   * @returns List of products matching filters
   */
  async discoverManual(
    filters: ManualDiscoveryFilters
  ): Promise<ManualDiscoveryResponse> {
    try {
      console.log('🔍 Manual discovery with filters:', filters)

      const response = await api.post<ManualDiscoveryResponse>(
        '/api/v1/products/discover-with-scoring',
        {
          domain: 1, // US Amazon
          ...filters,
        }
      )

      console.log('✅ Manual discovery completed:', {
        productsCount: response.data.products.length,
        cacheHit: response.data.cache_hit,
      })

      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        `Manual discovery failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },

  /**
   * Drill-down into a specific niche
   * Re-runs discovery with niche template filters to get all products
   *
   * @param niche - Validated niche to explore
   * @returns Full list of products in this niche
   */
  async exploreNiche(niche: ValidatedNiche): Promise<ManualDiscoveryResponse> {
    return this.discoverManual({
      category: niche.categories[0],
      bsr_min: niche.bsr_range[0],
      bsr_max: niche.bsr_range[1],
      price_min: niche.price_range[0],
      price_max: niche.price_range[1],
      max_results: 50, // More products for detailed view
    })
  },
}

/**
 * Helper: Format niche summary for UI display
 */
export const formatNicheSummary = (niche: ValidatedNiche): string => {
  return `${niche.products_found} produits | ROI moy. ${niche.avg_roi.toFixed(1)}% | Vélocité ${niche.avg_velocity.toFixed(0)}`
}

/**
 * Helper: Get niche quality badge
 */
export const getNicheQualityBadge = (
  niche: ValidatedNiche
): { label: string; color: string } => {
  const score = (niche.avg_roi + niche.avg_velocity) / 2

  if (score >= 60) {
    return { label: 'Excellent', color: 'green' }
  } else if (score >= 45) {
    return { label: 'Bon', color: 'blue' }
  } else {
    return { label: 'Moyen', color: 'yellow' }
  }
}

// Export pour backward compatibility
export const discoverNiches = nicheDiscoveryService.discoverAuto
export const exploreNiche = nicheDiscoveryService.exploreNiche
