/**
 * React Query hooks for Recherches feature
 * Phase 11 - Centralized search results
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { recherchesService } from '../services/recherchesService'
import type {
  SearchResultCreateRequest,
  SearchResultUpdateRequest,
  SearchSource
} from '../types/recherches'

// Query keys
export const recherchesKeys = {
  all: ['recherches'] as const,
  lists: () => [...recherchesKeys.all, 'list'] as const,
  list: (source?: SearchSource) => [...recherchesKeys.lists(), { source }] as const,
  details: () => [...recherchesKeys.all, 'detail'] as const,
  detail: (id: string) => [...recherchesKeys.details(), id] as const,
  stats: () => [...recherchesKeys.all, 'stats'] as const,
}

/**
 * Hook to list search results with optional source filter
 */
export function useRecherches(source?: SearchSource) {
  return useQuery({
    queryKey: recherchesKeys.list(source),
    queryFn: () => recherchesService.list({ source }),
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Hook to get search result detail with products
 */
export function useRechercheDetail(id: string) {
  return useQuery({
    queryKey: recherchesKeys.detail(id),
    queryFn: () => recherchesService.getById(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Hook to get search result statistics
 */
export function useRechercheStats() {
  return useQuery({
    queryKey: recherchesKeys.stats(),
    queryFn: () => recherchesService.getStats(),
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Hook to create a new search result
 */
export function useCreateRecherche() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SearchResultCreateRequest) => recherchesService.create(data),
    onSuccess: () => {
      // Invalidate list and stats
      queryClient.invalidateQueries({ queryKey: recherchesKeys.lists() })
      queryClient.invalidateQueries({ queryKey: recherchesKeys.stats() })
    },
  })
}

/**
 * Hook to update a search result
 */
export function useUpdateRecherche() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SearchResultUpdateRequest }) =>
      recherchesService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: recherchesKeys.detail(variables.id) })
      queryClient.invalidateQueries({ queryKey: recherchesKeys.lists() })
    },
  })
}

/**
 * Hook to delete a search result
 */
export function useDeleteRecherche() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => recherchesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recherchesKeys.lists() })
      queryClient.invalidateQueries({ queryKey: recherchesKeys.stats() })
    },
  })
}
