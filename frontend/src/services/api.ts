import axios from 'axios'

// Auto-detect API base URL (local development vs production)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Health check endpoint
export const healthCheck = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    throw new Error(`Backend connection failed: ${API_BASE_URL}`)
  }
}

// Additional imports for analysis functionality
import type { BatchAPIResponse, ConfiguredAnalysis } from '../types'

// Generate UUID for batch tracking
export const generateBatchId = (): string => {
  return 'batch_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// Keepa Analysis API - Main function for Phase 3
export const runAnalysis = async (configuredAnalysis: ConfiguredAnalysis): Promise<BatchAPIResponse> => {
  const batch_id = generateBatchId()
  
  const requestPayload = {
    identifiers: configuredAnalysis.asins,
    batch_id,
    config_profile: 'default',
    force_refresh: false,
    async_threshold: 100 // Use sync mode for UI progress
  }

  console.log('Starting Keepa analysis:', {
    asins_count: configuredAnalysis.asins.length,
    strategy: configuredAnalysis.strategy.name,
    batch_id
  })

  const response = await api.post('/api/v1/keepa/ingest', requestPayload)
  return response.data
}