/**
 * Recherches API Service
 * Phase 11 - Centralized search results management
 */

import { api, ApiError } from './api'
import type {
  SearchResultSummary,
  SearchResultDetail,
  SearchResultListResponse,
  SearchResultCreateRequest,
  SearchResultUpdateRequest,
  SearchResultStats,
  SearchSource
} from '../types/recherches'
import type { DisplayableProduct } from '../types/unified'

/**
 * Normalize product data from backend to ensure it has required fields
 * Defensive programming for products that may have been stored with different schemas
 */
function normalizeStoredProduct(product: Record<string, unknown>): DisplayableProduct {
  return {
    // Core identity (required)
    asin: String(product.asin || product.ASIN || ''),
    title: product.title as string | null ?? null,
    source: (product.source as DisplayableProduct['source']) || 'product_score',

    // Metrics (common)
    roi_percent: Number(product.roi_percent ?? product.roi_pct ?? 0),
    velocity_score: Number(product.velocity_score ?? 0),
    bsr: product.bsr != null ? Number(product.bsr) : undefined,

    // ProductScore-specific (optional)
    score: product.score != null ? Number(product.score) : undefined,
    rank: product.rank != null ? Number(product.rank) : undefined,
    stability_score: product.stability_score != null ? Number(product.stability_score) : undefined,
    amazon_on_listing: product.amazon_on_listing as boolean | undefined,
    amazon_buybox: product.amazon_buybox as boolean | undefined,

    // NicheProduct-specific (optional)
    recommendation: product.recommendation as DisplayableProduct['recommendation'],
    current_price: product.current_price != null ? Number(product.current_price) : undefined,
    category_name: product.category_name as string | undefined,
    fba_fees: product.fba_fees != null ? Number(product.fba_fees) : undefined,
    estimated_profit: product.estimated_profit != null ? Number(product.estimated_profit) : undefined,
    fba_seller_count: product.fba_seller_count != null ? Number(product.fba_seller_count) : undefined,
  }
}

export const recherchesService = {
  /**
   * Create a new search result
   */
  async create(data: SearchResultCreateRequest): Promise<SearchResultSummary> {
    try {
      const response = await api.post('/api/v1/recherches', data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to save search result')
    }
  },

  /**
   * List search results with optional filtering
   */
  async list(params?: {
    source?: SearchSource
    limit?: number
    offset?: number
  }): Promise<SearchResultListResponse> {
    try {
      const response = await api.get('/api/v1/recherches', { params })
      return response.data
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to fetch search results')
    }
  },

  /**
   * Get search result detail with products
   * Normalizes products to ensure consistent DisplayableProduct format
   */
  async getById(id: string): Promise<SearchResultDetail> {
    try {
      const response = await api.get(`/api/v1/recherches/${id}`)
      const data = response.data

      // Normalize products to ensure they have all required fields
      return {
        ...data,
        products: Array.isArray(data.products)
          ? data.products.map((p: Record<string, unknown>) => normalizeStoredProduct(p))
          : [],
      }
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to fetch search result')
    }
  },

  /**
   * Update search result (name or notes)
   */
  async update(id: string, data: SearchResultUpdateRequest): Promise<SearchResultSummary> {
    try {
      const response = await api.patch(`/api/v1/recherches/${id}`, data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to update search result')
    }
  },

  /**
   * Delete a search result
   */
  async delete(id: string): Promise<void> {
    try {
      await api.delete(`/api/v1/recherches/${id}`)
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to delete search result')
    }
  },

  /**
   * Get statistics about stored search results
   */
  async getStats(): Promise<SearchResultStats> {
    try {
      const response = await api.get('/api/v1/recherches/stats')
      return response.data
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to fetch search stats')
    }
  },

  /**
   * Trigger cleanup of expired results
   */
  async cleanup(): Promise<{ deleted_count: number; message: string }> {
    try {
      const response = await api.post('/api/v1/recherches/cleanup')
      return response.data
    } catch (error) {
      if (error instanceof ApiError) throw error
      throw new ApiError('Failed to cleanup expired results')
    }
  },
}
