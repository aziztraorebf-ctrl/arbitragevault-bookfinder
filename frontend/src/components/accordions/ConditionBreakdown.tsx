/**
 * ConditionBreakdown - Phase 5 Feature
 * Displays pricing breakdown by condition (new, very_good, good, acceptable)
 * with ROI, seller count, and FBA availability for each condition
 *
 * Used across all views: Analyse Manuelle, Mes Niches, AutoSourcing
 */

import { useState } from 'react'

// Accept both AnalysisResult and ProductScore which both have pricing field
type AnalysisLike = {
  pricing?: {
    by_condition?: Record<string, {
      market_price: number
      roi_pct: number
      roi_value: number
      seller_count: number
      fba_count: number
      is_recommended: boolean
      net_revenue: number
      amazon_fees: number
    }>
    recommended_condition?: string
    source_price?: number
  }
}

interface ConditionBreakdownProps {
  analysis: AnalysisLike
  sourcePrice?: number
}

const CONDITION_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  new: {
    label: 'New',
    icon: '✨',
    color: 'blue'
  },
  very_good: {
    label: 'Very Good',
    icon: '👍',
    color: 'green'
  },
  good: {
    label: 'Good',
    icon: '👌',
    color: 'yellow'
  },
  acceptable: {
    label: 'Acceptable',
    icon: '⚠️',
    color: 'orange'
  }
}

function getROIColor(roi: number): string {
  if (roi >= 30) return 'text-green-600 bg-green-50'
  if (roi >= 15) return 'text-yellow-600 bg-yellow-50'
  return 'text-red-600 bg-red-50'
}

function formatPrice(price: number | null): string {
  return price !== null ? `$${price.toFixed(2)}` : 'N/A'
}

function formatROI(roi: number | null): string {
  if (roi === null) return 'N/A'
  return roi >= 0 ? `+${(roi * 100).toFixed(1)}%` : `${(roi * 100).toFixed(1)}%`
}

export function ConditionBreakdown({
  analysis,
  sourcePrice = 8.0
}: ConditionBreakdownProps) {
  const [expandedCondition, setExpandedCondition] = useState<string | null>(null)

  const pricingByCondition = analysis.pricing?.by_condition
  const recommendedCondition = analysis.pricing?.recommended_condition

  if (!pricingByCondition || Object.keys(pricingByCondition).length === 0) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-600">
        ℹ️ Pas de données de pricing par condition disponibles
      </div>
    )
  }

  // Sort conditions by ROI (best first)
  const sortedConditions = Object.entries(pricingByCondition).sort(
    (a, b) => (b[1]?.roi_pct || 0) - (a[1]?.roi_pct || 0)
  )

  return (
    <div className="space-y-2">
      {/* Header with source price info */}
      <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm">
        <span className="text-blue-700 font-medium">
          📊 Pricing by Condition (source: ${sourcePrice.toFixed(2)})
        </span>
      </div>

      {/* Condition cards */}
      <div className="space-y-2">
        {sortedConditions.map(([conditionKey, conditionData]) => {
          const config = CONDITION_LABELS[conditionKey] || { label: conditionKey, icon: '📦', color: 'gray' }
          const isRecommended = conditionKey === recommendedCondition
          const isExpanded = expandedCondition === conditionKey

          return (
            <div
              key={conditionKey}
              className={`border rounded-lg overflow-hidden transition-all ${
                isRecommended
                  ? 'border-2 border-green-500 bg-green-50'
                  : 'border border-gray-200 bg-white hover:bg-gray-50'
              }`}
            >
              {/* Condition header - clickable to expand */}
              <button
                onClick={() =>
                  setExpandedCondition(
                    isExpanded ? null : conditionKey
                  )
                }
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-75 transition-colors"
              >
                {/* Left: Label and icon */}
                <div className="flex items-center gap-2">
                  <span className="text-xl">{config.icon}</span>
                  <div className="text-left">
                    <div className="font-semibold text-sm text-gray-900">
                      {config.label}
                      {isRecommended && (
                        <span className="ml-2 inline-block px-2 py-0.5 bg-green-600 text-white text-xs rounded-full font-medium">
                          ✨ Best
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600">
                      {conditionData?.seller_count || 0} seller{(conditionData?.seller_count || 0) !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>

                {/* Right: Price and ROI */}
                <div className="text-right">
                  <div className="font-bold text-lg text-blue-700">
                    {formatPrice(conditionData?.market_price)}
                  </div>
                  <div className={`font-bold text-sm ${getROIColor(conditionData?.roi_pct || 0)}`}>
                    {formatROI(conditionData?.roi_pct)}
                  </div>
                </div>

                {/* Expand icon */}
                <div className="ml-2 text-gray-400">
                  {isExpanded ? '▼' : '▶'}
                </div>
              </button>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-4 py-3 border-t border-gray-200 bg-white space-y-2">
                  {/* Price info grid */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {/* Market price */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">Market Price</span>
                      <span className="font-semibold text-gray-900">
                        {formatPrice(conditionData?.market_price)}
                      </span>
                    </div>

                    {/* ROI percentage */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">ROI %</span>
                      <span className={`font-semibold ${getROIColor(conditionData?.roi_pct || 0)}`}>
                        {formatROI(conditionData?.roi_pct)}
                      </span>
                    </div>

                    {/* ROI value in dollars */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">ROI Value</span>
                      <span
                        className={`font-semibold ${
                          (conditionData?.roi_value || 0) >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {formatPrice(conditionData?.roi_value)}
                      </span>
                    </div>

                    {/* Net Revenue */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">Net Revenue</span>
                      <span className="font-semibold text-gray-900">
                        {formatPrice(conditionData?.net_revenue)}
                      </span>
                    </div>

                    {/* Amazon Fees */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">Amazon Fees (15%)</span>
                      <span className="font-semibold text-gray-900">
                        {formatPrice(conditionData?.amazon_fees)}
                      </span>
                    </div>

                    {/* Seller count with FBA */}
                    <div>
                      <span className="text-gray-600 text-xs block mb-1">FBA Availability</span>
                      <span className="font-semibold text-gray-900">
                        {conditionData?.fba_count || 0} of{' '}
                        {conditionData?.seller_count || 0} FBA
                      </span>
                    </div>
                  </div>

                  {/* Cost breakdown explanation */}
                  <div className="mt-3 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 space-y-1">
                    <div className="font-medium text-gray-900">Cost Breakdown:</div>
                    <div>
                      • Source Price: {formatPrice(sourcePrice)}
                    </div>
                    <div>
                      • Market Price: {formatPrice(conditionData?.market_price)}
                    </div>
                    <div>
                      • Amazon Fees (15%): {formatPrice(conditionData?.amazon_fees)}
                    </div>
                    <div>
                      • Shipping: $3.00
                    </div>
                    <div className="font-medium text-gray-900">
                      = Net Profit: {formatPrice(conditionData?.roi_value)}
                    </div>
                  </div>

                  {/* Recommendation or warning */}
                  {isRecommended ? (
                    <div className="p-2 bg-green-100 border border-green-300 rounded text-xs text-green-900 font-medium">
                      ✅ Best ROI option - Recommended
                    </div>
                  ) : (
                    (conditionData?.roi_pct || 0) < 0 && (
                      <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                        ⚠️ Negative ROI - Not recommended
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary footer */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
        <div className="font-medium text-blue-900">💡 Pro Tips:</div>
        <ul className="mt-2 text-blue-800 text-xs space-y-1">
          <li>• Green ROI (≥30%) = Excellent for FBA</li>
          <li>• Yellow ROI (15-30%) = Good potential</li>
          <li>• Red ROI (&lt;15%) = Wait for better prices</li>
          <li>• Compare seller count - More FBA options = lower prices</li>
        </ul>
      </div>
    </div>
  )
}
