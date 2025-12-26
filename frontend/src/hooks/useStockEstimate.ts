/**
 * Stock Estimate Hook
 * Fetches FBA stock estimation for a given ASIN.
 *
 * Configuration:
 * - staleTime: 5 minutes (stock doesn't change frequently)
 * - retry: 2 attempts max, no retry on 404 (ASIN not found is not transient)
 * - enabled: Only when ASIN is 10+ chars (Amazon ASIN standard length)
 */
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

// ASIN length requirement: Amazon ASINs are exactly 10 characters (e.g., B08N5WRWNW)
const ASIN_MIN_LENGTH = 10

// Retry configuration: 2 attempts before giving up (balances UX vs API load)
const MAX_RETRY_COUNT = 2

// Query keys factory
export const stockKeys = {
  all: ['stock'] as const,
  estimate: (asin: string) => [...stockKeys.all, 'estimate', asin] as const,
}

// Get stock estimate for ASIN
export function useStockEstimate(asin: string) {
  return useQuery({
    queryKey: stockKeys.estimate(asin),
    queryFn: () => apiService.getStockEstimate(asin),
    staleTime: 5 * 60 * 1000, // 5 min - stock estimation doesn't change frequently
    enabled: !!asin && asin.length >= ASIN_MIN_LENGTH,
    retry: (failureCount, error: Error & { status?: number }) => {
      // Don't retry on 404 (ASIN not found is a definitive answer, not transient)
      if (error?.status === 404) return false
      return failureCount < MAX_RETRY_COUNT
    },
  })
}
