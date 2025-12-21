/**
 * Niche Card Component
 * Displays a validated niche with stats and top 3 products preview
 */

import type { ValidatedNiche } from '../../services/nicheDiscoveryService'

interface NicheCardProps {
  niche: ValidatedNiche
  onExplore: (niche: ValidatedNiche) => void
}

export function NicheCard({ niche, onExplore }: NicheCardProps) {
  // Quality badge based on combined score
  const avgScore = (niche.avg_roi + niche.avg_velocity) / 2
  const qualityBadge =
    avgScore >= 60
      ? { label: 'Excellent', color: 'bg-green-100 text-green-800' }
      : avgScore >= 45
        ? { label: 'Bon', color: 'bg-blue-100 text-blue-800' }
        : { label: 'Moyen', color: 'bg-yellow-100 text-yellow-800' }

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200 hover:border-purple-300 group">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <span className="text-4xl flex-shrink-0">{niche.icon}</span>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-bold text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-2" title={niche.name}>
                {niche.name}
              </h3>
              <p className="text-sm text-gray-600 mt-1 line-clamp-2" title={niche.description}>
                {niche.description}
              </p>
            </div>
          </div>
          <span
            className={`px-2 py-1 rounded-full text-xs font-semibold flex-shrink-0 ${qualityBadge.color}`}
          >
            {qualityBadge.label}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50">
        <div className="text-center">
          <p className="text-sm text-gray-500 font-medium mb-1">Produits</p>
          <p className="text-3xl font-bold text-purple-600">
            {niche.products_found}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-500 font-medium mb-1">ROI Moyen</p>
          <p className="text-3xl font-bold text-green-600">
            {niche.avg_roi.toFixed(1)}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-500 font-medium mb-1">Vélocité</p>
          <p className="text-3xl font-bold text-blue-600">
            {niche.avg_velocity.toFixed(0)}
          </p>
        </div>
      </div>

      {/* Top 3 Products Preview */}
      <div className="p-6 border-t border-gray-100">
        <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span>🏆</span>
          <span>Top 3 Produits</span>
        </p>
        <ul className="space-y-2">
          {niche.top_products.slice(0, 3).map((product, idx) => (
            <li
              key={product.asin}
              className="flex justify-between items-start text-sm bg-white p-2 rounded-lg border border-gray-100"
            >
              <div className="flex-1 min-w-0">
                <p className="text-gray-800 truncate font-medium">
                  {idx + 1}. {product.title || product.asin}
                </p>
                {product.current_price && (
                  <p className="text-gray-500 text-xs">
                    ${product.current_price.toFixed(2)}
                  </p>
                )}
              </div>
              <div className="ml-3 text-right flex-shrink-0">
                <p className="text-green-600 font-bold">
                  {product.roi_percent.toFixed(0)}%
                </p>
                <p className="text-xs text-gray-500">
                  V:{product.velocity_score.toFixed(0)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explore Button */}
      <div className="p-6 pt-0">
        <button
          onClick={() => onExplore(niche)}
          className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold shadow-md hover:shadow-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center justify-center gap-2 group"
        >
          <span>Explorer cette niche</span>
          <span className="text-lg group-hover:translate-x-1 transition-transform">
            →
          </span>
          <span className="text-xs opacity-75">({niche.products_found} produits)</span>
        </button>
      </div>
    </div>
  )
}
