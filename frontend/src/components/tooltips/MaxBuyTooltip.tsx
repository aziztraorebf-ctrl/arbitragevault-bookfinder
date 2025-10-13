/**
 * MaxBuyTooltip - Explains Max Buy Price recommendation
 *
 * Phase 2.5A Hybrid Solution
 * Shows calculation for recommended max purchase price to achieve 35% ROI
 */

interface MaxBuyTooltipProps {
  maxBuyPrice: number;
  marketSellPrice?: number;
  targetROI?: number;
}

export function MaxBuyTooltip({
  maxBuyPrice,
  marketSellPrice = 0,
  targetROI = 35
}: MaxBuyTooltipProps) {
  // Estimate fees (15% referral + ~$2 FBA for books)
  const estimatedFees = marketSellPrice * 0.15 + 2;
  const netProfit = marketSellPrice - estimatedFees - maxBuyPrice;

  return (
    <div className="space-y-2">
      {/* Title */}
      <div className="font-semibold text-sm border-b border-gray-700 pb-2">
        Maximum Buy Price ({targetROI}% ROI Target)
      </div>

      {/* Subtitle */}
      <div className="text-[11px] text-gray-300 leading-tight">
        Recommended max purchase price to achieve {targetROI}% profitability
      </div>

      {/* Calculation */}
      <div className="space-y-1 text-xs">
        <div className="font-medium text-gray-200 border-b border-gray-700 pb-1 mb-2">
          TO ACHIEVE {targetROI}% ROI:
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• Sell at:</span>
          <span className="font-mono">${marketSellPrice.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-green-400 font-semibold">
          <span>• Buy MAX:</span>
          <span className="font-mono">${maxBuyPrice.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• Amazon fees:</span>
          <span className="font-mono">${estimatedFees.toFixed(2)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1 mt-1">
          <span className="text-gray-300">• Net profit:</span>
          <span className="font-mono text-green-400 font-semibold">
            ${netProfit.toFixed(2)} ({targetROI}% ROI)
          </span>
        </div>
      </div>

      {/* Action tip */}
      <div className="mt-3 pt-2 border-t border-gray-700 text-xs">
        <div className="flex items-start gap-2">
          <span className="text-xl">🔍</span>
          <div className="text-[11px] text-blue-300 leading-tight">
            Find suppliers selling at <span className="font-semibold">${maxBuyPrice.toFixed(2)} or less</span> to achieve profitable arbitrage
          </div>
        </div>
      </div>

      {/* Formula */}
      <div className="mt-2 pt-2 border-t border-gray-700 text-xs">
        <div className="font-medium text-gray-200 mb-1">FORMULA:</div>
        <div className="font-mono text-[10px] text-gray-400 leading-relaxed">
          Max Buy = (Sell - Fees) / (1 + ROI/100)
        </div>
      </div>
    </div>
  );
}
