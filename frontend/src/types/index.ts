// Common types for ArbitrageVault frontend

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

export interface AnalysisResult {
  products: Product[]
  total_analyzed: number
  successful_analyses: number
  average_roi: number
  processing_time: number
}

export interface NicheDiscoveryResult {
  niche_id: string
  category: string
  score: number
  products_count: number
  average_roi: number
  competition_level: string
  created_at: string
}

export interface BookmarkedNiche {
  id: string
  name: string
  category: string
  filters: Record<string, any>
  score: number
  created_at: string
  last_analyzed: string
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

// Manual Analysis Types
export interface UploadedCSVData {
  headers: string[]
  rows: Record<string, string>[]
  fileName: string
  totalRows: number
  asinColumnIndex?: number
}

export interface ValidationResult {
  isValid: boolean
  validASINs: string[]
  invalidASINs: string[]
  errors: string[]
}

export interface AnalysisInput {
  asins: string[]
  source: 'csv' | 'manual'
  csvData?: UploadedCSVData
  strategy?: string
}

export interface AnalysisStep {
  step: 'upload' | 'criteria' | 'progress' | 'results' | 'export'
  title: string
  completed: boolean
}

// Analysis Criteria Types
export interface AnalysisCriteria {
  roiMin: number        // Percentage (20 = 20%)
  bsrMax: number        // Number (250000 = 250k)
  minSalesPerMonth: number  // Number (10 = 10+ sales/month)
}

export interface AnalysisStrategy {
  id: 'velocity' | 'balanced' | 'profit-hunter' | 'custom'
  name: string
  description: string
  criteria: AnalysisCriteria
  color: string
  icon: string
}

export interface ConfiguredAnalysis {
  asins: string[]
  source: 'csv' | 'manual'
  csvData?: UploadedCSVData
  strategy: AnalysisStrategy
  customCriteria?: AnalysisCriteria
}

// API Response Types (from backend /api/v1/keepa/ingest)
export interface AnalysisAPIResult {
  asin: string
  title: string
  roi: {
    roi_percentage: number
    is_profitable: boolean
    net_profit: string
    profit_tier: string
  }
  velocity: {
    velocity_score: number
    velocity_tier: string
  }
  overall_rating: string
  readable_summary: string
  recommendation: string
  risk_factors: string[]
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