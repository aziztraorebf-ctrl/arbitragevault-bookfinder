/**
 * ROITooltip - Explains Current ROI calculation
 *
 * Phase 2.5A Hybrid Solution
 * Shows ROI breakdown when buying/selling at current market prices
 */

interface ROITooltipProps {
  currentROI: number;
  marketSellPrice?: number;
  marketBuyPrice?: number;
  fees?: number;
}

export function ROITooltip({
  currentROI,
  marketSellPrice = 0,
  marketBuyPrice = 0,
}: ROITooltipProps) {
  // Estimate fees (15% referral + ~$2 FBA for books)
  const estimatedFees = marketSellPrice * 0.15 + 2;
  const netResult = marketSellPrice - estimatedFees - marketBuyPrice;

  const isNegative = currentROI < 0;
  const isGood = currentROI >= 15;

  return (
    <div className="space-y-2">
      {/* Title */}
      <div className="font-semibold text-sm border-b border-gray-700 pb-2">
        Current ROI: {currentROI.toFixed(1)}% {isNegative ? '❌' : isGood ? '✅' : '⚠️'}
      </div>

      {/* Subtitle */}
      <div className="text-xs text-gray-300">
        Market Analysis (Current Prices)
      </div>

      {/* Calculation */}
      <div className="space-y-1 text-xs">
        <div className="font-medium text-gray-200 border-b border-gray-700 pb-1 mb-2">
          CALCULATION:
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• Market Sell:</span>
          <span className="font-mono">${marketSellPrice.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• Market Buy:</span>
          <span className="font-mono">${marketBuyPrice.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• Amazon Fees:</span>
          <span className="font-mono">${estimatedFees.toFixed(2)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1 mt-1">
          <span className="text-gray-300">• Net Result:</span>
          <span className={`font-mono font-semibold ${
            netResult >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            ${netResult.toFixed(2)} {netResult >= 0 ? '(PROFIT)' : '(LOSS)'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-300">• ROI:</span>
          <span className={`font-mono font-semibold ${
            isNegative ? 'text-red-400' : isGood ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {currentROI.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Formula */}
      <div className="mt-3 pt-2 border-t border-gray-700 text-xs">
        <div className="font-medium text-gray-200 mb-1">FORMULA:</div>
        <div className="font-mono text-[10px] text-gray-400 leading-relaxed">
          (Sell - Fees - Buy) / Buy × 100
        </div>
      </div>
    </div>
  );
}
