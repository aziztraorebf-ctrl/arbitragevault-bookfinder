/**
 * UnifiedProductTable - Main table component for unified product display
 * Supports filtering, sorting, export, and feature flags
 *
 * UX Constants:
 * - min-w-[800px]: Minimum table width for horizontal scroll on mobile
 *   Ensures all columns remain readable without cramping
 * - sticky top-0: Keeps headers visible when scrolling vertically
 * - px-3 md:px-4: Reduced padding on mobile (12px) vs desktop (16px)
 */

import { useState, useMemo } from 'react'
import type { DisplayableProduct } from '../../types/unified'
import type { VerificationResponse } from '../../services/verificationService'
import { UnifiedProductRow, type UnifiedRowFeatures } from './UnifiedProductRow'

export interface UnifiedTableFeatures extends UnifiedRowFeatures {
  showFilters?: boolean
  showExportCSV?: boolean
  showFooterSummary?: boolean
}

export interface UnifiedTableFilters {
  minRoi?: number
  minVelocity?: number
  minScore?: number
  amazonListed?: boolean
  amazonBuybox?: boolean
}

export interface UnifiedTableSort {
  by: 'score' | 'rank' | 'roi' | 'velocity' | 'bsr'
  order: 'asc' | 'desc'
}

// Verification state for a single product
export interface VerificationState {
  loading: boolean
  result?: VerificationResponse
  error?: string
}

interface UnifiedProductTableProps {
  products: DisplayableProduct[]
  title: string
  features: UnifiedTableFeatures
  defaultFilters?: UnifiedTableFilters
  defaultSort?: UnifiedTableSort
  onExportCSV?: (products: DisplayableProduct[]) => void
  onVerify?: (product: DisplayableProduct) => void
  // Verification state props from useVerification hook
  getVerificationState?: (asin: string) => VerificationState | undefined
  isVerificationExpanded?: (asin: string) => boolean
  toggleVerificationExpansion?: (asin: string) => void
  AccordionComponent?: React.ComponentType<{ product: DisplayableProduct; isExpanded: boolean }>
}

export function UnifiedProductTable({
  products,
  title,
  features,
  defaultFilters = {},
  defaultSort = { by: 'score', order: 'desc' },
  onExportCSV,
  onVerify,
  getVerificationState,
  isVerificationExpanded,
  toggleVerificationExpansion,
  AccordionComponent,
}: UnifiedProductTableProps) {
  const {
    showFilters = false,
    showExportCSV = false,
    showFooterSummary = false,
    showScore = false,
    showRank = false,
    showRecommendation = false,
    showCategory = false,
    showAmazonBadges = false,
    showVerifyButton = false,
    showAccordion = false,
  } = features

  // Filter state
  const [filters, setFilters] = useState<UnifiedTableFilters>(defaultFilters)
  const [sort, setSort] = useState<UnifiedTableSort>(defaultSort)
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  // Process products with filters and sorting
  const processedProducts = useMemo(() => {
    let result = [...products]

    // Apply filters
    if (filters.minRoi !== undefined && filters.minRoi > 0) {
      result = result.filter((p) => p.roi_percent >= filters.minRoi!)
    }
    if (filters.minVelocity !== undefined && filters.minVelocity > 0) {
      result = result.filter((p) => p.velocity_score >= filters.minVelocity!)
    }
    if (filters.minScore !== undefined && filters.minScore > 0) {
      result = result.filter((p) => (p.score ?? 0) >= filters.minScore!)
    }
    if (filters.amazonListed) {
      result = result.filter((p) => p.amazon_on_listing)
    }
    if (filters.amazonBuybox) {
      result = result.filter((p) => p.amazon_buybox)
    }

    // Apply sorting
    result.sort((a, b) => {
      let compareValue = 0
      switch (sort.by) {
        case 'score':
          compareValue = (a.score ?? 0) - (b.score ?? 0)
          break
        case 'rank':
          compareValue = (a.rank ?? 999) - (b.rank ?? 999)
          break
        case 'roi':
          compareValue = a.roi_percent - b.roi_percent
          break
        case 'velocity':
          compareValue = a.velocity_score - b.velocity_score
          break
        case 'bsr':
          compareValue = (a.bsr ?? 999999) - (b.bsr ?? 999999)
          break
      }
      return sort.order === 'desc' ? -compareValue : compareValue
    })

    return result
  }, [products, filters, sort])

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    if (processedProducts.length === 0) return null
    const avgRoi =
      processedProducts.reduce((sum, p) => sum + p.roi_percent, 0) / processedProducts.length
    const avgVelocity =
      processedProducts.reduce((sum, p) => sum + p.velocity_score, 0) / processedProducts.length
    return { avgRoi, avgVelocity }
  }, [processedProducts])

  // Empty state
  if (products.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 text-center">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Aucun produit a afficher</h3>
        <p className="text-sm text-gray-500">Lancez une analyse pour voir les resultats.</p>
      </div>
    )
  }

  // Row features to pass down
  const rowFeatures: UnifiedRowFeatures = {
    showScore,
    showRank,
    showRecommendation,
    showCategory,
    showAmazonBadges,
    showVerifyButton,
    showAccordion,
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <span>{title}</span>
            <span className="text-sm font-normal text-gray-600">
              ({processedProducts.length} produits)
            </span>
          </h3>
          {showExportCSV && onExportCSV && (
            <button
              onClick={() => onExportCSV(processedProducts)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              Export CSV
            </button>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="flex gap-4 flex-wrap items-end mt-4">
            {/* Min ROI */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">ROI min</label>
              <input
                type="number"
                value={filters.minRoi ?? ''}
                onChange={(e) =>
                  setFilters({ ...filters, minRoi: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                placeholder="0"
              />
            </div>

            {/* Min Velocity */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Velocity min</label>
              <input
                type="number"
                value={filters.minVelocity ?? ''}
                onChange={(e) =>
                  setFilters({ ...filters, minVelocity: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                placeholder="0"
              />
            </div>

            {/* Min Score (only if showScore) */}
            {showScore && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Score min</label>
                <input
                  type="number"
                  value={filters.minScore ?? ''}
                  onChange={(e) =>
                    setFilters({ ...filters, minScore: e.target.value ? Number(e.target.value) : undefined })
                  }
                  className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                  placeholder="0"
                />
              </div>
            )}

            {/* Sort By */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Trier par</label>
              <select
                value={sort.by}
                onChange={(e) => setSort({ ...sort, by: e.target.value as UnifiedTableSort['by'] })}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
              >
                {showScore && <option value="score">Score</option>}
                {showRank && <option value="rank">Rank</option>}
                <option value="roi">ROI</option>
                <option value="velocity">Velocity</option>
                <option value="bsr">BSR</option>
              </select>
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ordre</label>
              <select
                value={sort.order}
                onChange={(e) => setSort({ ...sort, order: e.target.value as 'asc' | 'desc' })}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
              >
                <option value="desc">Decroissant</option>
                <option value="asc">Croissant</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full md:min-w-[800px]">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
            <tr>
              {showAccordion && <th className="px-3 md:px-4 py-3 w-12"></th>}
              {/* Mobile expand button - only visible on mobile */}
              <th className="md:hidden px-2 py-3 w-10"></th>
              {showRank && (
                <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Rank
                </th>
              )}
              <th className="px-3 md:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                ASIN
              </th>
              <th className="px-3 md:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase max-w-[200px]">
                Titre
              </th>
              {showScore && (
                <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Score
                </th>
              )}
              <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                ROI
              </th>
              <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                Velocity
              </th>
              <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                BSR
              </th>
              {showRecommendation && (
                <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Recommandation
                </th>
              )}
              {showAmazonBadges && (
                <th className="hidden md:table-cell px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Amazon
                </th>
              )}
              {showVerifyButton && (
                <th className="px-3 md:px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {processedProducts.map((product) => {
              const verificationState = getVerificationState?.(product.asin)
              return (
                <UnifiedProductRow
                  key={product.asin}
                  product={product}
                  isExpanded={expandedRow === product.asin}
                  onToggle={() => setExpandedRow(expandedRow === product.asin ? null : product.asin)}
                  features={rowFeatures}
                  onVerify={onVerify}
                  verificationLoading={verificationState?.loading}
                  verificationResult={verificationState?.result}
                  verificationError={verificationState?.error}
                  isVerificationExpanded={isVerificationExpanded?.(product.asin)}
                  onToggleVerification={() => toggleVerificationExpansion?.(product.asin)}
                  AccordionComponent={AccordionComponent}
                  isMobileExpanded={expandedRow === product.asin}
                  onMobileToggle={() => setExpandedRow(expandedRow === product.asin ? null : product.asin)}
                />
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      {showFooterSummary && summaryStats && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>Total: {processedProducts.length} produits</span>
            <div className="flex gap-6">
              <span>
                ROI moyen: <strong className="text-green-600">{summaryStats.avgRoi.toFixed(1)}%</strong>
              </span>
              <span>
                Velocite moyenne: <strong className="text-blue-600">{summaryStats.avgVelocity.toFixed(0)}</strong>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
