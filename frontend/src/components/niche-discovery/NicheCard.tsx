/**
 * Niche Card Component
 * Displays a validated niche with stats and top 3 products preview
 * Vault Elegance Design
 */

import { ArrowRight } from 'lucide-react'
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
      ? { label: 'Excellent', color: 'bg-vault-accent-light text-vault-accent' }
      : avgScore >= 45
        ? { label: 'Bon', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' }
        : { label: 'Moyen', color: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300' }

  return (
    <div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm hover:shadow-vault-md transition-all duration-200 overflow-hidden group">
      {/* Header */}
      <div className="px-5 py-4 border-b border-vault-border-light">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <span className="text-4xl flex-shrink-0">{niche.icon}</span>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-semibold text-vault-text group-hover:text-vault-accent transition-colors line-clamp-2" title={niche.name}>
                {niche.name}
              </h3>
              <p className="text-sm text-vault-text-secondary mt-1 line-clamp-2" title={niche.description}>
                {niche.description}
              </p>
            </div>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium flex-shrink-0 ${qualityBadge.color}`}
          >
            {qualityBadge.label}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 p-5 bg-vault-bg">
        <div className="text-center">
          <p className="text-sm text-vault-text-muted font-medium mb-1">Produits</p>
          <p className="text-2xl font-bold text-vault-accent">
            {niche.products_found}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-vault-text-muted font-medium mb-1">ROI Moyen</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {niche.avg_roi.toFixed(1)}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-vault-text-muted font-medium mb-1">Velocite</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {niche.avg_velocity.toFixed(0)}
          </p>
        </div>
      </div>

      {/* Top 3 Products Preview */}
      <div className="p-5 border-t border-vault-border-light">
        <p className="text-sm font-semibold text-vault-text mb-3 flex items-center gap-2">
          <span>Top 3 Produits</span>
        </p>
        <ul className="space-y-2">
          {niche.top_products.slice(0, 3).map((product, idx) => (
            <li
              key={product.asin}
              className="flex justify-between items-start text-sm bg-vault-bg p-2 rounded-lg border border-vault-border-light"
            >
              <div className="flex-1 min-w-0">
                <p className="text-vault-text truncate font-medium">
                  {idx + 1}. {product.title || product.asin}
                </p>
                {product.current_price && (
                  <p className="text-vault-text-muted text-xs">
                    ${product.current_price.toFixed(2)}
                  </p>
                )}
              </div>
              <div className="ml-3 text-right flex-shrink-0">
                <p className="text-emerald-600 dark:text-emerald-400 font-bold">
                  {product.roi_percent.toFixed(0)}%
                </p>
                <p className="text-xs text-vault-text-muted">
                  V:{product.velocity_score.toFixed(0)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explore Button */}
      <div className="p-5 pt-0">
        <button
          onClick={() => onExplore(niche)}
          className="w-full mt-4 px-4 py-3 rounded-xl font-medium bg-vault-accent hover:bg-vault-accent-dark text-white transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>Explorer cette niche</span>
          <ArrowRight className="w-4 h-4" />
          <span className="text-xs opacity-75">({niche.products_found} produits)</span>
        </button>
      </div>
    </div>
  )
}
