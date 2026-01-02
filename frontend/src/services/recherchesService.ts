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
   */
  async getById(id: string): Promise<SearchResultDetail> {
    try {
      const response = await api.get(`/api/v1/recherches/${id}`)
      return response.data
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
