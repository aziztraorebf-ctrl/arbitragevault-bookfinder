/**
 * React Query hooks for Configuration
 * Phase 9 - UI Completion
 *
 * Configuration:
 * - staleTime (effective): 5 min - config rarely changes
 * - staleTime (stats): 1 min - stats can change more often
 * - retry: 3 attempts for effective, 2 for stats (no retry on 4xx client errors)
 * - retryDelay: Exponential backoff, max 30s
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'
import { toast } from 'react-hot-toast'

// Retry configuration constants
const MAX_RETRY_EFFECTIVE = 3 // More retries for critical config data
const MAX_RETRY_STATS = 2     // Fewer retries for non-critical stats
const MAX_RETRY_DELAY_MS = 30000 // Cap retry delay at 30 seconds

// Query keys factory pattern - consistent with other hooks
export const configQueryKeys = {
  all: ['config'] as const,
  effective: (domainId: number, category: string) =>
    [...configQueryKeys.all, 'effective', domainId, category] as const,
  stats: () => [...configQueryKeys.all, 'stats'] as const,
}

// Hook for fetching effective configuration
export function useEffectiveConfig(domainId: number = 1, category: string = 'books') {
  return useQuery({
    queryKey: configQueryKeys.effective(domainId, category),
    queryFn: () => apiService.getConfig(domainId, category),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx client errors
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < MAX_RETRY_EFFECTIVE
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, MAX_RETRY_DELAY_MS),
    meta: {
      errorMessage: 'Failed to load configuration',
    },
  })
}

// Hook for fetching configuration stats
export function useConfigStats() {
  return useQuery({
    queryKey: configQueryKeys.stats(),
    queryFn: () => apiService.getConfigStats(),
    staleTime: 60 * 1000, // 1 minute
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < MAX_RETRY_STATS
    },
    meta: {
      errorMessage: 'Failed to load configuration stats',
    },
  })
}

// Hook for updating configuration (mutation)
export function useUpdateConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ scope, request }: { scope: string; request: Record<string, unknown> }) =>
      apiService.updateConfig(scope, request),
    onSuccess: () => {
      // Invalidate all config queries to refresh data
      queryClient.invalidateQueries({ queryKey: configQueryKeys.all })
      toast.success('Configuration mise a jour')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Erreur lors de la mise a jour'
      toast.error(message)
    },
  })
}

export default useEffectiveConfig
