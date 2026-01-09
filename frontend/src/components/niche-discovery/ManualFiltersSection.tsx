/**
 * Manual Filters Section Component
 * Allows users to search with custom filters (category, BSR, price)
 * Vault Elegance Design - Collapsible accordion
 */

import { useState } from 'react'
import { Search, ChevronDown } from 'lucide-react'
import type { ManualDiscoveryFilters } from '../../services/nicheDiscoveryService'

interface ManualFiltersSectionProps {
  onSearch: (filters: ManualDiscoveryFilters) => void
  isLoading: boolean
}

export function ManualFiltersSection({
  onSearch,
  isLoading,
}: ManualFiltersSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [filters, setFilters] = useState<ManualDiscoveryFilters>({
    category: undefined,
    bsr_min: 10000,
    bsr_max: 100000,
    price_min: 15,
    price_max: 50,
    min_roi: 25,
    min_velocity: 50,
    max_results: 20,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(filters)
  }

  const handleReset = () => {
    setFilters({
      category: undefined,
      bsr_min: 10000,
      bsr_max: 100000,
      price_min: 15,
      price_max: 50,
      min_roi: 25,
      min_velocity: 50,
      max_results: 20,
    })
  }

  return (
    <div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm overflow-hidden">
      {/* Toggle Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-vault-hover transition-colors"
      >
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5 text-vault-accent" />
          <div className="text-left">
            <h3 className="text-base font-semibold text-vault-text">
              Recherche Personnalisee
            </h3>
            <p className="text-sm text-vault-text-secondary">
              Definissez vos propres criteres de recherche
            </p>
          </div>
        </div>
        <ChevronDown
          className={`w-5 h-5 text-vault-text-muted transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Filters Form */}
      {isExpanded && (
        <form onSubmit={handleSubmit} className="px-6 pb-6 pt-2 border-t border-vault-border">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-4">
            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                Categorie Amazon
              </label>
              <select
                value={filters.category || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    category: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              >
                <option value="">Toutes categories</option>
                <option value="3">Books</option>
                <option value="172">Electronics</option>
                <option value="193">Toys & Games</option>
                <option value="283155">Self-Help</option>
                <option value="4736">Health & Fitness</option>
              </select>
            </div>

            {/* Max Results */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                Nombre max resultats
              </label>
              <input
                type="number"
                value={filters.max_results}
                onChange={(e) =>
                  setFilters({ ...filters, max_results: Number(e.target.value) })
                }
                min={1}
                max={50}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* BSR Min */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                BSR Minimum
              </label>
              <input
                type="number"
                value={filters.bsr_min}
                onChange={(e) =>
                  setFilters({ ...filters, bsr_min: Number(e.target.value) })
                }
                min={1}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* BSR Max */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                BSR Maximum
              </label>
              <input
                type="number"
                value={filters.bsr_max}
                onChange={(e) =>
                  setFilters({ ...filters, bsr_max: Number(e.target.value) })
                }
                min={1}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* Price Min */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                Prix Minimum ($)
              </label>
              <input
                type="number"
                value={filters.price_min}
                onChange={(e) =>
                  setFilters({ ...filters, price_min: Number(e.target.value) })
                }
                min={0}
                step={0.01}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* Price Max */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                Prix Maximum ($)
              </label>
              <input
                type="number"
                value={filters.price_max}
                onChange={(e) =>
                  setFilters({ ...filters, price_max: Number(e.target.value) })
                }
                min={0}
                step={0.01}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* Min ROI */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                ROI Minimum (%)
              </label>
              <input
                type="number"
                value={filters.min_roi}
                onChange={(e) =>
                  setFilters({ ...filters, min_roi: Number(e.target.value) })
                }
                min={0}
                max={100}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>

            {/* Min Velocity */}
            <div>
              <label className="block text-sm font-medium text-vault-text-secondary mb-2">
                Velocite Minimum
              </label>
              <input
                type="number"
                value={filters.min_velocity}
                onChange={(e) =>
                  setFilters({ ...filters, min_velocity: Number(e.target.value) })
                }
                min={0}
                max={100}
                className="w-full bg-vault-bg border border-vault-border rounded-xl px-4 py-3 text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-vault-accent hover:bg-vault-accent-dark text-white font-medium px-6 py-3 rounded-xl transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Recherche en cours...' : 'Rechercher'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-6 py-3 bg-vault-hover text-vault-text rounded-xl font-medium hover:bg-vault-border transition-colors"
            >
              Reinitialiser
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
