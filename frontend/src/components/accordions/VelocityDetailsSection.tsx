/**
 * Section détaillée Velocity - Phase 2.5A Accordéon
 * Affiche les métriques de rotation et d'activité de vente
 */

import type { AccordionSectionProps } from './types'

export function VelocityDetailsSection({ product }: AccordionSectionProps) {
  // Defensive extraction
  const velocityScore = product.raw_metrics?.velocity_score ?? 0
  const breakdown = product.velocity_breakdown

  // Extraction des données velocity avec fallbacks
  const estimatedSales = breakdown?.estimated_sales_30d ?? 0
  const bsrDrops = breakdown?.rank_drops_30d ?? breakdown?.bsr_drops_30d ?? 0
  const buyboxUptime = breakdown?.buybox_uptime_pct ?? null
  const priceVolatility = breakdown?.price_volatility_pct ?? null
  const priceRange = breakdown?.price_range_30d
  const velocityTier = breakdown?.velocity_tier ?? 'unknown'

  // Déterminer la couleur du tier
  const tierColors = {
    fast: 'text-green-600',
    medium: 'text-blue-600',
    slow: 'text-orange-600',
    very_slow: 'text-red-600',
    unknown: 'text-gray-600'
  }

  const tierColor = tierColors[velocityTier as keyof typeof tierColors] || tierColors.unknown

  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-sm text-gray-900 mb-3">⚡ Velocity Overview</h4>

      <div className="space-y-2 text-xs">
        {/* Score et Tier */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Score:</span>
          <span className="font-medium">
            <span className="text-gray-900">{velocityScore.toFixed(0)}</span>
            <span className={`ml-1 ${tierColor} font-semibold`}>
              ({velocityTier.charAt(0).toUpperCase() + velocityTier.slice(1)})
            </span>
          </span>
        </div>

        {/* Ventes estimées */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Est. Sales:</span>
          <span className="font-medium text-gray-900">{estimatedSales} / 30 days</span>
        </div>

        {/* Rank Drops */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Rank Drops:</span>
          <span className="font-medium text-gray-900">{bsrDrops}</span>
        </div>

        {/* Buy Box Uptime */}
        {buyboxUptime !== null && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Buy Box Active:</span>
            <span className="font-medium text-gray-900">{buyboxUptime.toFixed(0)}%</span>
          </div>
        )}

        {/* Price Volatility */}
        {priceVolatility != null && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Price Swings:</span>
            <span className="font-medium text-gray-900">+/-{priceVolatility.toFixed(1)}%</span>
          </div>
        )}

        {/* Price Range */}
        {priceRange?.min != null && priceRange?.max != null && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Price Range:</span>
            <span className="font-medium text-gray-900">
              ${priceRange.min.toFixed(2)} - ${priceRange.max.toFixed(2)}
            </span>
          </div>
        )}
      </div>

      {/* Indicateur visuel selon velocity tier */}
      <div className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-xs">
        {velocityTier === 'fast' && (
          <span className="text-green-700">🚀 Rotation rapide - Opportunité quick flip</span>
        )}
        {velocityTier === 'medium' && (
          <span className="text-blue-700">⚡ Rotation moyenne - Vente sous 30-60 jours</span>
        )}
        {velocityTier === 'slow' && (
          <span className="text-orange-700">🐢 Rotation lente - Risque de stock dormant</span>
        )}
        {velocityTier === 'very_slow' && (
          <span className="text-red-700">❌ Rotation très lente - Éviter sauf niche spécifique</span>
        )}
        {velocityTier === 'unknown' && (
          <span className="text-gray-700">⚠️ Données insuffisantes pour évaluation précise</span>
        )}
      </div>
    </div>
  )
}
