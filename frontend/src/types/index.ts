// Common types for ArbitrageVault frontend

// Phase 9: Config, Strategic, Stock types
export * from './config'
export * from './strategic'
export * from './stock'

export interface Product {
  asin: string
  title: string
  price: number
  bsr: number
  roi: number
  score: number
  category?: string
  image?: string
}

export interface AutoSchedulerConfig {
  enabled: boolean
  schedule_times: string[]
  skip_dates: string[]
  last_run: string | null
  next_run: string | null
}

export interface ApiError {
  message: string
  detail?: string
  status_code?: number
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

// Pricing detail for a specific condition
export interface PricingDetail {
  current_price: number | null
  target_buy_price: number
  roi_percentage: number | null
  net_profit: number | null
  available: boolean
  recommended: boolean
}

// API Response Types (from backend /api/v1/keepa/ingest)
export interface AnalysisAPIResult {
  asin: string
  title: string
  current_bsr?: number | null
  roi: {
    roi_percentage?: number
    is_profitable?: boolean
    net_profit?: string
    profit_tier?: string
    velocity_score?: number
    velocity_category?: string
    avg_daily_sales?: number
    current_bsr?: number
  }
  velocity: {
    velocity_score?: number
    velocity_tier?: string
    velocity_category?: string
    avg_daily_sales?: number
    current_bsr?: number
  }
  pricing?: {
    new?: PricingDetail
    very_good?: PricingDetail
    good?: PricingDetail
    acceptable?: PricingDetail
  }
  amazon_on_listing?: boolean
  amazon_buybox?: boolean
  overall_rating: string
  readable_summary: string
  recommendation: string
  risk_factors: string[]
  amazon_url?: string
  seller_central_url?: string
}

export interface BatchAPIResponse {
  batch_id: string
  total_items: number
  processed: number
  successful: number
  failed: number
  results: BatchResult[]
  trace_id: string
}

export interface BatchResult {
  identifier: string
  asin: string | null
  status: 'success' | 'error' | 'not_found'
  analysis: AnalysisAPIResult | null
  error: string | null
}

// Progress Tracking Types
export interface AnalysisProgress {
  status: 'idle' | 'running' | 'completed' | 'error' | 'partial'
  processed: number
  total: number
  percentage: number
  successful: number
  failed: number
  startTime?: Date
  endTime?: Date
}

export interface AnalysisResults {
  successful: AnalysisAPIResult[]
  failed: BatchResult[]
  batchInfo: {
    batch_id: string
    trace_id: string
    total_items: number
    processing_time?: number
  }
}
