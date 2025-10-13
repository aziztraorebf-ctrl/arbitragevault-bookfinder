/**
 * ViewResultsRow - Phase 2.5A avec Accordéon
 * Ligne individuelle du tableau avec détails expand/collapse
 */

import type { ProductScore } from '../types/views'
import { AccordionContent } from './accordions/AccordionContent'

interface ViewResultsRowProps {
  product: ProductScore
  isExpanded: boolean
  onToggle: () => void
}

export function ViewResultsRow({ product, isExpanded, onToggle }: ViewResultsRowProps) {
  // Defensive extraction des valeurs
  const roiPct = product.raw_metrics?.roi_pct ?? 0
  const velocityScore = product.raw_metrics?.velocity_score ?? 0
  const marketSellPrice = product.market_sell_price ?? 0
  const marketBuyPrice = product.market_buy_price ?? 0
  const maxBuyPrice35pct = product.max_buy_price_35pct ?? 0
  const productScore = product.score ?? 0

  return (
    <>
      <tr className="hover:bg-gray-50 transition-colors">
        {/* Chevron Expansion */}
        <td className="px-4 py-3 text-center">
          <button
            onClick={onToggle}
            className="text-gray-500 hover:text-gray-700 transition-transform"
            aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
          >
            <span className={`inline-block transition-transform duration-300 ${isExpanded ? 'rotate-90' : ''}`}>
              ▶
            </span>
          </button>
        </td>

        {/* Rank */}
        <td className="px-4 py-3 text-center text-sm font-medium text-gray-900">
          {product.rank}
        </td>

        {/* ASIN */}
        <td className="px-4 py-3 text-sm font-mono text-blue-600">
          <a
            href={`https://www.amazon.com/dp/${product.asin}`}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {product.asin}
          </a>
        </td>

        {/* Title */}
        <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
          {product.title || 'N/A'}
        </td>

        {/* Score */}
        <td className="px-4 py-3 text-center text-sm font-bold text-purple-600">
          {productScore.toFixed(1)}
        </td>

        {/* ROI */}
        <td className={`px-4 py-3 text-center text-sm font-semibold ${roiPct >= 30 ? 'text-green-600' : roiPct >= 15 ? 'text-yellow-600' : 'text-red-600'}`}>
          {roiPct.toFixed(1)}%
        </td>

        {/* Velocity */}
        <td className="px-4 py-3 text-center">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-sm font-medium text-gray-900">
              {velocityScore.toFixed(0)}
            </span>
            <div className="w-16 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min(velocityScore, 100)}%` }}
              />
            </div>
          </div>
        </td>

        {/* Max Buy (35%) */}
        <td className="px-4 py-3 text-center text-sm font-medium text-purple-600">
          ${maxBuyPrice35pct.toFixed(2)}
        </td>

        {/* Market Sell */}
        <td className="px-4 py-3 text-center text-sm font-medium text-green-700">
          ${marketSellPrice.toFixed(2)}
        </td>

        {/* Market Buy */}
        <td className="px-4 py-3 text-center text-sm font-medium text-blue-700">
          ${marketBuyPrice.toFixed(2)}
        </td>

        {/* Amazon Badge */}
        <td className="px-4 py-3 text-center">
          {product.amazon_on_listing && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              🔵 Amazon Listed
            </span>
          )}
          {product.amazon_buybox && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 mt-1">
              📦 Buy Box
            </span>
          )}
        </td>
      </tr>

      {/* Accordéon Row */}
      <tr>
        <td colSpan={11} className="p-0">
          <AccordionContent product={product} isExpanded={isExpanded} />
        </td>
      </tr>
    </>
  )
}
