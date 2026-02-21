import React, { useState, useMemo } from 'react'
import { BarChart3, TrendingUp, TrendingDown, CheckCircle, XCircle, AlertTriangle, ArrowUpDown, ExternalLink, Store } from 'lucide-react'
import type { AnalysisResults, AnalysisAPIResult, PricingDetail } from '../../types'

// Helper: Get best USED pricing from very_good, good, acceptable
// Returns the condition with lowest price that has positive ROI, or recommended
const getBestUsedPricing = (pricing: AnalysisAPIResult['pricing']): { condition: string; detail: PricingDetail } | null => {
  if (!pricing) return null

  // Priority: very_good > good > acceptable (exclude 'new' from USED)
  const usedConditions = ['very_good', 'good', 'acceptable'] as const

  for (const condition of usedConditions) {
    const detail = pricing[condition]
    if (detail?.available && detail.current_price !== null) {
      return { condition, detail }
    }
  }
  return null
}

// Helper: Get best NEW pricing
const getNewPricing = (pricing: AnalysisAPIResult['pricing']): PricingDetail | null => {
  return pricing?.new?.available ? pricing.new : null
}

interface ResultsViewProps {
  results: AnalysisResults
  onExportReady: (results: AnalysisResults) => void
}

type SortField = 'asin' | 'title' | 'roi_percentage' | 'velocity_score' | 'overall_rating'
type SortDirection = 'asc' | 'desc'

const ResultsView: React.FC<ResultsViewProps> = ({ results, onExportReady }) => {
  const [sortField, setSortField] = useState<SortField>('roi_percentage')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [showFailedASINs, setShowFailedASINs] = useState(false)

  // Trigger export readiness
  React.useEffect(() => {
    onExportReady(results)
  }, [results, onExportReady])

  // Sorting logic
  const sortedResults = useMemo(() => {
    console.log("CSV parsed:", results);
    const successful = Array.isArray(results.successful) ? results.successful : [];
    return [...successful].sort((a, b) => {
      let aVal: any, bVal: any

      switch (sortField) {
        case 'asin':
          aVal = a.asin
          bVal = b.asin
          break
        case 'title':
          aVal = a.title || ''
          bVal = b.title || ''
          break
        case 'roi_percentage':
          // ✅ Optional chaining - Pattern Context7 Defensive Programming
          aVal = a?.roi?.roi_percentage != null ? parseFloat(a.roi.roi_percentage.toString()) : 0
          bVal = b?.roi?.roi_percentage != null ? parseFloat(b.roi.roi_percentage.toString()) : 0
          break
        case 'velocity_score':
          // ✅ Optional chaining avec fallback
          aVal = a?.velocity?.velocity_score ?? 0
          bVal = b?.velocity?.velocity_score ?? 0
          break
        case 'overall_rating':
          const ratingOrder = { 'EXCELLENT': 4, 'GOOD': 3, 'FAIR': 2, 'PASS': 1 }
          aVal = ratingOrder[a.overall_rating as keyof typeof ratingOrder] || 0
          bVal = ratingOrder[b.overall_rating as keyof typeof ratingOrder] || 0
          break
        default:
          aVal = a.asin
          bVal = b.asin
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }, [results.successful, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  // Defensive Programming: Check profitability from pricing data
  const getProfitabilityIcon = (result: AnalysisAPIResult) => {
    // Get best ROI from any condition
    const newPrice = getNewPricing(result?.pricing)
    const usedPricing = getBestUsedPricing(result?.pricing)
    const bestRoi = Math.max(
      newPrice?.roi_percentage ?? -Infinity,
      usedPricing?.detail.roi_percentage ?? -Infinity
    )

    // If no pricing data available
    if (bestRoi === -Infinity) {
      return <XCircle className="w-5 h-5 text-gray-400" aria-label="Donnees manquantes" />
    }

    // ROI-based profitability icon
    if (bestRoi >= 40) return <CheckCircle className="w-5 h-5 text-green-600" aria-label="Tres rentable" />
    if (bestRoi >= 20) return <CheckCircle className="w-5 h-5 text-green-500" aria-label="Rentable" />
    if (bestRoi >= 0) return <AlertTriangle className="w-5 h-5 text-yellow-500" aria-label="Borderline" />
    return <XCircle className="w-5 h-5 text-red-500" aria-label="Non rentable" />
  }

  const getOverallRatingStyle = (rating: string) => {
    switch (rating) {
      case 'EXCELLENT': return 'bg-green-100 text-green-800 border-green-200'
      case 'GOOD': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'FAIR': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'PASS': return 'bg-gray-100 text-gray-800 border-gray-200'
      default: return 'bg-gray-100 text-gray-600 border-gray-200'
    }
  }

  const formatROI = (roi: number) => {
    return roi >= 0 ? `+${roi.toFixed(1)}%` : `${roi.toFixed(1)}%`
  }

  // ✅ Defensive: Gérer tier undefined/null
  const getVelocityIcon = (tier: string) => {
    if (!tier) {
      return <TrendingDown className="w-4 h-4 text-gray-400" />
    }
    
    switch (tier.toLowerCase()) {
      case 'very_fast':
      case 'fast':
        return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'moderate':
        return <TrendingUp className="w-4 h-4 text-yellow-500" />
      default:
        return <TrendingDown className="w-4 h-4 text-red-500" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header avec stats globales */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            4. Résultats & Analyse
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-600">{Array.isArray(results.successful) ? results.successful.length : 0}</div>
              <div className="text-sm text-green-700">Analyses réussies</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-xl font-bold text-red-600">{Array.isArray(results.failed) ? results.failed.length : 0}</div>
              <div className="text-sm text-red-700">Échecs</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600">
                {/* Count products with positive ROI */}
                {Array.isArray(results.successful)
                  ? results.successful.filter(r => {
                      const newPrice = getNewPricing(r?.pricing)
                      const usedPricing = getBestUsedPricing(r?.pricing)
                      const bestRoi = Math.max(
                        newPrice?.roi_percentage ?? -Infinity,
                        usedPricing?.detail.roi_percentage ?? -Infinity
                      )
                      return bestRoi >= 20
                    }).length
                  : 0}
              </div>
              <div className="text-sm text-blue-700">Rentables</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-xl font-bold text-purple-600">
                {/* ✅ Optional chaining dans filter */}
                {Array.isArray(results.successful) 
                  ? results.successful.filter(r => r?.overall_rating === 'EXCELLENT').length 
                  : 0}
              </div>
              <div className="text-sm text-purple-700">Excellents</div>
            </div>
          </div>

          {/* Batch Info - Formaté pour lisibilité */}
          <div className="mt-4 text-sm text-gray-500 border-t pt-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <span className="font-medium text-gray-700">Batch ID:</span>
                <br />
                <span className="font-mono text-xs">{results.batchInfo.batch_id}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Temps:</span>
                <br />
                {results.batchInfo.processing_time 
                  ? `${results.batchInfo.processing_time.toFixed(1)}s`
                  : 'N/A'}
              </div>
              <div>
                <span className="font-medium text-gray-700">Total produits:</span>
                <br />
                {results.batchInfo.total_items}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Toggle pour afficher les échecs */}
      {results.failed.length > 0 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowFailedASINs(!showFailedASINs)}
            className="flex items-center text-sm text-red-600 hover:text-red-800"
          >
            <XCircle className="w-4 h-4 mr-1" />
            {showFailedASINs ? 'Masquer' : 'Afficher'} les {results.failed.length} échec(s)
          </button>
        </div>
      )}

      {/* Échecs (si affichés) */}
      {showFailedASINs && results.failed.length > 0 && (
        <div className="bg-red-50 rounded-lg border border-red-200">
          <div className="p-4">
            <h3 className="font-medium text-red-800 mb-3">ASINs en échec</h3>
            <div className="space-y-2">
              {results.failed.map((failed, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="font-mono">{failed.identifier}</span>
                  <span className="text-red-600">{failed.error || failed.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Table des résultats */}
      {results.successful.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="font-medium text-gray-900">
              Résultats détaillés ({results.successful.length} produits)
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statut
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('asin')}
                  >
                    <div className="flex items-center">
                      ASIN
                      <ArrowUpDown className="w-3 h-3 ml-1" />
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('title')}
                  >
                    <div className="flex items-center">
                      Titre
                      <ArrowUpDown className="w-3 h-3 ml-1" />
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    BSR
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amazon
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Prix NEW
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Prix USED
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('roi_percentage')}
                  >
                    <div className="flex items-center">
                      ROI
                      <ArrowUpDown className="w-3 h-3 ml-1" />
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('velocity_score')}
                  >
                    <div className="flex items-center">
                      Velocity
                      <ArrowUpDown className="w-3 h-3 ml-1" />
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('overall_rating')}
                  >
                    <div className="flex items-center">
                      Note Globale
                      <ArrowUpDown className="w-3 h-3 ml-1" />
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Résumé
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Liens
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedResults.map((result) => (
                  <tr key={result?.asin ?? 'unknown'} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getProfitabilityIcon(result)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                      {result?.asin ?? 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={result?.title ?? 'N/A'}>
                      {result?.title ?? 'N/A'}
                    </td>
                    {/* BSR Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-700">
                      {result?.current_bsr ? `#${result.current_bsr.toLocaleString()}` : 'N/A'}
                    </td>
                    {/* Amazon Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {result?.amazon_on_listing ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          <Store className="w-3 h-3 mr-1" />
                          OUI
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          NON
                        </span>
                      )}
                    </td>
                    {/* Prix NEW Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {(() => {
                        const newPrice = getNewPricing(result?.pricing)
                        return newPrice?.current_price !== null && newPrice?.current_price !== undefined ? (
                          <span className="font-semibold text-gray-700">
                            ${newPrice.current_price.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">-</span>
                        )
                      })()}
                    </td>
                    {/* Prix USED Column (best of very_good, good, acceptable) */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {(() => {
                        const usedPricing = getBestUsedPricing(result?.pricing)
                        return usedPricing ? (
                          <div>
                            <span className="font-semibold text-blue-700">
                              ${usedPricing.detail.current_price?.toFixed(2)}
                            </span>
                            <span className="text-xs text-gray-500 ml-1">
                              ({usedPricing.condition.replace('_', ' ')})
                            </span>
                          </div>
                        ) : (
                          <span className="text-gray-400 text-xs">-</span>
                        )
                      })()}
                    </td>
                    {/* ROI Column (best ROI from all conditions) */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {(() => {
                        // Get best ROI from new or used conditions
                        const newPrice = getNewPricing(result?.pricing)
                        const usedPricing = getBestUsedPricing(result?.pricing)
                        const bestRoi = Math.max(
                          newPrice?.roi_percentage ?? -Infinity,
                          usedPricing?.detail.roi_percentage ?? -Infinity
                        )
                        return bestRoi > -Infinity ? (
                          <span className={`font-medium ${
                            bestRoi >= 30 ? 'text-green-600' :
                            bestRoi >= 15 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {formatROI(bestRoi)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )
                      })()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center">
                        {/* Velocity tier/category */}
                        {getVelocityIcon(result?.velocity?.velocity_tier ?? result?.velocity?.velocity_category ?? 'unknown')}
                        <span className="ml-2 capitalize">
                          {(result?.velocity?.velocity_tier ?? result?.velocity?.velocity_category)?.replace('_', ' ') ?? 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded border ${getOverallRatingStyle(result?.overall_rating ?? 'PASS')}`}>
                        {result?.overall_rating ?? 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                      {result?.readable_summary ?? 'Aucun résumé disponible'}
                    </td>
                    {/* Amazon and Seller Central Links */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {(result?.amazon_url || result?.seller_central_url) ? (
                        <div className="flex gap-3">
                          {result.amazon_url && (
                            <a
                              href={result.amazon_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline"
                              title="Voir sur Amazon"
                            >
                              <ExternalLink className="w-3 h-3 mr-1" />
                              Amazon
                            </a>
                          )}
                          {result.seller_central_url && (
                            <a
                              href={result.seller_central_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center text-orange-600 hover:text-orange-800 hover:underline"
                              title="Verifier restrictions de vente"
                            >
                              <ExternalLink className="w-3 h-3 mr-1" />
                              Restrictions
                            </a>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Message si aucun résultat */}
      {/* ✅ Defensive check avec optional chaining */}
      {(!results?.successful || results.successful.length === 0) && (
        <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-6 text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
          <h3 className="font-medium text-yellow-800 mb-2">Aucun résultat exploitable</h3>
          <p className="text-yellow-600 text-sm">
            Toutes les analyses ont échoué. Vérifiez vos ASINs et réessayez.
          </p>
        </div>
      )}

      {/* Debug Info */}
      {import.meta.env.MODE === 'development' && (
        <div className="p-4 bg-gray-100 rounded border text-xs">
          <strong>Debug - Results Summary:</strong>
          <pre className="mt-2 overflow-x-auto">
            {JSON.stringify({
              successful_count: Array.isArray(results.successful) ? results.successful.length : 0,
              failed_count: Array.isArray(results.failed) ? results.failed.length : 0,
              profitable_count: Array.isArray(results.successful)
                ? results.successful.filter(r => {
                    const newPrice = getNewPricing(r?.pricing)
                    const usedPricing = getBestUsedPricing(r?.pricing)
                    const bestRoi = Math.max(
                      newPrice?.roi_percentage ?? -Infinity,
                      usedPricing?.detail.roi_percentage ?? -Infinity
                    )
                    return bestRoi >= 20
                  }).length
                : 0,
              sort: { field: sortField, direction: sortDirection }
            }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default ResultsView