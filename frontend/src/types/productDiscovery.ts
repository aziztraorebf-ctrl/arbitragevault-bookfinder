/**
 * Phase 3 - Product Discovery Types
 * Types TypeScript et Zod schemas pour Product Discovery MVP
 */

import { z } from 'zod'

// ============================================================
// ZOD SCHEMAS - Runtime Validation
// ============================================================

/**
 * Request schema pour product discovery
 */
export const ProductDiscoveryRequestSchema = z.object({
  categories: z.array(z.string()).min(1, 'Au moins une catégorie requise'),
  bsr_range: z.tuple([
    z.number().int().positive(),
    z.number().int().positive()
  ]).refine(
    ([min, max]) => min < max,
    'BSR min doit être inférieur à BSR max'
  ),
  price_range: z.tuple([
    z.number().positive(),
    z.number().positive()
  ]).optional(),
  discount_min: z.number().int().min(0).max(100).optional(),
  availability: z.enum(['amazon', 'any', 'fba']).optional(),
  max_results: z.number().int().positive().max(100).default(50),
})

/**
 * Product score schema (résultat scoring individuel)
 */
export const ProductScoreSchema = z.object({
  asin: z.string(),
  title: z.string(),
  price: z.number().nullable(),
  bsr: z.number().int().nullable(),
  roi_percent: z.number(),
  velocity_score: z.number().min(0).max(100),
  stability_score: z.number().min(0).max(100).optional(),
  confidence_score: z.number().min(0).max(100).optional(),
  recommendation: z.enum(['STRONG_BUY', 'BUY', 'CONSIDER', 'SKIP']),
  overall_rating: z.string(),
  image_url: z.string().url().nullable().optional(),
})

/**
 * Response schema pour product discovery avec scoring
 */
export const ProductDiscoveryResponseSchema = z.object({
  products: z.array(ProductScoreSchema),
  total_count: z.number().int(),
  cache_hit: z.boolean(),
  metadata: z.object({
    filters_applied: z.record(z.string(), z.any()),
    execution_time_ms: z.number(),
    discovery_source: z.enum(['cache', 'keepa_api']).optional(),
  }),
})

/**
 * Discovery-only response schema (sans scoring)
 */
export const DiscoveryOnlyResponseSchema = z.object({
  asins: z.array(z.string()),
  total_count: z.number().int(),
  cache_hit: z.boolean(),
  metadata: z.object({
    filters_applied: z.record(z.string(), z.any()),
    execution_time_ms: z.number(),
  }),
})

/**
 * Scoring-only request schema
 */
export const ScoringRequestSchema = z.object({
  asins: z.array(z.string()).min(1).max(100),
  force_refresh: z.boolean().optional().default(false),
})

/**
 * Keepa Product Finder filters schema
 */
export const KeepaFiltersSchema = z.object({
  categoryId: z.number().int().positive(),
  bsrMin: z.number().int().positive(),
  bsrMax: z.number().int().positive(),
  priceMin: z.number().positive().optional(),
  priceMax: z.number().positive().optional(),
  availability: z.enum(['amazon', 'any', 'fba']).optional(),
  discountMin: z.number().int().min(0).max(100).optional(),
})

// ============================================================
// TYPESCRIPT TYPES - Inferred from Zod
// ============================================================

export type ProductDiscoveryRequest = z.infer<typeof ProductDiscoveryRequestSchema>
export type ProductScore = z.infer<typeof ProductScoreSchema>
export type ProductDiscoveryResponse = z.infer<typeof ProductDiscoveryResponseSchema>
export type DiscoveryOnlyResponse = z.infer<typeof DiscoveryOnlyResponseSchema>
export type ScoringRequest = z.infer<typeof ScoringRequestSchema>
export type KeepaFilters = z.infer<typeof KeepaFiltersSchema>

// ============================================================
// UI STATE TYPES (non-validés par Zod)
// ============================================================

/**
 * État du formulaire de filtres (UI state)
 */
export interface DiscoveryFormState {
  selectedCategories: string[]
  bsrMin: number
  bsrMax: number
  priceMin?: number
  priceMax?: number
  discountMin?: number
  availability?: 'amazon' | 'any' | 'fba'
  maxResults: number
}

/**
 * État de la recherche (loading, results, error)
 */
export interface DiscoverySearchState {
  status: 'idle' | 'loading' | 'success' | 'error'
  products: ProductScore[]
  totalCount: number
  cacheHit: boolean
  executionTimeMs?: number
  error?: string
  lastSearchFilters?: ProductDiscoveryRequest
}

/**
 * Catégories Keepa disponibles pour le frontend
 */
export interface KeepaCategory {
  id: number
  name: string
  parentId?: number
}

/**
 * Options de tri pour les résultats
 */
export type SortOption =
  | 'roi_desc'
  | 'roi_asc'
  | 'velocity_desc'
  | 'velocity_asc'
  | 'bsr_asc'
  | 'bsr_desc'
  | 'price_asc'
  | 'price_desc'

/**
 * Options de filtrage post-recherche
 */
export interface ResultsFilterOptions {
  minROI?: number
  maxROI?: number
  minVelocity?: number
  maxVelocity?: number
  recommendationFilter?: Array<'STRONG_BUY' | 'BUY' | 'CONSIDER' | 'SKIP'>
}

// ============================================================
// CONSTANTS
// ============================================================

/**
 * Catégories Keepa populaires (Books = 3, Electronics = 172, etc.)
 * Mapping simplifié pour le MVP
 */
export const POPULAR_KEEPA_CATEGORIES: KeepaCategory[] = [
  { id: 3, name: 'Books' },
  { id: 172, name: 'Electronics' },
  { id: 193, name: 'Toys & Games' },
  { id: 15, name: 'Video Games' },
  { id: 11, name: 'Home & Kitchen' },
]

/**
 * Options de disponibilité (Keepa availability filter)
 */
export const AVAILABILITY_OPTIONS = [
  { value: 'amazon', label: 'Amazon uniquement' },
  { value: 'any', label: 'Tous les vendeurs' },
  { value: 'fba', label: 'FBA seulement' },
] as const

/**
 * Labels pour recommandations
 */
export const RECOMMENDATION_LABELS: Record<string, { label: string; color: string }> = {
  STRONG_BUY: { label: 'Achat Fort', color: 'green' },
  BUY: { label: 'Acheter', color: 'blue' },
  CONSIDER: { label: 'Considérer', color: 'yellow' },
  SKIP: { label: 'Passer', color: 'red' },
}

/**
 * Ranges BSR par défaut pour Books
 */
export const DEFAULT_BSR_RANGES = {
  books: {
    excellent: [1, 10000],
    good: [10000, 50000],
    fair: [50000, 150000],
    risky: [150000, 500000],
  },
  electronics: {
    excellent: [1, 5000],
    good: [5000, 25000],
    fair: [25000, 100000],
    risky: [100000, 300000],
  },
} as const
