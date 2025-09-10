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