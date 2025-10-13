/**
 * VelocityTooltip - Explains Velocity Score breakdown
 *
 * Phase 2.5A Hybrid Solution
 * Shows detailed components: BSR, Sales Activity, Buy Box, Price Stability
 */

import type { VelocityBreakdown } from '../../types/views';

interface VelocityTooltipProps {
  score: number;
  breakdown?: VelocityBreakdown;
}

export function VelocityTooltip({ score, breakdown }: VelocityTooltipProps) {
  const tier = breakdown?.velocity_tier || getTierFromScore(score);
  const tierInfo = getTierInfo(tier);

  return (
    <div className="space-y-2">
      {/* Title */}
      <div className="font-semibold text-sm border-b border-gray-700 pb-2">
        Velocity Score: {score.toFixed(0)} ({tierInfo.label} {tierInfo.emoji})
      </div>

      {/* Subtitle */}
      <div className="text-[11px] text-gray-300 leading-tight">
        Sales speed indicator. Higher = faster sales, better cash flow.
      </div>

      {/* Score Breakdown */}
      {breakdown && (
        <div className="space-y-1 text-xs">
          <div className="font-medium text-gray-200 border-b border-gray-700 pb-1 mb-2">
            SCORE BREAKDOWN (0-100):
          </div>

          {/* BSR Trend */}
          {breakdown.bsr_score !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between">
                <span className="text-gray-300">📈 BSR Rank Trend:</span>
                <span className="font-mono">{breakdown.bsr_score.toFixed(1)} / 30 pts</span>
              </div>
              {breakdown.bsr_percentile !== undefined && (
                <div className="text-[10px] text-gray-400 ml-4">
                  • Average BSR: {breakdown.bsr_avg?.toLocaleString()} (Top {breakdown.bsr_percentile}%)
                </div>
              )}
            </div>
          )}

          {/* Sales Activity */}
          {breakdown.sales_activity_score !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between">
                <span className="text-gray-300">🔄 Sales Activity:</span>
                <span className="font-mono">{breakdown.sales_activity_score.toFixed(1)} / 25 pts</span>
              </div>
              {breakdown.estimated_sales_30d !== undefined && (
                <div className="text-[10px] text-gray-400 ml-4">
                  • Est. ~{breakdown.estimated_sales_30d} sales in last 30 days
                </div>
              )}
              {breakdown.bsr_drops_30d !== undefined && (
                <div className="text-[10px] text-gray-400 ml-4">
                  • {breakdown.bsr_drops_30d} BSR drops detected
                </div>
              )}
            </div>
          )}

          {/* Buy Box Uptime (only if data available) */}
          {breakdown.buybox_uptime_pct !== null && breakdown.buybox_uptime_pct !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between">
                <span className="text-gray-300">🎯 Buy Box Availability:</span>
                <span className="font-mono">{breakdown.buybox_score?.toFixed(1) || 0} / 25 pts</span>
              </div>
              <div className="text-[10px] text-gray-400 ml-4">
                • Buy Box active {breakdown.buybox_uptime_pct.toFixed(0)}% of time
              </div>
            </div>
          )}

          {/* Price Stability */}
          {breakdown.stability_score !== undefined && (
            <div className="space-y-0.5">
              <div className="flex justify-between">
                <span className="text-gray-300">💹 Price Stability:</span>
                <span className="font-mono">{breakdown.stability_score.toFixed(1)} / 20 pts</span>
              </div>
              {breakdown.price_volatility_pct !== undefined && (
                <div className="text-[10px] text-gray-400 ml-4">
                  • Price swings: ±{breakdown.price_volatility_pct.toFixed(1)}%
                </div>
              )}
              {breakdown.price_range_30d && (
                <div className="text-[10px] text-gray-400 ml-4">
                  • Range: ${breakdown.price_range_30d.min}-${breakdown.price_range_30d.max} (30d)
                </div>
              )}
            </div>
          )}

          {/* Total */}
          <div className="flex justify-between border-t border-gray-700 pt-1 mt-2 font-semibold">
            <span className="text-gray-200">TOTAL:</span>
            <span className="font-mono text-blue-400">{score.toFixed(0)} / 100 pts</span>
          </div>
        </div>
      )}

      {/* Velocity Tier Explanation */}
      <div className="mt-3 pt-2 border-t border-gray-700 text-xs">
        <div className="font-medium text-gray-200 mb-1">VELOCITY TIER: {tierInfo.label}</div>
        <div className="space-y-1 text-[10px] text-gray-400 leading-relaxed">
          <div>• Fast (80+): Quick flip, &lt;30 days{tier === 'fast' ? ' ← YOU' : ''}</div>
          <div>• Medium (60-79): Steady sales, 30-60 days{tier === 'medium' ? ' ← YOU' : ''}</div>
          <div>• Slow (40-59): Longer hold, 60-90 days{tier === 'slow' ? ' ← YOU' : ''}</div>
          <div>• Very Slow (&lt;40): Risk stagnation, 90+ days{tier === 'very_slow' ? ' ← YOU' : ''}</div>
        </div>
      </div>

      {/* Tip */}
      <div className="mt-2 pt-2 border-t border-gray-700 text-[10px] text-blue-300 leading-tight">
        💡 TIP: Combine high velocity (70+) with low Amazon competition for best opportunities.
      </div>
    </div>
  );
}

// Helper to determine tier from score
function getTierFromScore(score: number): 'fast' | 'medium' | 'slow' | 'very_slow' {
  if (score >= 80) return 'fast';
  if (score >= 60) return 'medium';
  if (score >= 40) return 'slow';
  return 'very_slow';
}

// Helper to get tier display info
function getTierInfo(tier: string) {
  const info = {
    fast: { label: 'Fast', emoji: '🚀' },
    medium: { label: 'Medium', emoji: '📊' },
    slow: { label: 'Slow', emoji: '🐢' },
    very_slow: { label: 'Very Slow', emoji: '⚠️' }
  };
  return info[tier as keyof typeof info] || info.medium;
}
