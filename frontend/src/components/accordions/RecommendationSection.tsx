/**
 * Section Recommandation - Phase 2.5A Accordéon
 * Génère une recommandation actionable basée sur ROI et Velocity
 */

import type { AccordionSectionProps } from './types'

export function RecommendationSection({ product }: AccordionSectionProps) {
  // Extraction des métriques
  const roi = product.current_roi_pct ?? 0
  const velocityScore = product.raw_metrics?.velocity_score ?? 0
  const amazonOnListing = product.amazon_on_listing
  const amazonBuybox = product.amazon_buybox
  const maxBuy35 = product.max_buy_price_35pct ?? null

  // Logique de recommandation
  let recommendation: {
    emoji: string
    title: string
    message: string
    bgColor: string
    textColor: string
    borderColor: string
  }

  if (roi < 0) {
    // Non rentable
    recommendation = {
      emoji: '❌',
      title: 'À Éviter',
      message: 'ROI négatif aux prix actuels. Attendre une baisse du prix d\'achat ou une hausse du prix de vente.',
      bgColor: 'bg-red-50',
      textColor: 'text-red-800',
      borderColor: 'border-red-200'
    }
  } else if (roi >= 30 && velocityScore >= 70) {
    // Excellent arbitrage
    recommendation = {
      emoji: '🎯',
      title: 'Excellent Arbitrage',
      message: 'ROI élevé avec rotation rapide. Opportunité prioritaire pour maximiser profit et liquidité.',
      bgColor: 'bg-green-50',
      textColor: 'text-green-800',
      borderColor: 'border-green-200'
    }
  } else if (roi >= 20 && velocityScore >= 60) {
    // Bon potentiel
    recommendation = {
      emoji: '✅',
      title: 'Bon Potentiel',
      message: 'ROI acceptable et velocity correcte. Bon candidat pour diversification du stock.',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-800',
      borderColor: 'border-blue-200'
    }
  } else if (velocityScore >= 70 && roi >= 10) {
    // Quick flip
    recommendation = {
      emoji: '⚡',
      title: 'Quick Flip',
      message: 'Rotation rapide malgré ROI modéré. Idéal pour liquidité immédiate et volume d\'affaires.',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-800',
      borderColor: 'border-purple-200'
    }
  } else if (roi >= 30 && velocityScore < 50) {
    // ROI élevé mais lent
    recommendation = {
      emoji: '🐢',
      title: 'ROI Élevé, Rotation Lente',
      message: 'Rentabilité forte mais vente possiblement longue. Acceptable si stock suffisant et patience.',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-800',
      borderColor: 'border-yellow-200'
    }
  } else {
    // Analyser avec prudence
    recommendation = {
      emoji: '⚠️',
      title: 'Analyser avec Prudence',
      message: 'Métriques moyennes. Valider avec recherche manuelle et contexte niche avant achat.',
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-800',
      borderColor: 'border-gray-300'
    }
  }

  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-sm text-gray-900 mb-3">💡 Recommendation</h4>

      <div className={`p-3 rounded ${recommendation.bgColor} border ${recommendation.borderColor}`}>
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-lg">{recommendation.emoji}</span>
          <span className={`font-semibold text-sm ${recommendation.textColor}`}>
            {recommendation.title}
          </span>
        </div>
        <p className={`text-xs ${recommendation.textColor} leading-relaxed`}>
          {recommendation.message}
        </p>
      </div>

      {/* Max Buy Price - Toujours affiché (Option A validée par user) */}
      <div className="mt-3 p-2 bg-purple-50 border border-purple-200 rounded text-xs">
        {maxBuy35 !== null && maxBuy35 > 0 ? (
          <div className="text-purple-800">
            <span className="font-semibold">💰 Prix Max Achat:</span>
            <span className="ml-1 font-bold text-purple-900">${maxBuy35.toFixed(2)}</span>
            <span className="ml-1 text-purple-700">(pour atteindre 35% ROI)</span>
          </div>
        ) : (
          <div className="text-gray-700">
            <span className="font-semibold">💰 Prix Max Achat:</span>
            <span className="ml-1 italic">Aucun prix d'achat rentable aux conditions actuelles</span>
          </div>
        )}
      </div>

      {/* Avertissement si Amazon présent */}
      {(amazonOnListing || amazonBuybox) && (
        <div className="p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-800">
          <span className="font-semibold">⚠️ Amazon Detected:</span>
          {amazonBuybox && <span className="ml-1">Possède Buy Box.</span>}
          {amazonOnListing && !amazonBuybox && <span className="ml-1">Présent sur listing.</span>}
          <span className="ml-1">Compétition accrue, marges possiblement réduites.</span>
        </div>
      )}
    </div>
  )
}
