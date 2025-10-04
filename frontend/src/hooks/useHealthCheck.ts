import { useQuery } from '@tanstack/react-query'
import { apiService, ApiError } from '../services/api'

// Query keys for health check
export const healthCheckQueryKeys = {
  all: ['health'] as const,
  check: () => [...healthCheckQueryKeys.all, 'check'] as const,
}

// Hook for backend health monitoring
export const useHealthCheck = (enabled: boolean = true) => {
  return useQuery({
    queryKey: healthCheckQueryKeys.check(),
    queryFn: apiService.healthCheck,
    enabled,
    refetchInterval: 30 * 1000, // Check every 30 seconds
    staleTime: 15 * 1000, // Consider stale after 15 seconds
    retry: (failureCount, _error) => {
      // Always retry health checks, but limit attempts
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff
    meta: {
      errorMessage: 'Backend health check failed',
    },
  })
}

// Hook for connection status (derived from health check)
export const useConnectionStatus = () => {
  const { data, isError, error, isLoading, isFetching } = useHealthCheck()
  
  const status = {
    isConnected: !!data && !isError,
    isChecking: isLoading || isFetching,
    lastCheck: data?.timestamp,
    version: data?.version,
    error: error instanceof ApiError ? error.message : undefined,
  }
  
  return status
}

export default useHealthCheck