import axios from 'axios'
import { z } from 'zod'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Type-safe API client
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Custom API Error class
export class ApiError extends Error {
  status?: number
  data?: any

  constructor(
    message: string,
    status?: number,
    data?: any
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(new ApiError('Request failed', undefined, error))
  }
)

// Response interceptor with proper error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const message = error.response?.data?.message || error.response?.data?.detail || error.message
    const status = error.response?.status
    const data = error.response?.data
    
    console.error('API Response Error:', { message, status, data })
    throw new ApiError(message, status, data)
  }
)

// Zod schemas for validation - conformes à l'OpenAPI
const BatchResultSchema = z.object({
  identifier: z.string(),
  asin: z.string().nullable(),
  status: z.enum(['success', 'error', 'not_found']),
  analysis: z.any().nullable(),
  error: z.string().nullable(),
})

const IngestResponseSchema = z.object({
  batch_id: z.string(),
  total_items: z.number(),
  processed: z.number(),
  successful: z.number(),
  failed: z.number(),
  results: z.array(BatchResultSchema),
  job_id: z.string().nullable().optional(),
  status_url: z.string().nullable().optional(),
  trace_id: z.string(),
})

const BatchSchema = z.object({
  batch_id: z.string(),
  total_items: z.number(),
  processed_items: z.number(),
  successful_items: z.number(),
  failed_items: z.number(),
  status: z.enum(['pending', 'processing', 'completed', 'failed', 'partial']),
  created_at: z.string(),
  updated_at: z.string(),
  results: z.array(z.object({
    asin: z.string(),
    status: z.enum(['success', 'error', 'not_found']),
    analysis: z.any().optional(),
    error: z.string().optional(),
  })).optional(),
})

const BatchListSchema = z.object({
  batches: z.array(BatchSchema),
  total: z.number(),
  page: z.number(),
  size: z.number(),
  has_next: z.boolean(),
  has_prev: z.boolean(),
})

const HealthSchema = z.object({
  status: z.string(),
  timestamp: z.string(),
  version: z.string().optional(),
})

// Type definitions - Inferred from Zod schemas
export type Batch = z.infer<typeof BatchSchema>
export type BatchList = z.infer<typeof BatchListSchema>
export type IngestResponse = z.infer<typeof IngestResponseSchema>
export type HealthCheck = z.infer<typeof HealthSchema>

// API Functions - Typed and validated
export const apiService = {
  // Health check
  async healthCheck(): Promise<HealthCheck> {
    try {
      const response = await api.get('/api/v1/health/ready')
      
      const healthData = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: response.data?.version,
      }
      
      // Safe parse with proper error handling
      const result = HealthSchema.safeParse(healthData)
      if (!result.success) {
        throw new ApiError('Invalid health check response format', 500, {
          zodErrors: result.error.issues,
          received: healthData
        })
      }
      
      return result.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  },

  // Get all batches with pagination
  async getBatches(page: number = 1, size: number = 20): Promise<BatchList> {
    try {
      const response = await api.get('/api/v1/batches/', {
        params: { page, size }
      })
      
      // Safe parse with proper error handling
      const result = BatchListSchema.safeParse(response.data)
      if (!result.success) {
        throw new ApiError('Invalid response format from server', 500, {
          zodErrors: result.error.issues,
          received: response.data
        })
      }
      
      return result.data as BatchList
    } catch (error) {
      throw error // Re-throw as ApiError already handled above
    }
  },

  // Get single batch by ID
  async getBatch(batchId: string): Promise<Batch> {
    try {
      const response = await api.get(`/api/v1/batches/${batchId}`)
      
      // Safe parse with proper error handling  
      const result = BatchSchema.safeParse(response.data)
      if (!result.success) {
        throw new ApiError('Invalid batch data format', 500, {
          zodErrors: result.error.issues,
          received: response.data
        })
      }
      
      return result.data as Batch
    } catch (error) {
      throw error
    }
  },

  // Run analysis (for keepa ingest)
  async runAnalysis(identifiers: string[], config_profile: string = 'default'): Promise<IngestResponse> {
    try {
      const batch_id = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      const response = await api.post('/api/v1/keepa/ingest', {
        identifiers,
        batch_id,
        config_profile,
        force_refresh: false,
        async_threshold: 100
      })
      
      // Safe parse with correct schema
      const result = IngestResponseSchema.safeParse(response.data)
      if (!result.success) {
        throw new ApiError('Invalid ingest response format', 500, {
          zodErrors: result.error.issues,
          received: response.data
        })
      }
      
      return result.data
    } catch (error) {
      throw error
    }
  },
}

// Export functions for backward compatibility
export const healthCheck = apiService.healthCheck
export const getBatches = apiService.getBatches
export const getBatch = apiService.getBatch
export const runAnalysis = apiService.runAnalysis