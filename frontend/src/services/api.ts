import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { z } from 'zod'
import { getIdToken, getIdTokenForced } from '../config/firebase'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Type-safe API client
// Timeout: 300s (5 min) pour supporter jusqu'a 200 ASINs
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 300 secondes = 5 minutes (supporte 200+ ASINs)
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

// Request interceptor - Add Firebase token to all requests
api.interceptors.request.use(
  async (config) => {
    // Get Firebase ID token if user is logged in
    try {
      const token = await getIdToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (error) {
      // Token fetch failed - continue without auth (will fail on protected endpoints)
      console.warn('Failed to get Firebase token:', error)
    }

    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(new ApiError('Request failed', undefined, error))
  }
)

// Flag to prevent infinite retry loops
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string | null) => void
  reject: (error: Error) => void
}> = []

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Response interceptor with token refresh on 401
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Force refresh the Firebase token
        const newToken = await getIdTokenForced()

        if (newToken) {
          // Update the failed request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
          }

          // Process queued requests
          processQueue(null, newToken)

          // Retry the original request
          return api(originalRequest)
        } else {
          // No token available - user needs to re-login
          processQueue(new Error('No token available'), null)
          // Redirect to login handled by AuthContext
        }
      } catch (refreshError) {
        processQueue(refreshError as Error, null)
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Standard error handling for non-401 errors
    let message = (error.response?.data as { message?: string; detail?: string })?.message ||
      (error.response?.data as { message?: string; detail?: string })?.detail ||
      error.message

    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      message = 'L\'analyse prend plus de temps que prevu. Essayez avec moins de produits ou reessayez plus tard.'
    }

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
  async runAnalysis(
    identifiers: string[],
    config_profile: string = 'default',
    conditionFilter?: string[]
  ): Promise<IngestResponse> {
    try {
      const batch_id = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      // Build query params if conditionFilter provided
      const params: Record<string, string> = {}
      if (conditionFilter && conditionFilter.length > 0) {
        params.condition_filter = conditionFilter.join(',')
      }

      const response = await api.post('/api/v1/keepa/ingest', {
        identifiers,
        batch_id,
        config_profile,
        force_refresh: false,
        async_threshold: 100
      }, { params })
      
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

  // Phase 8.0 Analytics - Product Decision
  async getProductDecision(asin: string): Promise<any> {
    try {
      const response = await api.post('/api/v1/analytics/product-decision', {
        asin,
        estimated_buy_price: 5.00,
        estimated_sell_price: 19.99,
      })
      return response.data
    } catch (error) {
      throw error
    }
  },

  // Phase 8.0 Analytics - ASIN Historical Trends
  async getASINTrends(asin: string, days: number = 90): Promise<any> {
    try {
      const response = await api.get(`/api/v1/asin-history/trends/${asin}`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      throw error
    }
  },

  // Phase 8.0 Analytics - ASIN Historical Records
  async getASINHistory(asin: string, days: number = 30, limit: number = 100): Promise<any> {
    try {
      const response = await api.get(`/api/v1/asin-history/records/${asin}`, {
        params: { days, limit }
      })
      return response.data
    } catch (error) {
      throw error
    }
  },

  // ===== Phase 9: Configuration Endpoints =====

  async getConfig(domainId: number = 1, category: string = 'books'): Promise<any> {
    const response = await api.get('/api/v1/config/', {
      params: { domain_id: domainId, category, force_refresh: false }
    })
    return response.data
  },

  async updateConfig(scope: string, request: any): Promise<any> {
    const response = await api.put('/api/v1/config/', request, {
      params: { scope }
    })
    return response.data
  },

  async getConfigStats(): Promise<any> {
    const response = await api.get('/api/v1/config/stats')
    return response.data
  },

  // ===== Phase 9: Strategic Views Endpoints =====

  async getStrategicView(viewType: string, niches?: string[]): Promise<any> {
    const response = await api.get(`/api/v1/strategic-views/${viewType}`, {
      params: niches ? { niches: niches.join(',') } : {}
    })
    return response.data
  },

  async getAllStrategicViews(): Promise<any> {
    const response = await api.get('/api/v1/strategic-views/')
    return response.data
  },

  async getTargetPrices(viewType: string): Promise<any> {
    const response = await api.get(`/api/v1/strategic-views/${viewType}/target-prices`)
    return response.data
  },

  // ===== Phase 9: Stock Estimates Endpoint =====

  async getStockEstimate(asin: string): Promise<any> {
    const response = await api.get(`/api/v1/products/${asin}/stock-estimate`)
    return response.data
  },
}

// Export functions for backward compatibility
export const healthCheck = apiService.healthCheck
export const getBatches = apiService.getBatches
export const getBatch = apiService.getBatch
export const runAnalysis = (
  identifiers: string[],
  config_profile: string = 'default',
  conditionFilter?: string[]
) => apiService.runAnalysis(identifiers, config_profile, conditionFilter)