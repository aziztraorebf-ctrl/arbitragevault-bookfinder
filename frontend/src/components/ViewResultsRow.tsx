/**
 * ViewResultsRow - Phase 2.5A avec Accordéon
 * Ligne individuelle du tableau avec détails expand/collapse
 */

import type { ProductScore } from '../types/views'
import type { ProductScoreWithBSR } from '../utils/analysisAdapter'
import { AccordionContent } from './accordions/AccordionContent'

interface ViewResultsRowProps {
  product: ProductScore | ProductScoreWithBSR
  isExpanded: boolean
  onToggle: () => void
}

export function ViewResultsRow({ product, isExpanded, onToggle }: ViewResultsRowProps) {
  // Defensive extraction des valeurs
  const roiPct = product.raw_metrics?.roi_pct ?? 0
  const velocityScore = product.raw_metrics?.velocity_score ?? 0
  const productScore = product.score ?? 0

  // USED vs NEW pricing - NEW: Priority à pricing.used si disponible
  console.log('ViewResultsRow product:', product.asin, {
    pricing: product.pricing,
    market_buy_price: product.market_buy_price,
    current_roi_pct: product.current_roi_pct,
    raw_metrics: product.raw_metrics
  })
  const usedPrice = product.pricing?.used?.current_price ?? product.market_buy_price ?? 0
  const usedROI = product.pricing?.used?.roi_percentage
    ? parseFloat(product.pricing.used.roi_percentage)
    : (product.current_roi_pct ?? product.raw_metrics?.roi_pct ?? 0)
  console.log('ViewResultsRow calculated:', { usedPrice, usedROI })

  // BSR - Now directly from ProductScore type
  const currentBsr = product.current_bsr ?? (('current_bsr' in product) ? (product as ProductScoreWithBSR).current_bsr : null)

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

        {/* BSR */}
        <td className="px-4 py-3 text-center text-sm font-medium text-gray-700">
          {currentBsr ? `#${currentBsr.toLocaleString()}` : 'N/A'}
        </td>

        {/* Prix USED */}
        <td className="px-4 py-3 text-center text-sm">
          {usedPrice > 0 ? (
            <span className="font-semibold text-blue-700">
              ${usedPrice.toFixed(2)}
            </span>
          ) : (
            <span className="text-gray-400 text-xs">Non dispo</span>
          )}
        </td>

        {/* ROI USED */}
        <td className="px-4 py-3 text-center text-sm">
          {usedROI !== undefined && usedROI !== null ? (
            <span className={`font-semibold ${
              usedROI >= 30 ? 'text-green-600' :
              usedROI >= 15 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {usedROI >= 0 ? '+' : ''}{usedROI.toFixed(1)}%
            </span>
          ) : (
            <span className="text-gray-400">—</span>
          )}
        </td>
      </tr>

      {/* Accordéon Row */}
      <tr>
        <td colSpan={10} className="p-0">
          <AccordionContent product={product} isExpanded={isExpanded} />
        </td>
      </tr>
    </>
  )
}
