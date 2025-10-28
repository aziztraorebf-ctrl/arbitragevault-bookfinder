/**
 * Phase 3 - Product Discovery Service
 * Service API pour discovery et scoring produits via Keepa Product Finder
 */

import { api, ApiError } from './api'
import type {
  ProductDiscoveryRequest,
  ProductDiscoveryResponse,
  DiscoveryOnlyResponse,
  ScoringRequest,
  ProductScore,
} from '../types/productDiscovery'
import {
  ProductDiscoveryResponseSchema,
  DiscoveryOnlyResponseSchema,
} from '../types/productDiscovery'

/**
 * Service Product Discovery avec validation Zod
 */
export const productDiscoveryService = {
  /**
   * Discovery + Scoring en une seule requête
   * Endpoint: POST /api/v1/products/discover-with-scoring
   *
   * Utilise le cache backend (product_discovery_cache + product_scoring_cache)
   *
   * @param filters - Filtres de recherche (catégories, BSR, prix)
   * @returns Liste de produits avec scores ROI/Velocity
   */
  async discoverWithScoring(
    filters: ProductDiscoveryRequest
  ): Promise<ProductDiscoveryResponse> {
    try {
      console.log('🔍 Product Discovery with Scoring:', filters)

      const response = await api.post(
        '/api/v1/products/discover-with-scoring',
        filters
      )

      // Validation Zod
      const result = ProductDiscoveryResponseSchema.safeParse(response.data)
      if (!result.success) {
        throw new ApiError('Invalid discovery response format', 500, {
          zodErrors: result.error.issues,
          received: response.data,
        })
      }

      console.log('✅ Discovery completed:', {
        productsCount: result.data.products.length,
        cacheHit: result.data.cache_hit,
        executionTime: result.data.metadata.execution_time_ms,
      })

      return result.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        `Product discovery failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },

  /**
   * Discovery UNIQUEMENT (retourne ASINs sans scoring)
   * Endpoint: POST /api/v1/products/discover
   *
   * Plus rapide que discoverWithScoring si scoring pas nécessaire
   *
   * @param filters - Filtres de recherche
   * @returns Liste d'ASINs découverts
   */
  async discoverOnly(
    filters: ProductDiscoveryRequest
  ): Promise<DiscoveryOnlyResponse> {
    try {
      console.log('🔍 Product Discovery (ASINs only):', filters)

      const response = await api.post('/api/v1/products/discover', filters)

      // Validation Zod
      const result = DiscoveryOnlyResponseSchema.safeParse(response.data)
      if (!result.success) {
        throw new ApiError('Invalid discovery-only response format', 500, {
          zodErrors: result.error.issues,
          received: response.data,
        })
      }

      console.log('✅ Discovery completed:', {
        asinsCount: result.data.asins.length,
        cacheHit: result.data.cache_hit,
      })

      return result.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        `Product discovery failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },

  /**
   * Scoring UNIQUEMENT pour liste d'ASINs
   * Endpoint: POST /api/v1/products/score
   *
   * Utile pour scorer des ASINs déjà découverts ou externes
   *
   * @param request - Liste d'ASINs à scorer
   * @returns Liste de produits avec scores
   */
  async scoreProducts(
    request: ScoringRequest
  ): Promise<{ products: ProductScore[] }> {
    try {
      console.log('📊 Scoring products:', request.asins.length, 'ASINs')

      const response = await api.post('/api/v1/products/score', request)

      // Validation manuelle car pas de schema dédié pour score-only
      if (!response.data?.products || !Array.isArray(response.data.products)) {
        throw new ApiError('Invalid scoring response format', 500, {
          received: response.data,
        })
      }

      console.log('✅ Scoring completed:', response.data.products.length, 'products')

      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        `Product scoring failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },

  /**
   * Health check pour module Product Discovery
   * Endpoint: GET /api/v1/products/discovery/health
   */
  async healthCheck(): Promise<{ status: string; cache_stats?: any }> {
    try {
      const response = await api.get('/api/v1/products/discovery/health')
      return response.data
    } catch (error) {
      throw new ApiError(
        `Discovery health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  },
}

/**
 * Helper: Mapper catégories frontend → Keepa category IDs
 *
 * Frontend utilise noms lisibles ("Books", "Electronics")
 * Backend/Keepa utilise IDs (3, 172, etc.)
 */
export const mapCategoryToKeepaId = (categoryName: string): number => {
  const mapping: Record<string, number> = {
    Books: 3,
    Electronics: 172,
    'Toys & Games': 193,
    'Video Games': 15,
    'Home & Kitchen': 11,
    'Computers & Accessories': 541966,
    'Sports & Outdoors': 3375251,
  }

  return mapping[categoryName] || 3 // Default to Books
}

/**
 * Helper: Valider et formater BSR range
 */
export const validateBSRRange = (
  min: number,
  max: number
): { isValid: boolean; error?: string } => {
  if (min <= 0 || max <= 0) {
    return { isValid: false, error: 'BSR doit être > 0' }
  }

  if (min >= max) {
    return { isValid: false, error: 'BSR min doit être < BSR max' }
  }

  if (max > 5000000) {
    return { isValid: false, error: 'BSR max trop élevé (max: 5M)' }
  }

  return { isValid: true }
}

/**
 * Helper: Estimer coût tokens Keepa
 *
 * Product Finder: ~1 token par requête
 * Discovery cache hit: 0 tokens
 */
export const estimateKeepaTokenCost = (cacheHit: boolean): number => {
  if (cacheHit) return 0
  return 1 // Product Finder coûte 1 token par call
}

// Export pour backward compatibility
export const discoverWithScoring = productDiscoveryService.discoverWithScoring
export const discoverOnly = productDiscoveryService.discoverOnly
export const scoreProducts = productDiscoveryService.scoreProducts
