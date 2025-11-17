/**
 * Phase 8.0 Analytics Type Definitions
 * Types matching backend Pydantic schemas
 */

export interface VelocityAnalytics {
  velocity_score: number
  trend_7d: number | null
  trend_30d: number | null
  trend_90d: number | null
  bsr_current: number | null
  risk_level: string
}

export interface PriceStability {
  stability_score: number
  coefficient_variation: number | null
  price_volatility: string
  avg_price: number | null
  std_deviation: number | null
}

export interface ROIAnalysis {
  net_profit: number
  roi_percentage: number
  gross_profit: number
  referral_fee: number
  fba_fee: number
  prep_fee: number
  storage_cost: number
  return_losses: number
  total_fees: number
  breakeven_required_days: number | null
}

export interface CompetitionAnalysis {
  competition_score: number
  competition_level: string
  seller_count: number | null
  fba_ratio: number | null
  amazon_risk: string
}

export interface RiskComponent {
  score: number
  weighted: number
  weight: number
}

export interface RiskScore {
  asin: string
  risk_score: number
  risk_level: string
  components: Record<string, RiskComponent>
  recommendations: string
}

export interface Recommendation {
  asin: string
  title: string
  recommendation: 'STRONG_BUY' | 'BUY' | 'CONSIDER' | 'WATCH' | 'SKIP' | 'AVOID'
  confidence_percent: number
  criteria_passed: number
  criteria_total: number
  reason: string
  roi_net: number
  velocity_score: number
  risk_score: number
  profit_per_unit: number
  estimated_time_to_sell_days: number | null
  suggested_action: string
  next_steps: string[]
}

export interface ProductDecision {
  asin: string
  title: string
  velocity: VelocityAnalytics
  price_stability: PriceStability
  roi: ROIAnalysis
  competition: CompetitionAnalysis
  risk: RiskScore
  recommendation: Recommendation
}

export interface ASINHistoryRecord {
  id: string
  asin: string
  tracked_at: string
  price: number | null
  bsr: number | null
  seller_count: number | null
  amazon_on_listing: boolean | null
  metadata: Record<string, unknown> | null
}

export interface ASINTrends {
  asin: string
  data_points: number
  date_range: {
    start: string | null
    end: string | null
  }
  bsr?: {
    current: number
    earliest: number
    lowest_rank: number
    highest_rank: number
    trend: 'improving' | 'declining'
    change: number
  }
  price?: {
    current: number
    average: number
    min: number
    max: number
    volatility: number
  }
  sellers?: {
    current: number
    average: number
    min: number
    max: number
    trend: 'decreasing' | 'increasing'
  }
}
