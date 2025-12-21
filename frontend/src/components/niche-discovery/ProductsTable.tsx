/**
 * Products Table Component
 * Displays drill-down products with ROI, velocity, price, BSR
 * Phase 8: Added Verify button for pre-purchase verification
 */

import { useState, Fragment } from 'react'
import {
  verificationService,
  type VerificationResponse,
  type VerificationStatus,
} from '../../services/verificationService'

interface Product {
  asin: string
  title?: string
  roi_percent: number
  velocity_score: number
  recommendation: string
  current_price?: number
  bsr?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
  fba_seller_count?: number
}

interface ProductsTableProps {
  products: Product[]
  title?: string
}

interface VerificationState {
  loading: boolean
  result?: VerificationResponse
  error?: string
}

export function ProductsTable({ products, title = 'Produits Trouves' }: ProductsTableProps) {
  const [verificationStates, setVerificationStates] = useState<Record<string, VerificationState>>({})
  const [expandedVerification, setExpandedVerification] = useState<string | null>(null)

  if (products.length === 0) {
    return null
  }

  // Recommendation badge colors
  const getRecommendationBadge = (recommendation: string) => {
    const badges: Record<string, { label: string; color: string }> = {
      STRONG_BUY: { label: 'Achat Fort', color: 'bg-green-600 text-white' },
      BUY: { label: 'Acheter', color: 'bg-green-500 text-white' },
      CONSIDER: { label: 'Considerer', color: 'bg-yellow-500 text-white' },
      SKIP: { label: 'Passer', color: 'bg-red-500 text-white' },
    }
    return badges[recommendation] || { label: recommendation, color: 'bg-gray-500 text-white' }
  }

  // Verification status badge
  const getVerificationBadge = (status: VerificationStatus) => {
    const badges: Record<VerificationStatus, { label: string; color: string; bgColor: string }> = {
      ok: { label: 'OK', color: 'text-green-700', bgColor: 'bg-green-100 border-green-300' },
      changed: { label: 'Modifie', color: 'text-yellow-700', bgColor: 'bg-yellow-100 border-yellow-300' },
      avoid: { label: 'Eviter', color: 'text-red-700', bgColor: 'bg-red-100 border-red-300' },
    }
    return badges[status] || badges.avoid
  }

  // Handle verification click
  const handleVerify = async (product: Product) => {
    const asin = product.asin

    // Set loading state
    setVerificationStates((prev) => ({
      ...prev,
      [asin]: { loading: true },
    }))

    try {
      const result = await verificationService.verifyProduct({
        asin,
        saved_price: product.current_price,
        saved_bsr: product.bsr,
        saved_fba_count: product.fba_seller_count,
      })

      setVerificationStates((prev) => ({
        ...prev,
        [asin]: { loading: false, result },
      }))

      // Auto-expand result panel
      setExpandedVerification(asin)
    } catch (error) {
      setVerificationStates((prev) => ({
        ...prev,
        [asin]: {
          loading: false,
          error: error instanceof Error ? error.message : 'Erreur de verification',
        },
      }))
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>Products</span>
          <span>{title}</span>
          <span className="text-sm font-normal text-gray-600">
            ({products.length} produits)
          </span>
        </h3>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                ASIN / Titre
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                ROI
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Velocite
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Prix
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                BSR
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Recommandation
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {products.map((product) => {
              const badge = getRecommendationBadge(product.recommendation)
              const verifyState = verificationStates[product.asin]
              const isExpanded = expandedVerification === product.asin

              return (
                <Fragment key={product.asin}>
                  <tr
                    className="hover:bg-gray-50 transition-colors"
                  >
                    {/* ASIN / Title */}
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900 mb-1">
                          {product.title || product.asin}
                        </p>
                        <p className="text-xs text-gray-500 font-mono">
                          {product.asin}
                        </p>
                        {product.category_name && (
                          <p className="text-xs text-gray-400 mt-1">
                            {product.category_name}
                          </p>
                        )}
                      </div>
                    </td>

                    {/* ROI */}
                    <td className="px-6 py-4 text-center">
                      <span className="text-lg font-bold text-green-600">
                        {product.roi_percent.toFixed(1)}%
                      </span>
                      {product.estimated_profit !== undefined && (
                        <p className="text-xs text-gray-500 mt-1">
                          ${product.estimated_profit.toFixed(2)} profit
                        </p>
                      )}
                    </td>

                    {/* Velocity */}
                    <td className="px-6 py-4 text-center">
                      <span className="text-lg font-bold text-blue-600">
                        {product.velocity_score.toFixed(0)}
                      </span>
                    </td>

                    {/* Price */}
                    <td className="px-6 py-4 text-center">
                      {product.current_price !== undefined ? (
                        <div>
                          <span className="text-sm font-semibold text-gray-900">
                            ${product.current_price.toFixed(2)}
                          </span>
                          {product.fba_fees !== undefined && (
                            <p className="text-xs text-gray-500">
                              FBA: ${product.fba_fees.toFixed(2)}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">N/A</span>
                      )}
                    </td>

                    {/* BSR */}
                    <td className="px-6 py-4 text-center">
                      {product.bsr !== undefined ? (
                        <span className="text-sm text-gray-700 font-mono">
                          #{product.bsr.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">N/A</span>
                      )}
                    </td>

                    {/* Recommendation */}
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    </td>

                    {/* Actions - Verify Button */}
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <button
                          onClick={() => handleVerify(product)}
                          disabled={verifyState?.loading}
                          className={`
                            px-3 py-1.5 text-xs font-medium rounded-md border transition-all
                            ${verifyState?.loading
                              ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                              : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 hover:border-blue-300'
                            }
                          `}
                        >
                          {verifyState?.loading ? (
                            <span className="flex items-center gap-1">
                              <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                                <circle
                                  className="opacity-25"
                                  cx="12"
                                  cy="12"
                                  r="10"
                                  stroke="currentColor"
                                  strokeWidth="4"
                                  fill="none"
                                />
                                <path
                                  className="opacity-75"
                                  fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                                />
                              </svg>
                              Verification...
                            </span>
                          ) : (
                            'Verifier'
                          )}
                        </button>

                        {/* Verification Result Badge */}
                        {verifyState?.result && (
                          <button
                            onClick={() =>
                              setExpandedVerification(isExpanded ? null : product.asin)
                            }
                            className={`
                              px-2 py-0.5 text-xs font-medium rounded border
                              ${getVerificationBadge(verifyState.result.status).bgColor}
                              ${getVerificationBadge(verifyState.result.status).color}
                            `}
                          >
                            {getVerificationBadge(verifyState.result.status).label}
                            <span className="ml-1">{isExpanded ? 'chevron-up' : 'chevron-down'}</span>
                          </button>
                        )}

                        {/* Error */}
                        {verifyState?.error && (
                          <span className="text-xs text-red-600 max-w-[120px] truncate">
                            {verifyState.error}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>

                  {/* Expanded Verification Details Row */}
                  {isExpanded && verifyState?.result && (
                    <tr className="bg-gray-50">
                      <td colSpan={7} className="px-6 py-4">
                        <VerificationDetails result={verifyState.result} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>Total: {products.length} produits</span>
          <div className="flex gap-6">
            <span>
              ROI moyen:{' '}
              <strong className="text-green-600">
                {(
                  products.reduce((sum, p) => sum + p.roi_percent, 0) / products.length
                ).toFixed(1)}
                %
              </strong>
            </span>
            <span>
              Velocite moyenne:{' '}
              <strong className="text-blue-600">
                {(
                  products.reduce((sum, p) => sum + p.velocity_score, 0) /
                  products.length
                ).toFixed(0)}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Verification Details Component
 * Shows expanded verification result with changes
 */
function VerificationDetails({ result }: { result: VerificationResponse }) {
  const statusColors: Record<VerificationStatus, string> = {
    ok: 'border-green-500',
    changed: 'border-yellow-500',
    avoid: 'border-red-500',
  }

  return (
    <div className={`border-l-4 ${statusColors[result.status]} pl-4`}>
      {/* Message */}
      <p className="text-sm font-medium text-gray-700 mb-3">{result.message}</p>

      {/* Current Data Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
        {result.current_price !== undefined && (
          <div>
            <p className="text-xs text-gray-500">Prix actuel</p>
            <p className="text-sm font-semibold">${result.current_price.toFixed(2)}</p>
          </div>
        )}
        {result.current_bsr !== undefined && (
          <div>
            <p className="text-xs text-gray-500">BSR actuel</p>
            <p className="text-sm font-semibold">#{result.current_bsr.toLocaleString()}</p>
          </div>
        )}
        {result.current_fba_count !== undefined && (
          <div>
            <p className="text-xs text-gray-500">Vendeurs FBA</p>
            <p className="text-sm font-semibold">{result.current_fba_count}</p>
          </div>
        )}
        {result.estimated_profit !== undefined && (
          <div>
            <p className="text-xs text-gray-500">Profit estime</p>
            <p className="text-sm font-semibold text-green-600">
              ${result.estimated_profit.toFixed(2)}
              {result.profit_change_percent !== undefined && (
                <span
                  className={`ml-1 text-xs ${
                    result.profit_change_percent >= 0 ? 'text-green-500' : 'text-red-500'
                  }`}
                >
                  ({result.profit_change_percent >= 0 ? '+' : ''}
                  {result.profit_change_percent.toFixed(1)}%)
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Amazon Warning */}
      {result.amazon_selling && (
        <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 mb-3">
          <p className="text-sm text-red-700 font-medium">
            Attention: Amazon vend ce produit directement
          </p>
        </div>
      )}

      {/* Changes List */}
      {result.changes.length > 0 && (
        <div className="mt-2">
          <p className="text-xs text-gray-500 uppercase mb-1">Changements detectes:</p>
          <ul className="space-y-1">
            {result.changes.map((change, idx) => (
              <li
                key={idx}
                className={`text-xs px-2 py-1 rounded ${
                  change.severity === 'critical'
                    ? 'bg-red-50 text-red-700'
                    : change.severity === 'warning'
                    ? 'bg-yellow-50 text-yellow-700'
                    : 'bg-gray-50 text-gray-700'
                }`}
              >
                {change.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Verification Timestamp */}
      <p className="text-xs text-gray-400 mt-3">
        Verifie le: {new Date(result.verified_at).toLocaleString()}
      </p>
    </div>
  )
}
