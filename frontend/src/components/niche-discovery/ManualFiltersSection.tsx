/**
 * Manual Filters Section Component
 * Allows users to search with custom filters (category, BSR, price)
 */

import { useState } from 'react'
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
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Toggle Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔍</span>
          <div className="text-left">
            <h3 className="text-lg font-semibold text-gray-900">
              Recherche Personnalisée
            </h3>
            <p className="text-sm text-gray-600">
              Définissez vos propres critères de recherche
            </p>
          </div>
        </div>
        <svg
          className={`w-6 h-6 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Filters Form */}
      {isExpanded && (
        <form onSubmit={handleSubmit} className="p-6 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-6">
            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Catégorie Amazon
              </label>
              <select
                value={filters.category || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    category: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Toutes catégories</option>
                <option value="3">Books</option>
                <option value="172">Electronics</option>
                <option value="193">Toys & Games</option>
                <option value="283155">Self-Help</option>
                <option value="4736">Health & Fitness</option>
              </select>
            </div>

            {/* Max Results */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre max résultats
              </label>
              <input
                type="number"
                value={filters.max_results}
                onChange={(e) =>
                  setFilters({ ...filters, max_results: Number(e.target.value) })
                }
                min={1}
                max={50}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* BSR Min */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                BSR Minimum
              </label>
              <input
                type="number"
                value={filters.bsr_min}
                onChange={(e) =>
                  setFilters({ ...filters, bsr_min: Number(e.target.value) })
                }
                min={1}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* BSR Max */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                BSR Maximum
              </label>
              <input
                type="number"
                value={filters.bsr_max}
                onChange={(e) =>
                  setFilters({ ...filters, bsr_max: Number(e.target.value) })
                }
                min={1}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Price Min */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Price Max */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Min ROI */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Min Velocity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vélocité Minimum
              </label>
              <input
                type="number"
                value={filters.min_velocity}
                onChange={(e) =>
                  setFilters({ ...filters, min_velocity: Number(e.target.value) })
                }
                min={0}
                max={100}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold shadow-md hover:bg-purple-700 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Recherche en cours...' : 'Rechercher'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
            >
              Réinitialiser
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
