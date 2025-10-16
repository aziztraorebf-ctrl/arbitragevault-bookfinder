// Types pour l'intégration Keepa

// === Request Types ===
export interface IngestRequest {
  identifiers: string[];
  config_profile?: 'balanced' | 'aggressive' | 'conservative';
  force_refresh?: boolean;
}

// === Response Types ===
export interface ROIMetrics {
  sell_price: string;
  buy_cost: string;
  weight_lbs: string;
  net_profit: string;
  roi_percentage: string;
  margin_percentage: string;
  is_profitable: boolean;
  meets_target_roi: boolean;
  profit_tier: 'excellent' | 'good' | 'fair' | 'loss';
  fees: {
    referral_fee: string;
    closing_fee: string;
    fba_fee: string;
    inbound_shipping: string;
    prep_fee: string;
    total_fees: string;
  };
}

export interface VelocityMetrics {
  velocity_score: number;
  rank_percentile_30d: number;
  rank_drops_30d: number;
  velocity_tier: 'high' | 'medium' | 'low';
}

export interface ScoreBreakdown {
  score: number;
  raw: number;
  level: string;
  notes: string;
}

export interface PricingDetail {
  current_price: number | null;
  target_buy_price: number;
  roi_percentage: number | null;
  net_profit: number | null;
  available: boolean;
  recommended: boolean;
}

export interface AnalysisResult {
  asin: string;
  title: string | null;
  current_price: number | null;
  current_bsr: number | null;

  // NEW: USED vs NEW pricing breakdown
  pricing?: {
    used?: PricingDetail;
    new?: PricingDetail;
  };

  roi: ROIMetrics | { error: string };
  velocity: VelocityMetrics | { error: string };
  velocity_score: number;
  price_stability_score: number;
  confidence_score: number;
  overall_rating: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'PASS' | 'ERROR';
  score_breakdown: {
    velocity: ScoreBreakdown;
    stability: ScoreBreakdown;
    confidence: ScoreBreakdown;
  };
  readable_summary: string;
  recommendation: string;
  risk_factors: string[];
}

export interface BatchResultItem {
  identifier: string;
  asin: string | null;
  status: 'success' | 'error' | 'not_found';
  analysis: AnalysisResult | null;
  error: string | null;
}

export interface IngestResponse {
  batch_id: string;
  total_items: number;
  processed: number;
  successful: number;
  failed: number;
  results: BatchResultItem[];
  trace_id: string;
}