import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'
import { toast } from 'react-hot-toast'

// Query keys factory pattern - Context7 recommended approach
export const batchesQueryKeys = {
  all: ['batches'] as const,
  lists: () => [...batchesQueryKeys.all, 'list'] as const,
  list: (filters: { page: number; size: number }) => [...batchesQueryKeys.lists(), filters] as const,
  details: () => [...batchesQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...batchesQueryKeys.details(), id] as const,
}

// Hook for fetching paginated batches - Context7 pattern
export const useBatches = (page: number = 1, size: number = 20) => {
  return useQuery({
    queryKey: batchesQueryKeys.list({ page, size }),
    queryFn: ({ queryKey }) => {
      const [, , filters] = queryKey
      return apiService.getBatches(filters.page, filters.size)
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: (failureCount, error) => {
      // Context7 pattern: Don't retry on 4xx client errors
      if (error instanceof ApiError && error.status) {
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      return failureCount < 3 // Allow more retries for server errors
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    meta: {
      errorMessage: 'Failed to load batches',
    },
  })
}

// Hook for fetching single batch
export const useBatch = (batchId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: batchesQueryKeys.detail(batchId),
    queryFn: () => apiService.getBatch(batchId),
    enabled: enabled && !!batchId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) {
        return false
      }
      return failureCount < 2
    },
    meta: {
      errorMessage: `Failed to load batch ${batchId}`,
    },
  })
}

// Hook for running new analysis (mutation)
export const useRunAnalysis = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ identifiers, config_profile }: { identifiers: string[], config_profile?: string }) =>
      apiService.runAnalysis(identifiers, config_profile),
    onSuccess: (data) => {
      // Invalidate batches queries to refresh the list
      queryClient.invalidateQueries({ queryKey: batchesQueryKeys.lists() })
      
      // Add the new batch to cache
      queryClient.setQueryData(
        batchesQueryKeys.detail(data.batch_id),
        data
      )
      
      toast.success(`Analysis started successfully (${data.batch_id})`)
    },
    onError: (error) => {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to start analysis'
      toast.error(message)
    },
  })
}

// Hook for batch statistics (derived from batches list)
export const useBatchesStats = (page: number = 1, size: number = 100) => {
  const { data: batchesData, ...queryState } = useBatches(page, size)
  
  const stats = {
    total: batchesData?.total || 0,
    completed: batchesData?.batches?.filter(b => b.status === 'completed').length || 0,
    processing: batchesData?.batches?.filter(b => b.status === 'processing').length || 0,
    failed: batchesData?.batches?.filter(b => b.status === 'failed').length || 0,
    successRate: 0,
    totalProcessedItems: 0,
    totalSuccessfulItems: 0,
  }
  
  if (batchesData?.batches) {
    const totalItems = batchesData.batches.reduce((sum, batch) => sum + batch.total_items, 0)
    const successfulItems = batchesData.batches.reduce((sum, batch) => sum + batch.successful_items, 0)
    
    stats.successRate = totalItems > 0 ? Math.round((successfulItems / totalItems) * 100) : 0
    stats.totalProcessedItems = batchesData.batches.reduce((sum, batch) => sum + batch.processed_items, 0)
    stats.totalSuccessfulItems = successfulItems
  }
  
  return {
    stats,
    ...queryState,
  }
}

export default useBatches