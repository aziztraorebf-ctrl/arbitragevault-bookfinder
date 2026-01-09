/**
 * Phase 3 Day 9 - Niche Discovery Page
 * One-click niche discovery with curated templates + manual search
 * Phase 10: Updated to use UnifiedProductTable
 */

import { useState, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useNicheDiscoveryState } from '../hooks/useNicheDiscovery'
import { CacheIndicator } from '../components/niche-discovery/CacheIndicator'
import { AutoDiscoveryHero } from '../components/niche-discovery/AutoDiscoveryHero'
import { NicheCard } from '../components/niche-discovery/NicheCard'
import { ManualFiltersSection } from '../components/niche-discovery/ManualFiltersSection'
import { UnifiedProductTable, useVerification } from '../components/unified'
import { SaveSearchButton } from '../components/recherches/SaveSearchButton'
import { normalizeNicheProduct } from '../types/unified'
import type { ValidatedNiche, NicheStrategy } from '../services/nicheDiscoveryService'
import type { ManualDiscoveryResponse } from '../services/nicheDiscoveryService'
import type { SavedNiche } from '../types/bookmarks'
import type { NicheProduct } from '../types/unified'

export default function NicheDiscovery() {
  const location = useLocation()
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
  const [rerunResults, setRerunResults] = useState<ManualDiscoveryResponse | null>(null)
  const [fromNiche, setFromNiche] = useState<SavedNiche | null>(null)
  const [loadingStrategy, setLoadingStrategy] = useState<NicheStrategy>()

  useEffect(() => {
    const state = location.state as {
      rerunResults?: ManualDiscoveryResponse
      fromNiche?: SavedNiche
      isRefresh?: boolean
    } | null

    if (state?.rerunResults && state?.isRefresh) {
      setRerunResults(state.rerunResults)
      setFromNiche(state.fromNiche || null)
      setViewMode('products')
    }
  }, [location.state])

  // Strategy-based discovery handler
  const handleStrategyDiscover = (strategy: NicheStrategy) => {
    setLoadingStrategy(strategy)
    discoverAuto(
      { count: 3, shuffle: true, strategy },
      {
        onSuccess: () => {
          setLastExploration(new Date())
          setViewMode('niches')
          setSelectedNicheId(undefined)
          setLoadingStrategy(undefined)
        },
        onError: () => {
          setLoadingStrategy(undefined)
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

  // Verification hook for product verification
  const {
    verifyProduct,
    getVerificationState,
    isVerificationExpanded,
    toggleVerificationExpansion,
  } = useVerification()

  const niches = autoDiscoveryData?.metadata.niches || []
  const products = viewMode === 'products'
    ? (rerunResults?.products || nicheExplorationData?.products || manualDiscoveryData?.products || [])
    : []

  // Normalize products for UnifiedProductTable
  const normalizedProducts = useMemo(() => {
    return products.map((p: NicheProduct) => normalizeNicheProduct(p))
  }, [products])

  const cacheHit =
    rerunResults?.cache_hit ||
    autoDiscoveryData?.cache_hit ||
    manualDiscoveryData?.cache_hit ||
    nicheExplorationData?.cache_hit ||
    false

  const selectedNiche = niches.find((n) => n.id === selectedNicheId)

  return (
    <div className="min-h-screen bg-vault-bg">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto mb-4 md:mb-8 overflow-x-hidden">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
              Niche Discovery
            </h1>
            <p className="text-vault-text-secondary text-sm md:text-base mt-2">
              Decouvrez des niches rentables en un clic ou personnalisez votre recherche
            </p>
          </div>
          {cacheHit && <CacheIndicator cacheHit={cacheHit} />}
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6 md:space-y-8 overflow-x-hidden">
        {/* Strategy-Based Discovery Hero */}
        <AutoDiscoveryHero
          onExplore={handleStrategyDiscover}
          isLoading={isDiscoveringAuto}
          loadingStrategy={loadingStrategy}
          lastExploration={lastExploration}
        />

        {/* Divider "OU" */}
        <div className="flex items-center gap-4 my-8">
          <div className="h-px bg-vault-border flex-1"></div>
          <span className="text-vault-text-muted font-medium text-sm px-4 py-1 bg-vault-card border border-vault-border rounded-full">
            OU
          </span>
          <div className="h-px bg-vault-border flex-1"></div>
        </div>

        {/* Manual Filters Section */}
        <ManualFiltersSection
          onSearch={handleManualSearch}
          isLoading={isDiscoveringManual}
        />

        {/* Results: Niches Cards */}
        {viewMode === 'niches' && niches.length > 0 && (
          <div>
            <h2 className="text-2xl font-display font-semibold text-vault-text mb-6">
              Niches Decouvertes
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
          <div className="overflow-x-hidden">
            {/* Actions Bar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
              {/* Back to Niches Button */}
              {selectedNiche ? (
                <button
                  onClick={() => {
                    setViewMode('niches')
                    setSelectedNicheId(undefined)
                  }}
                  className="px-4 py-2 bg-vault-card text-vault-accent border border-vault-border rounded-xl font-medium hover:bg-vault-hover transition-colors flex items-center gap-2"
                >
                  <span>&larr;</span>
                  <span>Retour aux niches</span>
                </button>
              ) : (
                <div />
              )}

              {/* Save Search Button */}
              <SaveSearchButton
                products={normalizedProducts}
                source="niche_discovery"
                defaultName={
                  fromNiche
                    ? `Rerun: ${fromNiche.niche_name}`
                    : selectedNiche
                    ? selectedNiche.name
                    : undefined
                }
                searchParams={
                  manualDiscoveryData
                    ? { type: 'manual' }
                    : selectedNiche
                    ? { niche: selectedNiche.id, strategy: selectedNiche.name }
                    : undefined
                }
              />
            </div>

            <UnifiedProductTable
              products={normalizedProducts}
              title={
                fromNiche
                  ? `Analyse relancee: ${fromNiche.niche_name}`
                  : selectedNiche
                  ? `${selectedNiche.icon} ${selectedNiche.name}`
                  : 'Resultats de recherche'
              }
              features={{
                showRecommendation: true,
                showCategory: true,
                showVerifyButton: true,
                showFooterSummary: true,
                showFilters: true,
                showAccordion: false, // NicheProduct doesn't have accordion content
              }}
              onVerify={verifyProduct}
              getVerificationState={getVerificationState}
              isVerificationExpanded={isVerificationExpanded}
              toggleVerificationExpansion={toggleVerificationExpansion}
            />
          </div>
        )}

        {/* Loading State */}
        {(isDiscoveringAuto || isDiscoveringManual || isExploringNiche) && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-vault-text-secondary text-base mt-4">
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
            <div className="text-center py-12 bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm">
              <h3 className="text-xl font-semibold text-vault-text mb-2">
                Pret a decouvrir des niches rentables ?
              </h3>
              <p className="text-vault-text-secondary text-sm max-w-md mx-auto">
                Choisissez une strategie Textbook ci-dessus pour decouvrir des niches
                validees avec vraies donnees Keepa, ou utilisez la recherche personnalisee.
              </p>
            </div>
          )}
      </div>
    </div>
  )
}
