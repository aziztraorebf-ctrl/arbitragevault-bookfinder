/**
 * Phase 3 Day 9 - Niche Discovery Hooks
 * React Query hooks pour auto-discovery et manual discovery
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  nicheDiscoveryService,
  type ValidatedNiche,
  type NicheDiscoveryResponse,
  type ManualDiscoveryResponse,
  type ManualDiscoveryFilters,
  type NicheStrategy,
} from '../services/nicheDiscoveryService'

/**
 * Hook: Auto-discover curated niches
 *
 * Usage:
 * const { mutate: explore, isPending } = useAutoDiscoverNiches()
 * explore({ count: 3, shuffle: true, strategy: 'textbooks_standard' })
 */
export function useAutoDiscoverNiches() {
  const queryClient = useQueryClient()

  return useMutation<
    NicheDiscoveryResponse,
    Error,
    { count?: number; shuffle?: boolean; strategy?: NicheStrategy }
  >({
    mutationFn: async ({ count = 3, shuffle = true, strategy }) => {
      return nicheDiscoveryService.discoverAuto(count, shuffle, strategy)
    },
    onSuccess: (data) => {
      // Invalidate related queries (if any)
      queryClient.invalidateQueries({ queryKey: ['niches'] })

      console.log('[NicheDiscovery] Auto-discovery mutation success:', {
        nichesCount: data.metadata.niches_count,
        tokensConsumed: data.metadata.tokens_consumed,
      })
    },
    onError: (error) => {
      console.error('[NicheDiscovery] Auto-discovery mutation failed:', error)
    },
  })
}

/**
 * Hook: Manual discovery with filters
 *
 * Usage:
 * const { mutate: search, isPending } = useManualDiscovery()
 * search({ category: 283155, bsr_min: 10000, bsr_max: 50000 })
 */
export function useManualDiscovery() {
  const queryClient = useQueryClient()

  return useMutation<ManualDiscoveryResponse, Error, ManualDiscoveryFilters>({
    mutationFn: async (filters) => {
      return nicheDiscoveryService.discoverManual(filters)
    },
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['products'] })

      console.log('✅ Manual discovery mutation success:', {
        productsCount: data.products.length,
        cacheHit: data.cache_hit,
      })
    },
    onError: (error) => {
      console.error('❌ Manual discovery mutation failed:', error)
    },
  })
}

/**
 * Hook: Explore a specific niche (drill-down)
 *
 * Usage:
 * const { mutate: exploreNiche, isPending } = useExploreNiche()
 * exploreNiche(selectedNiche)
 */
export function useExploreNiche() {
  const queryClient = useQueryClient()

  return useMutation<ManualDiscoveryResponse, Error, ValidatedNiche>({
    mutationFn: async (niche) => {
      return nicheDiscoveryService.exploreNiche(niche)
    },
    onSuccess: (data, niche) => {
      // Invalidate products queries
      queryClient.invalidateQueries({ queryKey: ['products'] })

      console.log(`✅ Niche exploration success (${niche.id}):`, {
        productsCount: data.products.length,
      })
    },
    onError: (error) => {
      console.error('❌ Niche exploration failed:', error)
    },
  })
}

/**
 * Helper hook: Combined state for Niche Discovery page
 *
 * Manages niches, products, and drill-down state
 */
export function useNicheDiscoveryState() {
  const autoDiscoverMutation = useAutoDiscoverNiches()
  const manualDiscoveryMutation = useManualDiscovery()
  const exploreNicheMutation = useExploreNiche()

  return {
    // Auto-discovery
    discoverAuto: autoDiscoverMutation.mutate,
    isDiscoveringAuto: autoDiscoverMutation.isPending,
    autoDiscoveryData: autoDiscoverMutation.data,
    autoDiscoveryError: autoDiscoverMutation.error,

    // Manual discovery
    discoverManual: manualDiscoveryMutation.mutate,
    isDiscoveringManual: manualDiscoveryMutation.isPending,
    manualDiscoveryData: manualDiscoveryMutation.data,
    manualDiscoveryError: manualDiscoveryMutation.error,

    // Niche exploration
    exploreNiche: exploreNicheMutation.mutate,
    isExploringNiche: exploreNicheMutation.isPending,
    nicheExplorationData: exploreNicheMutation.data,
    nicheExplorationError: exploreNicheMutation.error,

    // Combined loading state
    isLoading:
      autoDiscoverMutation.isPending ||
      manualDiscoveryMutation.isPending ||
      exploreNicheMutation.isPending,

    // Reset function
    reset: () => {
      autoDiscoverMutation.reset()
      manualDiscoveryMutation.reset()
      exploreNicheMutation.reset()
    },
  }
}
