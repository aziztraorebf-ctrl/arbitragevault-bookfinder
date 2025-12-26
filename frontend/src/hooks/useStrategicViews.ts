/**
 * React Query hooks for Strategic Views
 * Phase 9 - UI Completion
 */
import { useQuery } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'
import type { ViewType, StrategicViewResponse, TargetPrices } from '../types/strategic'

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
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
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
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!viewType,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
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
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!viewType,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < 2
    },
    meta: {
      errorMessage: 'Failed to load target prices',
    },
  })
}

export default useStrategicView
