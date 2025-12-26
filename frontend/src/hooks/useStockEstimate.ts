import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

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
    staleTime: 5 * 60 * 1000, // 5 min
    enabled: !!asin && asin.length >= 10,
    retry: (failureCount, error: any) => {
      // Don't retry on 404 (ASIN not found)
      if (error?.status === 404) return false
      return failureCount < 2
    },
  })
}
