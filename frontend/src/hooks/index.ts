// Centralized exports for all custom hooks

export {
  useHealthCheck,
  useConnectionStatus,
  healthCheckQueryKeys
} from './useHealthCheck'

export {
  useEffectiveConfig,
  useConfigStats,
  useUpdateConfig,
  configQueryKeys
} from './useConfig'

export {
  useStockEstimate,
  stockKeys
} from './useStockEstimate'

export { useMobileMenu } from './useMobileMenu'

export { useOnboarding } from './useOnboarding'

export {
  useDashboardData,
  dashboardKeys
} from './useDashboardData'

// Re-export types for convenience
export type { HealthCheck, ApiError } from '../services/api'
