/**
 * Phase 3 Day 9 - Niche Discovery Page
 * One-click niche discovery with curated templates + manual search
 */

import { useState } from 'react'
import { useNicheDiscoveryState } from '../hooks/useNicheDiscovery'
import { CacheIndicator } from '../components/niche-discovery/CacheIndicator'
import { AutoDiscoveryHero } from '../components/niche-discovery/AutoDiscoveryHero'
import { NicheCard } from '../components/niche-discovery/NicheCard'
import { ManualFiltersSection } from '../components/niche-discovery/ManualFiltersSection'
import { ProductsTable } from '../components/niche-discovery/ProductsTable'
import type { ValidatedNiche } from '../services/nicheDiscoveryService'

export default function NicheDiscovery() {
  const {
    discoverAuto,
    isDiscoveringAuto,
    autoDiscoveryData,
    discoverManual,
    isDiscoveringManual,
    manualDiscoveryData,
    exploreNiche,
    isExploringNiche,
    nicheExplorationData,
  } = useNicheDiscoveryState()

  const [lastExploration, setLastExploration] = useState<Date>()
  const [selectedNicheId, setSelectedNicheId] = useState<string>()
  const [viewMode, setViewMode] = useState<'niches' | 'products'>('niches')

  // Auto-discovery handler
  const handleAutoDiscover = () => {
    discoverAuto(
      { count: 3, shuffle: true },
      {
        onSuccess: () => {
          setLastExploration(new Date())
          setViewMode('niches')
          setSelectedNicheId(undefined)
        },
      }
    )
  }

  // Manual search handler
  const handleManualSearch = (filters: any) => {
    discoverManual(filters, {
      onSuccess: () => {
        setViewMode('products')
        setSelectedNicheId(undefined)
      },
    })
  }

  // Niche exploration (drill-down)
  const handleExploreNiche = (niche: ValidatedNiche) => {
    exploreNiche(niche, {
      onSuccess: () => {
        setViewMode('products')
        setSelectedNicheId(niche.id)
      },
    })
  }

  // Current niches and products
  const niches = autoDiscoveryData?.metadata.niches || []
  const products = viewMode === 'products'
    ? (nicheExplorationData?.products || manualDiscoveryData?.products || [])
    : []

  const cacheHit =
    autoDiscoveryData?.cache_hit ||
    manualDiscoveryData?.cache_hit ||
    nicheExplorationData?.cache_hit ||
    false

  const selectedNiche = niches.find((n) => n.id === selectedNicheId)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50 p-8">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              🔍 Niche Discovery
            </h1>
            <p className="text-gray-600 text-lg">
              Découvrez des niches rentables en un clic ou personnalisez votre recherche
            </p>
          </div>
          {cacheHit && <CacheIndicator cacheHit={cacheHit} />}
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Auto-Discovery Hero */}
        <AutoDiscoveryHero
          onExplore={handleAutoDiscover}
          isLoading={isDiscoveringAuto}
          lastExploration={lastExploration}
        />

        {/* Divider "OU" */}
        <div className="flex items-center gap-4">
          <div className="h-px bg-gray-300 flex-1"></div>
          <span className="text-gray-500 font-semibold text-lg px-4 py-2 bg-white rounded-full shadow-sm">
            OU
          </span>
          <div className="h-px bg-gray-300 flex-1"></div>
        </div>

        {/* Manual Filters Section */}
        <ManualFiltersSection
          onSearch={handleManualSearch}
          isLoading={isDiscoveringManual}
        />

        {/* Results: Niches Cards */}
        {viewMode === 'niches' && niches.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>✨</span>
              <span>Niches Découvertes</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {niches.map((niche) => (
                <NicheCard
                  key={niche.id}
                  niche={niche}
                  onExplore={handleExploreNiche}
                />
              ))}
            </div>
          </div>
        )}

        {/* Results: Products Table */}
        {viewMode === 'products' && products.length > 0 && (
          <div>
            {/* Back to Niches Button */}
            {selectedNiche && (
              <div className="mb-4">
                <button
                  onClick={() => {
                    setViewMode('niches')
                    setSelectedNicheId(undefined)
                  }}
                  className="px-4 py-2 bg-white text-purple-600 border border-purple-300 rounded-lg font-medium hover:bg-purple-50 transition-colors flex items-center gap-2"
                >
                  <span>←</span>
                  <span>Retour aux niches</span>
                </button>
              </div>
            )}

            <ProductsTable
              products={products}
              title={
                selectedNiche
                  ? `${selectedNiche.icon} ${selectedNiche.name}`
                  : 'Résultats de recherche'
              }
            />
          </div>
        )}

        {/* Loading State */}
        {(isDiscoveringAuto || isDiscoveringManual || isExploringNiche) && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mb-4"></div>
              <p className="text-gray-600 text-lg font-medium">
                {isDiscoveringAuto && 'Exploration des niches en cours...'}
                {isDiscoveringManual && 'Recherche de produits...'}
                {isExploringNiche && 'Chargement des produits de la niche...'}
              </p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isDiscoveringAuto &&
          !isDiscoveringManual &&
          !isExploringNiche &&
          niches.length === 0 &&
          products.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl shadow-md border border-gray-200">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                Prêt à découvrir des niches rentables ?
              </h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Cliquez sur "Surprise Me!" pour découvrir 3 niches validées avec vraies
                données Keepa, ou utilisez la recherche personnalisée ci-dessus.
              </p>
            </div>
          )}
      </div>
    </div>
  )
}
