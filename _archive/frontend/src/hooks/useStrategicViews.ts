/**
 * React Query hooks for Strategic Views
 * Phase 9 - UI Completion
 *
 * Configuration:
 * - staleTime (allViews): 5 min - list of views rarely changes
 * - staleTime (specificView): 2 min - view data updates more frequently
 * - staleTime (targetPrices): 5 min - prices don't change rapidly
 * - retry: 3 attempts for views, 2 for target prices (no retry on 4xx)
 * - retryDelay: Exponential backoff, max 30s
 */
import { useQuery } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'
import type { ViewType, StrategicViewResponse, TargetPrices } from '../types/strategic'

// Retry configuration constants
const MAX_RETRY_VIEWS = 3          // More retries for critical view data
const MAX_RETRY_TARGET_PRICES = 2  // Fewer retries for supplementary data
const MAX_RETRY_DELAY_MS = 30000   // Cap retry delay at 30 seconds

// Query keys factory pattern - consistent with other hooks
export const strategicQueryKeys = {
  all: ['strategic'] as const,
  views: () => [...strategicQueryKeys.all, 'views'] as const,
  view: (type: ViewType, niches?: string[]) =>
    [...strategicQueryKeys.views(), type, niches] as const,
  targetPrices: (type: ViewType) =>
    [...strategicQueryKeys.all, 'targetPrices', type] as const,
}

// Hook for fetching all available strategic views
export function useAllStrategicViews() {
  return useQuery({
    queryKey: strategicQueryKeys.views(),
    queryFn: () => apiService.getAllStrategicViews(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx client errors
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < MAX_RETRY_VIEWS
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, MAX_RETRY_DELAY_MS),
    meta: {
      errorMessage: 'Failed to load strategic views',
    },
  })
}

// Hook for fetching a specific strategic view
export function useStrategicView(viewType: ViewType, niches?: string[]) {
  return useQuery<StrategicViewResponse>({
    queryKey: strategicQueryKeys.view(viewType, niches),
    queryFn: () => apiService.getStrategicView(viewType, niches),
    staleTime: 2 * 60 * 1000, // 2 min - view data can change more frequently
    enabled: !!viewType,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < MAX_RETRY_VIEWS
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, MAX_RETRY_DELAY_MS),
    meta: {
      errorMessage: `Failed to load ${viewType} view`,
    },
  })
}

// Hook for fetching target prices for a specific view
export function useTargetPrices(viewType: ViewType) {
  return useQuery<TargetPrices>({
    queryKey: strategicQueryKeys.targetPrices(viewType),
    queryFn: () => apiService.getTargetPrices(viewType),
    staleTime: 5 * 60 * 1000, // 5 min - target prices don't change rapidly
    enabled: !!viewType,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < MAX_RETRY_TARGET_PRICES
    },
    meta: {
      errorMessage: 'Failed to load target prices',
    },
  })
}

export default useStrategicView
