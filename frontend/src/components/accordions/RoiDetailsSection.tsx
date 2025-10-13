/**
 * Section détaillée ROI - Phase 2.5A Accordéon
 * Affiche les prix actuels du marché et le ROI calculé
 */

import type { AccordionSectionProps } from './types'

export function RoiDetailsSection({ product }: AccordionSectionProps) {
  // Defensive extraction avec fallbacks
  const marketSell = product.market_sell_price ?? 0
  const marketBuy = product.market_buy_price ?? 0
  const currentRoi = product.current_roi_pct ?? 0
  const maxBuy35 = product.max_buy_price_35pct ?? null

  // Calcul estimé des frais (15% + $2 closing fee approximatif)
  const estimatedFees = marketSell > 0 ? marketSell * 0.15 + 2 : 0

  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-sm text-gray-900 mb-3">📊 ROI Summary</h4>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-600">Vente Amazon:</span>{' '}
          <span className="font-medium text-green-700">${marketSell.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-600">Achat FBA:</span>{' '}
          <span className="font-medium text-blue-700">${marketBuy.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-600">Est. Fees:</span>{' '}
          <span className="font-medium text-gray-700">${estimatedFees.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-600">Net Profit:</span>{' '}
          <span className={`font-medium ${currentRoi >= 0 ? 'text-green-700' : 'text-red-700'}`}>
            ${(marketSell - marketBuy - estimatedFees).toFixed(2)}
          </span>
        </div>
      </div>

      <div className="pt-2 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">ROI:</span>
          <span className={`text-sm font-bold ${currentRoi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {currentRoi.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-gray-600">Max Buy (35% target):</span>
          <span className="text-sm font-medium text-purple-600">
            {maxBuy35 !== null && maxBuy35 > 0 ? `$${maxBuy35.toFixed(2)}` : 'N/A'}
          </span>
        </div>
      </div>

      {currentRoi < 0 && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          ❌ Non rentable aux prix actuels du marché
        </div>
      )}
    </div>
  )
}
