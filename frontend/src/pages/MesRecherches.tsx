/**
 * Mes Recherches Page
 * Display and manage saved search results
 * Phase 11 - Centralized Search Results
 */

import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { Loader2, Inbox, Trash2, Calendar, Package, ExternalLink, Filter, ChevronDown } from 'lucide-react'
import { useInfiniteRecherches, useDeleteRecherche, useRechercheStats } from '../hooks/useRecherches'
import { SOURCE_LABELS, SOURCE_COLORS } from '../types/recherches'
import type { SearchSource, SearchResultSummary } from '../types/recherches'

// Source badge component
function SourceBadge({ source }: { source: SearchSource }) {
  const colorClasses: Record<string, string> = {
    purple: 'bg-vault-accent-light text-vault-accent',
    blue: 'bg-vault-accent-light text-vault-accent',
    green: 'bg-vault-success-light text-vault-success',
  }

  const color = SOURCE_COLORS[source] || 'gray'
  const classes = colorClasses[color] || 'bg-vault-card text-vault-text-secondary'

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${classes}`}>
      {SOURCE_LABELS[source]}
    </span>
  )
}

// Search result card component
function SearchResultCard({
  result,
  onDelete,
  onView,
  isDeleting,
}: {
  result: SearchResultSummary
  onDelete: (id: string) => void
  onView: (id: string) => void
  isDeleting: boolean
}) {
  const createdDate = new Date(result.created_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  const expiresDate = new Date(result.expires_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
  })

  return (
    <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-4 md:p-6 hover:shadow-vault-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <SourceBadge source={result.source} />
            <span className="text-xs text-vault-text-muted">
              Expire le {expiresDate}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-vault-text truncate">
            {result.name}
          </h3>
          <div className="flex items-center gap-4 mt-2 text-sm text-vault-text-secondary">
            <span className="flex items-center gap-1">
              <Package className="w-4 h-4" />
              {result.product_count} produit{result.product_count !== 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {createdDate}
            </span>
          </div>
          {result.notes && (
            <p className="text-sm text-vault-text-muted mt-2 truncate">{result.notes}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => onView(result.id)}
            className="p-2 text-vault-accent hover:bg-vault-accent-light rounded-xl transition-colors"
            title="Voir les resultats"
          >
            <ExternalLink className="w-5 h-5" />
          </button>
          <button
            onClick={() => onDelete(result.id)}
            disabled={isDeleting}
            className="p-2 text-vault-danger hover:bg-vault-danger-light rounded-xl transition-colors disabled:opacity-50"
            title="Supprimer"
          >
            {isDeleting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Trash2 className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function MesRecherches() {
  const navigate = useNavigate()
  const [sourceFilter, setSourceFilter] = useState<SearchSource | undefined>(undefined)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const {
    data,
    isLoading,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteRecherches(sourceFilter)
  const { data: stats } = useRechercheStats()
  const { mutate: deleteRecherche } = useDeleteRecherche()

  // Flatten all pages into a single array of results
  const allResults = useMemo(() => {
    if (!data) return []
    return data.pages.flatMap((page) => page.results)
  }, [data])

  const totalCount = data?.pages[0]?.total_count ?? 0

  const handleDelete = (id: string) => {
    const result = allResults.find((r) => r.id === id)
    if (!result) return

    if (!window.confirm(`Supprimer "${result.name}" ?`)) {
      return
    }

    setDeletingId(id)
    deleteRecherche(id, {
      onSuccess: () => {
        toast.success('Recherche supprimee')
        setDeletingId(null)
      },
      onError: (err) => {
        toast.error(
          `Erreur: ${err instanceof Error ? err.message : 'Erreur inconnue'}`
        )
        setDeletingId(null)
      },
    })
  }

  const handleView = (id: string) => {
    navigate(`/recherches/${id}`)
  }

  const filterButtons: { label: string; value: SearchSource | undefined }[] = [
    { label: 'Toutes', value: undefined },
    { label: 'Niche Discovery', value: 'niche_discovery' },
    { label: 'AutoSourcing', value: 'autosourcing' },
    { label: 'Analyse Manuelle', value: 'manual_analysis' },
  ]

  return (
    <div className="min-h-screen bg-vault-bg">
      <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6 md:space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
            Mes Recherches
          </h1>
          <p className="text-vault-text-secondary text-sm md:text-base mt-2">
            Resultats de recherche sauvegardes (30 jours de retention)
          </p>
        </div>

        {/* Stats Summary */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-vault-card rounded-2xl p-4 shadow-vault-sm border border-vault-border">
              <div className="text-2xl font-bold text-vault-text">{stats.total}</div>
              <div className="text-sm text-vault-text-secondary">Total</div>
            </div>
            <div className="bg-vault-accent-light rounded-2xl p-4 shadow-vault-sm border border-vault-accent/20">
              <div className="text-2xl font-bold text-vault-accent">{stats.niche_discovery}</div>
              <div className="text-sm text-vault-accent">Niche Discovery</div>
            </div>
            <div className="bg-vault-accent-light rounded-2xl p-4 shadow-vault-sm border border-vault-accent/20">
              <div className="text-2xl font-bold text-vault-accent">{stats.autosourcing}</div>
              <div className="text-sm text-vault-accent">AutoSourcing</div>
            </div>
            <div className="bg-vault-accent-light rounded-2xl p-4 shadow-vault-sm border border-vault-accent/20">
              <div className="text-2xl font-bold text-vault-accent">{stats.manual_analysis}</div>
              <div className="text-sm text-vault-accent">Analyse Manuelle</div>
            </div>
          </div>
        )}

        {/* Filter Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="w-4 h-4 text-vault-text-muted" />
          <span className="text-sm text-vault-text-secondary mr-2">Filtrer:</span>
          {filterButtons.map((btn) => (
            <button
              key={btn.label}
              onClick={() => setSourceFilter(btn.value)}
              className={`px-3 py-1.5 text-sm rounded-xl transition-colors ${
                sourceFilter === btn.value
                  ? 'bg-vault-accent text-white'
                  : 'bg-vault-card text-vault-text-secondary border border-vault-border hover:bg-vault-hover'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full" />
            <span className="mt-4 text-vault-text-secondary">
              Chargement de vos recherches...
            </span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
            <p className="text-vault-danger">
              Erreur lors du chargement:{' '}
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-2 text-vault-danger underline hover:opacity-80"
            >
              Reessayer
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && allResults.length === 0 && (
          <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-12 text-center">
            <Inbox className="w-16 h-16 text-vault-text-muted mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-vault-text mb-2">
              Aucune recherche sauvegardee
            </h2>
            <p className="text-vault-text-secondary mb-6">
              {sourceFilter
                ? `Aucun resultat pour ${SOURCE_LABELS[sourceFilter]}.`
                : 'Vos resultats de recherche apparaitront ici apres sauvegarde.'}
            </p>
            <div className="flex justify-center gap-4">
              <a
                href="/niche-discovery"
                className="px-4 py-2 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover transition-colors"
              >
                Niche Discovery
              </a>
              <a
                href="/autosourcing"
                className="px-4 py-2 bg-vault-card text-vault-accent border border-vault-border rounded-xl hover:bg-vault-hover transition-colors"
              >
                AutoSourcing
              </a>
            </div>
          </div>
        )}

        {/* Results List */}
        {!isLoading && allResults.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-vault-text-secondary">
              {allResults.length} sur {totalCount} recherche{totalCount !== 1 ? 's' : ''}
            </div>
            {allResults.map((result) => (
              <SearchResultCard
                key={result.id}
                result={result}
                onDelete={handleDelete}
                onView={handleView}
                isDeleting={deletingId === result.id}
              />
            ))}

            {/* Load More Button */}
            {hasNextPage && (
              <div className="flex justify-center pt-4">
                <button
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="flex items-center gap-2 px-6 py-3 bg-vault-card text-vault-text border border-vault-border rounded-xl hover:bg-vault-hover disabled:opacity-50 transition-colors"
                >
                  {isFetchingNextPage ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Chargement...
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4" />
                      Charger plus ({totalCount - allResults.length} restants)
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
