/**
 * Types for Mes Recherches feature
 * Phase 11 - Centralized search results
 */

import type { DisplayableProduct } from './unified'

export type SearchSource = 'niche_discovery' | 'autosourcing' | 'manual_analysis'

export interface SearchResultSummary {
  id: string
  name: string
  source: SearchSource
  product_count: number
  search_params: Record<string, unknown>
  notes: string | null
  created_at: string
  expires_at: string
}

export interface SearchResultDetail extends SearchResultSummary {
  products: DisplayableProduct[]
}

export interface SearchResultListResponse {
  results: SearchResultSummary[]
  total_count: number
}

export interface SearchResultCreateRequest {
  name: string
  source: SearchSource
  products: DisplayableProduct[]
  search_params?: Record<string, unknown>
  notes?: string
}

export interface SearchResultUpdateRequest {
  name?: string
  notes?: string
}

export interface SearchResultStats {
  total: number
  niche_discovery: number
  autosourcing: number
  manual_analysis: number
}

// Source display helpers
export const SOURCE_LABELS: Record<SearchSource, string> = {
  niche_discovery: 'Niche Discovery',
  autosourcing: 'AutoSourcing',
  manual_analysis: 'Analyse Manuelle'
}

export const SOURCE_COLORS: Record<SearchSource, string> = {
  niche_discovery: 'purple',
  autosourcing: 'blue',
  manual_analysis: 'green'
}
