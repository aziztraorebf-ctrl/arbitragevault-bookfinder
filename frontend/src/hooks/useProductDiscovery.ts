/**
 * Phase 3 - Product Discovery React Query Hooks
 * Hooks pour discovery et scoring produits avec cache frontend
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productDiscoveryService } from '../services/productDiscoveryService'
import type {
  ProductDiscoveryRequest,
  ProductDiscoveryResponse,
  DiscoveryOnlyResponse,
  ScoringRequest,
  ProductScore,
} from '../types/productDiscovery'
import toast from 'react-hot-toast'

// ============================================================
// QUERY KEYS - Centralisé pour invalidation
// ============================================================

export const productDiscoveryKeys = {
  all: ['product-discovery'] as const,
  discoverWithScoring: (filters: ProductDiscoveryRequest) =>
    ['product-discovery', 'with-scoring', filters] as const,
  discoverOnly: (filters: ProductDiscoveryRequest) =>
    ['product-discovery', 'asins-only', filters] as const,
  scoring: (asins: string[]) => ['product-discovery', 'scoring', asins] as const,
  health: () => ['product-discovery', 'health'] as const,
}

// ============================================================
// HOOKS - Discovery avec Scoring
// ============================================================

/**
 * Hook principal: Discovery + Scoring en une requête
 *
 * @param filters - Filtres de recherche (catégories, BSR, prix)
 * @param options - Options React Query (enabled, onSuccess, etc.)
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDiscoverWithScoring({
 *   categories: ['Books'],
 *   bsr_range: [10000, 50000],
 *   max_results: 50,
 * })
 * ```
 */
export function useDiscoverWithScoring(
  filters: ProductDiscoveryRequest,
  options?: {
    enabled?: boolean
    onSuccess?: (data: ProductDiscoveryResponse) => void
    onError?: (error: Error) => void
  }
) {
  return useQuery({
    queryKey: productDiscoveryKeys.discoverWithScoring(filters),
    queryFn: () => productDiscoveryService.discoverWithScoring(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes frontend cache
    gcTime: 30 * 60 * 1000, // 30 minutes (remplace cacheTime)
    enabled: options?.enabled !== false && filters.categories.length > 0,
    retry: 2,
    ...options,
  })
}

/**
 * Hook mutation: Discovery avec Scoring (version imperative)
 *
 * Utile pour déclencher recherche via button click sans auto-fetch
 *
 * @example
 * ```tsx
 * const { mutate, isPending } = useDiscoverWithScoringMutation()
 *
 * <button onClick={() => mutate(filters)}>
 *   Rechercher
 * </button>
 * ```
 */
export function useDiscoverWithScoringMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (filters: ProductDiscoveryRequest) =>
      productDiscoveryService.discoverWithScoring(filters),
    onSuccess: (data, variables) => {
      // Invalider queries existantes
      queryClient.invalidateQueries({
        queryKey: productDiscoveryKeys.all,
      })

      // Mettre en cache le résultat pour ce filtre spécifique
      queryClient.setQueryData(
        productDiscoveryKeys.discoverWithScoring(variables),
        data
      )

      toast.success(
        `${data.products.length} produits découverts ${data.cache_hit ? '(cache)' : ''}`
      )
    },
    onError: (error: Error) => {
      console.error('Discovery mutation failed:', error)
      toast.error(error.message || 'Erreur lors de la recherche')
    },
  })
}

// ============================================================
// HOOKS - Discovery Uniquement (ASINs)
// ============================================================

/**
 * Hook: Discovery ASINs uniquement (sans scoring)
 *
 * Plus rapide si scoring pas nécessaire immédiatement
 */
export function useDiscoverOnly(
  filters: ProductDiscoveryRequest,
  options?: {
    enabled?: boolean
    onSuccess?: (data: DiscoveryOnlyResponse) => void
  }
) {
  return useQuery({
    queryKey: productDiscoveryKeys.discoverOnly(filters),
    queryFn: () => productDiscoveryService.discoverOnly(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes (ASINs changent moins)
    gcTime: 60 * 60 * 1000, // 60 minutes
    enabled: options?.enabled !== false && filters.categories.length > 0,
    retry: 2,
    ...options,
  })
}

// ============================================================
// HOOKS - Scoring Uniquement
// ============================================================

/**
 * Hook: Scoring pour liste d'ASINs
 *
 * Utile pour scorer ASINs découverts séparément
 */
export function useScoreProducts(
  request: ScoringRequest,
  options?: {
    enabled?: boolean
    onSuccess?: (data: { products: ProductScore[] }) => void
  }
) {
  return useQuery({
    queryKey: productDiscoveryKeys.scoring(request.asins),
    queryFn: () => productDiscoveryService.scoreProducts(request),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: options?.enabled !== false && request.asins.length > 0,
    retry: 2,
    ...options,
  })
}

/**
 * Hook mutation: Scoring produits (version imperative)
 */
export function useScoreProductsMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ScoringRequest) =>
      productDiscoveryService.scoreProducts(request),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        productDiscoveryKeys.scoring(variables.asins),
        data
      )

      toast.success(`${data.products.length} produits scorés`)
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Erreur lors du scoring')
    },
  })
}

// ============================================================
// HOOKS - Health Check
// ============================================================

/**
 * Hook: Health check module Product Discovery
 *
 * Vérifie disponibilité backend + stats cache
 */
export function useDiscoveryHealth(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: productDiscoveryKeys.health(),
    queryFn: () => productDiscoveryService.healthCheck(),
    staleTime: 30 * 1000, // 30 secondes
    gcTime: 60 * 1000, // 1 minute
    enabled: options?.enabled !== false,
    retry: 1,
  })
}

// ============================================================
// UTILITY HOOKS
// ============================================================

/**
 * Hook: Invalider cache Product Discovery
 *
 * Utile après changement de configuration backend
 */
export function useInvalidateDiscoveryCache() {
  const queryClient = useQueryClient()

  return () => {
    queryClient.invalidateQueries({
      queryKey: productDiscoveryKeys.all,
    })
    toast.success('Cache Product Discovery invalidé')
  }
}

/**
 * Hook: Préfetch discovery pour filtres futurs
 *
 * Améliore UX en préchargeant données avant navigation
 */
export function usePrefetchDiscovery() {
  const queryClient = useQueryClient()

  return (filters: ProductDiscoveryRequest) => {
    queryClient.prefetchQuery({
      queryKey: productDiscoveryKeys.discoverWithScoring(filters),
      queryFn: () => productDiscoveryService.discoverWithScoring(filters),
      staleTime: 5 * 60 * 1000,
    })
  }
}
