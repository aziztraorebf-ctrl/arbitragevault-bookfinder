import ErrorBoundary from '../Common/ErrorBoundary'
import { useProductDecision } from '../../hooks/useProductDecision'
import { Loader2, AlertTriangle, TrendingUp, DollarSign, Shield } from 'lucide-react'
import type { ProductDecision } from '../../types/analytics'

interface ProductDecisionCardProps {
  asin: string
  title?: string
  onActionTaken?: (action: 'buy' | 'watch' | 'skip') => void
}

/**
 * Phase 8.0 Product Decision Card Component
 *
 * Displays comprehensive analytics for a single product:
 * - Velocity intelligence and BSR trends
 * - Price stability analysis
 * - ROI net calculation with all fees
 * - Competition analysis
 * - Risk score (5 components)
 * - Final recommendation (5-tier)
 *
 * Includes error boundaries and loading states
 */
export function ProductDecisionCard({
  asin,
  title,
  onActionTaken
}: ProductDecisionCardProps) {
  const {
    data: decision,
    isLoading,
    isError,
    error
  } = useProductDecision(asin)

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (isError || !decision) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-red-200 p-6">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <div>
            <p className="text-red-700 font-medium">Failed to load analytics</p>
            <p className="text-sm text-red-600">
              {error instanceof Error ? error.message : 'Unknown error occurred'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
        {/* Header with Product Info */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-xl font-bold mb-1">
                {decision.title || title || 'Product Analysis'}
              </h3>
              <p className="text-blue-100 text-sm">ASIN: {decision.asin}</p>
            </div>
            <RecommendationBadge recommendation={decision.recommendation.recommendation} />
          </div>
        </div>

        {/* Recommendation Banner */}
        <RecommendationBanner recommendation={decision.recommendation} />

        {/* Analytics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
          {/* Score Panel */}
          <ScorePanel
            roi={decision.roi}
            velocity={decision.velocity}
            priceStability={decision.price_stability}
          />

          {/* Risk Panel */}
          <RiskPanel risk={decision.risk} />

          {/* Financial Panel */}
          <FinancialPanel roi={decision.roi} />

          {/* Competition Panel */}
          <CompetitionPanel competition={decision.competition} />
        </div>

        {/* Action Buttons */}
        {onActionTaken && (
          <div className="border-t border-gray-200 p-6">
            <ActionButtons
              recommendation={decision.recommendation.recommendation}
              onActionTaken={onActionTaken}
            />
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}

/**
 * Recommendation Badge - Color-coded tier indicator
 */
function RecommendationBadge({ recommendation }: { recommendation: string }) {
  const config = {
    STRONG_BUY: { bg: 'bg-green-500', text: 'Strong Buy' },
    BUY: { bg: 'bg-green-400', text: 'Buy' },
    CONSIDER: { bg: 'bg-yellow-400', text: 'Consider' },
    WATCH: { bg: 'bg-orange-400', text: 'Watch' },
    SKIP: { bg: 'bg-red-400', text: 'Skip' },
    AVOID: { bg: 'bg-red-600', text: 'Avoid' },
  }[recommendation] || { bg: 'bg-gray-400', text: recommendation }

  return (
    <span className={`${config.bg} text-white px-4 py-2 rounded-full text-sm font-semibold`}>
      {config.text}
    </span>
  )
}

/**
 * Recommendation Banner - Full recommendation details
 */
function RecommendationBanner({ recommendation }: { recommendation: ProductDecision['recommendation'] }) {
  const isPositive = ['STRONG_BUY', 'BUY'].includes(recommendation.recommendation)
  const isNegative = ['SKIP', 'AVOID'].includes(recommendation.recommendation)

  const bgColor = isPositive
    ? 'bg-green-50 border-green-200'
    : isNegative
    ? 'bg-red-50 border-red-200'
    : 'bg-yellow-50 border-yellow-200'

  const textColor = isPositive
    ? 'text-green-800'
    : isNegative
    ? 'text-red-800'
    : 'text-yellow-800'

  return (
    <div className={`border-b ${bgColor} p-4`}>
      <div className="flex items-start space-x-3">
        <div className={`mt-1 ${textColor}`}>
          {isPositive ? <TrendingUp className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
        </div>
        <div className="flex-1">
          <p className={`font-semibold ${textColor} mb-1`}>
            {recommendation.reason}
          </p>
          <p className="text-sm text-gray-700">
            Confidence: {recommendation.confidence_percent.toFixed(1)}%
            ({recommendation.criteria_passed}/{recommendation.criteria_total} criteria passed)
          </p>
          <p className="text-sm text-gray-600 mt-2">
            <strong>Suggested Action:</strong> {recommendation.suggested_action}
          </p>
        </div>
      </div>
    </div>
  )
}

/**
 * Score Panel - Overall scores display
 */
function ScorePanel({ roi, velocity, priceStability }: {
  roi: ProductDecision['roi']
  velocity: ProductDecision['velocity']
  priceStability: ProductDecision['price_stability']
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
        <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
        Performance Scores
      </h4>

      <div className="space-y-3">
        <ScoreBar label="ROI" value={roi.roi_percentage} max={100} unit="%" />
        <ScoreBar label="Velocity" value={velocity.velocity_score} max={100} />
        <ScoreBar label="Price Stability" value={priceStability.stability_score} max={100} />
      </div>

      <div className="mt-4 pt-4 border-t border-gray-300">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Net Profit:</span>
          <span className="font-semibold text-green-700">${roi.net_profit.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm mt-2">
          <span className="text-gray-600">Time to Sell:</span>
          <span className="font-semibold">{roi.breakeven_required_days || 'N/A'} days</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Risk Panel - Risk score breakdown
 */
function RiskPanel({ risk }: { risk: ProductDecision['risk'] }) {
  const riskColor =
    risk.risk_level === 'CRITICAL' ? 'text-red-700' :
    risk.risk_level === 'HIGH' ? 'text-orange-600' :
    risk.risk_level === 'MEDIUM' ? 'text-yellow-600' :
    'text-green-600'

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
        <Shield className="w-5 h-5 mr-2 text-red-600" />
        Risk Assessment
      </h4>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Overall Risk Score</span>
          <span className={`font-bold text-lg ${riskColor}`}>
            {risk.risk_score.toFixed(1)}
          </span>
        </div>
        <div className={`text-xs font-semibold ${riskColor}`}>
          {risk.risk_level} RISK
        </div>
      </div>

      <div className="space-y-2">
        {Object.entries(risk.components).map(([key, component]) => (
          <div key={key} className="text-sm">
            <div className="flex justify-between mb-1">
              <span className="text-gray-600 capitalize">{key.replace('_', ' ')}</span>
              <span className="font-medium">{component.weighted.toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${component.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-4 text-xs text-gray-600 italic">
        {risk.recommendations}
      </p>
    </div>
  )
}

/**
 * Financial Panel - Detailed fee breakdown
 */
function FinancialPanel({ roi }: { roi: ProductDecision['roi'] }) {
  const fees = [
    { label: 'Referral Fee', value: roi.referral_fee },
    { label: 'FBA Fee', value: roi.fba_fee },
    { label: 'Storage Cost', value: roi.storage_cost },
    { label: 'Return Losses', value: roi.return_losses },
    { label: 'Prep Fee', value: roi.prep_fee },
  ]

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
        <DollarSign className="w-5 h-5 mr-2 text-green-600" />
        Financial Breakdown
      </h4>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm font-medium">
          <span className="text-gray-700">Gross Profit:</span>
          <span className="text-green-700">${roi.gross_profit.toFixed(2)}</span>
        </div>
        {fees.map(fee => (
          <div key={fee.label} className="flex justify-between text-xs text-gray-600">
            <span>{fee.label}:</span>
            <span>-${fee.value.toFixed(2)}</span>
          </div>
        ))}
        <div className="flex justify-between text-xs text-gray-600 pt-2 border-t">
          <span>Total Fees:</span>
          <span className="font-medium">-${roi.total_fees.toFixed(2)}</span>
        </div>
      </div>

      <div className="pt-3 border-t border-gray-300">
        <div className="flex justify-between items-center">
          <span className="font-bold text-gray-900">Net Profit:</span>
          <span className="font-bold text-lg text-green-700">
            ${roi.net_profit.toFixed(2)}
          </span>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          ROI: {roi.roi_percentage.toFixed(1)}%
        </div>
      </div>
    </div>
  )
}

/**
 * Competition Panel - Seller metrics
 */
function CompetitionPanel({ competition }: { competition: ProductDecision['competition'] }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="font-semibold text-gray-900 mb-4">Competition Analysis</h4>

      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Competition Level:</span>
          <span className="font-semibold text-gray-900">{competition.competition_level}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Total Sellers:</span>
          <span className="font-medium">{competition.seller_count ?? 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">FBA Ratio:</span>
          <span className="font-medium">
            {competition.fba_ratio ? `${(competition.fba_ratio * 100).toFixed(1)}%` : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Amazon Risk:</span>
          <span className={`font-semibold ${competition.amazon_risk === 'HIGH' ? 'text-red-600' : 'text-green-600'}`}>
            {competition.amazon_risk}
          </span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-300">
        <ScoreBar label="Competition Score" value={competition.competition_score} max={100} />
      </div>
    </div>
  )
}

/**
 * Score Bar - Reusable progress bar component
 */
function ScoreBar({ label, value, max = 100, unit = '' }: {
  label: string
  value: number
  max?: number
  unit?: string
}) {
  const percentage = Math.min((value / max) * 100, 100)
  const color = value >= 70 ? 'bg-green-500' : value >= 40 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-semibold">{value.toFixed(1)}{unit}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`${color} h-2.5 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

/**
 * Action Buttons - Buy/Watch/Skip actions
 */
function ActionButtons({
  recommendation,
  onActionTaken
}: {
  recommendation: string
  onActionTaken: (action: 'buy' | 'watch' | 'skip') => void
}) {
  const isPositive = ['STRONG_BUY', 'BUY'].includes(recommendation)
  const isNegative = ['SKIP', 'AVOID'].includes(recommendation)

  return (
    <div className="flex space-x-3">
      <button
        onClick={() => onActionTaken('buy')}
        disabled={isNegative}
        className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
          isPositive
            ? 'bg-green-600 hover:bg-green-700 text-white'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        Buy This Product
      </button>
      <button
        onClick={() => onActionTaken('watch')}
        className="flex-1 py-3 px-4 rounded-lg font-semibold bg-yellow-500 hover:bg-yellow-600 text-white transition-colors"
      >
        Add to Watch List
      </button>
      <button
        onClick={() => onActionTaken('skip')}
        className="flex-1 py-3 px-4 rounded-lg font-semibold bg-gray-200 hover:bg-gray-300 text-gray-700 transition-colors"
      >
        Skip
      </button>
    </div>
  )
}
