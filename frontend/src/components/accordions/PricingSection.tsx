/**
 * Section Pricing USED vs NEW - Design "USED Focus"
 * Affiche les prix USED prominemment (recommandé pour FBA)
 * et NEW comme alternative dans la section expandable
 */

import { useState } from 'react'
import type { AnalysisResult } from '../../types/keepa'

interface PricingSectionProps {
  analysis: AnalysisResult
  isExpanded?: boolean
}

export function PricingSection({ analysis, isExpanded: initialExpanded = false }: PricingSectionProps) {
  const [showNewPricing, setShowNewPricing] = useState(initialExpanded)
  const pricingUsed = analysis.pricing?.used
  const pricingNew = analysis.pricing?.new

  if (!pricingUsed && !pricingNew) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-600">
        ℹ️ Aucune donnée de pricing disponible
      </div>
    )
  }

  // Helper pour formater les prix
  const formatPrice = (price: number | null): string => {
    return price !== null ? `$${price.toFixed(2)}` : 'N/A'
  }

  // Helper pour formater le ROI
  const formatROI = (roi: number | null): string => {
    if (roi === null) return 'N/A'
    return roi >= 0 ? `+${roi.toFixed(1)}%` : `${roi.toFixed(1)}%`
  }

  // Helper pour la couleur du ROI
  const getROIColor = (roi: number | null): string => {
    if (roi === null) return 'text-gray-600'
    if (roi >= 30) return 'text-green-600'
    if (roi >= 15) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-3">
      {/* Section USED - Toujours visible (recommandé) */}
      {pricingUsed && (
        <div className="border-2 border-green-200 bg-green-50 rounded-lg p-4">
          {/* Badge recommandé */}
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-sm text-gray-900">💚 Pricing USED</h4>
            <span className="text-xs px-2 py-1 bg-green-600 text-white rounded-full font-medium">
              ✅ Recommandé pour FBA
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {/* Prix actuel USED */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Prix Achat Actuel</span>
              {pricingUsed.available && pricingUsed.current_price !== null ? (
                <span className="font-bold text-lg text-blue-700">
                  {formatPrice(pricingUsed.current_price)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">Non disponible</span>
              )}
            </div>

            {/* ROI USED */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">ROI Estimé</span>
              {pricingUsed.available && pricingUsed.roi_percentage !== null ? (
                <span className={`font-bold text-lg ${getROIColor(pricingUsed.roi_percentage)}`}>
                  {formatROI(pricingUsed.roi_percentage)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">—</span>
              )}
            </div>

            {/* Prix cible */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Prix Cible (30% ROI)</span>
              <span className="font-medium text-purple-600">
                {formatPrice(pricingUsed.target_buy_price)}
              </span>
            </div>

            {/* Net profit */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Net Profit</span>
              {pricingUsed.available && pricingUsed.net_profit !== null ? (
                <span className={`font-medium ${pricingUsed.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatPrice(pricingUsed.net_profit)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">—</span>
              )}
            </div>
          </div>

          {/* Message si prix USED pas disponible */}
          {!pricingUsed.available && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              ⚠️ Aucune offre USED actuellement. Prix cible affiché pour référence.
            </div>
          )}

          {/* Message si ROI négatif */}
          {pricingUsed.available &&
           pricingUsed.roi_percentage !== null &&
           pricingUsed.roi_percentage < 0 && (
            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
              ❌ Prix USED actuel trop élevé. Attendre une meilleure opportunité (prix cible: {formatPrice(pricingUsed.target_buy_price)})
            </div>
          )}

          {/* Message si ROI positif */}
          {pricingUsed.available &&
           pricingUsed.roi_percentage !== null &&
           pricingUsed.roi_percentage >= 30 && (
            <div className="mt-3 p-2 bg-green-100 border border-green-300 rounded text-xs text-green-900 font-medium">
              ✅ Excellente opportunité FBA USED ! ROI &gt; 30%
            </div>
          )}
        </div>
      )}

      {/* Section NEW - Visible seulement si expanded (alternative) */}
      {pricingNew && showNewPricing && (
        <div className="border border-gray-200 bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-sm text-gray-700">📦 Pricing NEW (Alternative)</h4>
            <span className="text-xs px-2 py-1 bg-gray-300 text-gray-700 rounded-full">
              Alternative
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {/* Prix actuel NEW */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Prix Achat Actuel</span>
              {pricingNew.available && pricingNew.current_price !== null ? (
                <span className="font-bold text-lg text-blue-700">
                  {formatPrice(pricingNew.current_price)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">Non disponible</span>
              )}
            </div>

            {/* ROI NEW */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">ROI Estimé</span>
              {pricingNew.available && pricingNew.roi_percentage !== null ? (
                <span className={`font-bold text-lg ${getROIColor(pricingNew.roi_percentage)}`}>
                  {formatROI(pricingNew.roi_percentage)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">—</span>
              )}
            </div>

            {/* Prix cible */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Prix Cible (30% ROI)</span>
              <span className="font-medium text-purple-600">
                {formatPrice(pricingNew.target_buy_price)}
              </span>
            </div>

            {/* Net profit */}
            <div>
              <span className="text-gray-600 text-xs block mb-1">Net Profit</span>
              {pricingNew.available && pricingNew.net_profit !== null ? (
                <span className={`font-medium ${pricingNew.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatPrice(pricingNew.net_profit)}
                </span>
              ) : (
                <span className="text-gray-400 text-sm">—</span>
              )}
            </div>
          </div>

          {/* Note explicative */}
          <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
            ℹ️ Prix NEW généralement moins rentable (concurrence Amazon, marges faibles)
          </div>
        </div>
      )}

      {/* Bouton pour toggle expanded (si NEW existe) */}
      {pricingNew && !showNewPricing && (
        <button
          className="w-full text-sm text-gray-600 hover:text-gray-900 py-2 border border-gray-200 rounded hover:bg-gray-50 transition-colors"
          onClick={() => setShowNewPricing(true)}
        >
          Voir aussi pricing NEW (alternative)
        </button>
      )}

      {/* Bouton pour collapse (si NEW est visible) */}
      {pricingNew && showNewPricing && (
        <button
          className="w-full text-sm text-gray-500 hover:text-gray-700 py-2 border border-gray-200 rounded hover:bg-gray-50 transition-colors"
          onClick={() => setShowNewPricing(false)}
        >
          Masquer pricing NEW
        </button>
      )}
    </div>
  )
}
