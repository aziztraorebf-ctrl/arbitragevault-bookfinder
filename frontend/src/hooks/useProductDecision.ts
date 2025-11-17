import { useQuery } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'
import type { ProductDecision, ASINTrends } from '../types/analytics'

/**
 * Query keys factory for Phase 8.0 Analytics
 * Context7 recommended pattern for React Query
 */
export const analyticsQueryKeys = {
  all: ['analytics'] as const,
  decisions: () => [...analyticsQueryKeys.all, 'decision'] as const,
  decision: (asin: string) => [...analyticsQueryKeys.decisions(), asin] as const,
  trends: () => [...analyticsQueryKeys.all, 'trends'] as const,
  trend: (asin: string, days: number) => [...analyticsQueryKeys.trends(), asin, days] as const,
}

/**
 * Hook for fetching product decision analytics
 *
 * Fetches comprehensive analytics from Phase 8.0 backend:
 * - Velocity intelligence and BSR trends
 * - Price stability analysis
 * - ROI net calculation with all fees
 * - Competition analysis
 * - Risk score (5 components)
 * - Final recommendation (5-tier)
 */
export const useProductDecision = (asin: string, enabled: boolean = true) => {
  return useQuery<ProductDecision>({
    queryKey: analyticsQueryKeys.decision(asin),
    queryFn: () => apiService.getProductDecision(asin),
    enabled: enabled && !!asin,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < 2
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    meta: {
      errorMessage: `Failed to load decision analytics for ${asin}`,
    },
  })
}

/**
 * Hook for fetching historical ASIN trends
 *
 * Fetches BSR, price, and seller count trends from ASINHistory table
 */
export const useASINTrends = (
  asin: string,
  days: number = 90,
  enabled: boolean = true
) => {
  return useQuery<ASINTrends>({
    queryKey: analyticsQueryKeys.trend(asin, days),
    queryFn: () => apiService.getASINTrends(asin, days),
    enabled: enabled && !!asin,
    staleTime: 10 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) {
        return false
      }
      return failureCount < 2
    },
    meta: {
      errorMessage: `Failed to load trends for ${asin}`,
    },
  })
}
