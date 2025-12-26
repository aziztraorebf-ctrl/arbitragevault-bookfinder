// Centralized exports for all custom hooks

export {
  useBatches,
  useBatch,
  useRunAnalysis,
  useBatchesStats,
  batchesQueryKeys
} from './useBatches'

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
  useAllStrategicViews,
  useStrategicView,
  useTargetPrices,
  strategicQueryKeys
} from './useStrategicViews'

export {
  useStockEstimate,
  stockKeys
} from './useStockEstimate'

// Re-export types for convenience
export type { Batch, BatchList, HealthCheck, ApiError } from '../services/api'