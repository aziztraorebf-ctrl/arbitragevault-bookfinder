/**
 * UnifiedProductRow - Single row component for unified product display
 * Supports both ProductScore and NicheProduct sources
 * Feature flags control which columns are displayed
 */

import { Fragment } from 'react'
import type { DisplayableProduct, Recommendation } from '../../types/unified'

export interface UnifiedRowFeatures {
  showScore?: boolean
  showRank?: boolean
  showRecommendation?: boolean
  showCategory?: boolean
  showAmazonBadges?: boolean
  showVerifyButton?: boolean
  showAccordion?: boolean
}

interface UnifiedProductRowProps {
  product: DisplayableProduct
  isExpanded: boolean
  onToggle: () => void
  features: UnifiedRowFeatures
  onVerify?: (product: DisplayableProduct) => void
  verificationLoading?: boolean
  AccordionComponent?: React.ComponentType<{ product: DisplayableProduct; isExpanded: boolean }>
}

// Recommendation badge colors and labels
const RECOMMENDATION_BADGES: Record<string, { label: string; color: string }> = {
  STRONG_BUY: { label: 'Achat Fort', color: 'bg-green-600 text-white' },
  BUY: { label: 'Acheter', color: 'bg-green-500 text-white' },
  CONSIDER: { label: 'Considerer', color: 'bg-yellow-500 text-white' },
  SKIP: { label: 'Passer', color: 'bg-red-500 text-white' },
}

export function UnifiedProductRow({
  product,
  isExpanded,
  onToggle,
  features,
  onVerify,
  verificationLoading,
  AccordionComponent,
}: UnifiedProductRowProps) {
  const {
    showScore = false,
    showRank = false,
    showRecommendation = false,
    showCategory = false,
    showAmazonBadges = false,
    showVerifyButton = false,
    showAccordion = false,
  } = features

  const recommendationBadge = product.recommendation
    ? RECOMMENDATION_BADGES[product.recommendation] || { label: product.recommendation, color: 'bg-gray-500 text-white' }
    : null

  // ROI color coding
  const roiColorClass =
    product.roi_percent >= 30
      ? 'text-green-600'
      : product.roi_percent >= 15
      ? 'text-yellow-600'
      : 'text-red-600'

  return (
    <Fragment>
      <tr className="hover:bg-gray-50 transition-colors">
        {/* Chevron for expansion */}
        {showAccordion && (
          <td className="px-4 py-3 text-center">
            <button
              onClick={onToggle}
              className="text-gray-500 hover:text-gray-700 transition-transform"
              aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
            >
              <svg
                className={`w-5 h-5 transition-transform duration-300 ${
                  isExpanded ? 'rotate-90' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </td>
        )}

        {/* Rank (optional) */}
        {showRank && (
          <td className="px-4 py-3 text-center text-sm font-medium text-gray-900">
            {product.rank ?? '-'}
          </td>
        )}

        {/* ASIN with Amazon link */}
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
          <div>
            <p className="truncate">{product.title || 'N/A'}</p>
            {showCategory && product.category_name && (
              <p className="text-xs text-gray-400 mt-1">{product.category_name}</p>
            )}
          </div>
        </td>

        {/* Score (optional - ProductScore only) */}
        {showScore && (
          <td className="px-4 py-3 text-center text-sm font-bold text-purple-600">
            {product.score?.toFixed(1) ?? '-'}
          </td>
        )}

        {/* ROI */}
        <td className={`px-4 py-3 text-center text-sm font-semibold ${roiColorClass}`}>
          {product.roi_percent.toFixed(1)}%
        </td>

        {/* Velocity */}
        <td className="px-4 py-3 text-center">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-sm font-medium text-gray-900">
              {product.velocity_score.toFixed(0)}
            </span>
            <div className="w-16 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min(product.velocity_score, 100)}%` }}
              />
            </div>
          </div>
        </td>

        {/* BSR */}
        <td className="px-4 py-3 text-center text-sm font-medium text-gray-700">
          {product.bsr ? `#${product.bsr.toLocaleString()}` : 'N/A'}
        </td>

        {/* Recommendation badge (optional - NicheProduct) */}
        {showRecommendation && (
          <td className="px-4 py-3 text-center">
            {recommendationBadge ? (
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${recommendationBadge.color}`}
              >
                {recommendationBadge.label}
              </span>
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </td>
        )}

        {/* Amazon badges (optional) */}
        {showAmazonBadges && (
          <td className="px-4 py-3 text-center">
            <div className="flex gap-1 justify-center">
              {product.amazon_on_listing && (
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">
                  AMZ
                </span>
              )}
              {product.amazon_buybox && (
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                  BB
                </span>
              )}
            </div>
          </td>
        )}

        {/* Actions: Verify button (optional) */}
        {showVerifyButton && (
          <td className="px-4 py-3 text-center">
            <div className="flex gap-2 justify-center">
              <a
                href={`https://www.amazon.com/dp/${product.asin}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-xs font-medium rounded-md border bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100"
              >
                Amazon
              </a>
              {onVerify && (
                <button
                  onClick={() => onVerify(product)}
                  disabled={verificationLoading}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                    verificationLoading
                      ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                      : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                  }`}
                >
                  {verificationLoading ? 'Verification...' : 'Verifier'}
                </button>
              )}
            </div>
          </td>
        )}
      </tr>

      {/* Accordion row */}
      {showAccordion && AccordionComponent && (
        <tr>
          <td colSpan={20} className="p-0">
            <AccordionComponent product={product} isExpanded={isExpanded} />
          </td>
        </tr>
      )}
    </Fragment>
  )
}
