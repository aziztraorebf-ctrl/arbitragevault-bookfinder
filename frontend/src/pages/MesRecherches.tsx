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
    purple: 'bg-purple-100 text-purple-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
  }

  const color = SOURCE_COLORS[source] || 'gray'
  const classes = colorClasses[color] || 'bg-gray-100 text-gray-800'

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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <SourceBadge source={result.source} />
            <span className="text-xs text-gray-400">
              Expire le {expiresDate}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {result.name}
          </h3>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
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
            <p className="text-sm text-gray-500 mt-2 truncate">{result.notes}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => onView(result.id)}
            className="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            title="Voir les resultats"
          >
            <ExternalLink className="w-5 h-5" />
          </button>
          <button
            onClick={() => onDelete(result.id)}
            disabled={isDeleting}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
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
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Mes Recherches
            </h1>
            <p className="text-gray-600 mt-2">
              Resultats de recherche sauvegardes (30 jours de retention)
            </p>
          </div>
          <div className="text-sm text-gray-400">Phase 11</div>
        </div>

        {/* Stats Summary */}
        {stats && (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-sm text-gray-500">Total</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 shadow-sm border border-purple-100">
              <div className="text-2xl font-bold text-purple-700">{stats.niche_discovery}</div>
              <div className="text-sm text-purple-600">Niche Discovery</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4 shadow-sm border border-blue-100">
              <div className="text-2xl font-bold text-blue-700">{stats.autosourcing}</div>
              <div className="text-sm text-blue-600">AutoSourcing</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 shadow-sm border border-green-100">
              <div className="text-2xl font-bold text-green-700">{stats.manual_analysis}</div>
              <div className="text-sm text-green-600">Analyse Manuelle</div>
            </div>
          </div>
        )}

        {/* Filter Buttons */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500 mr-2">Filtrer:</span>
          {filterButtons.map((btn) => (
            <button
              key={btn.label}
              onClick={() => setSourceFilter(btn.value)}
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                sourceFilter === btn.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            <span className="ml-3 text-gray-600">
              Chargement de vos recherches...
            </span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Erreur lors du chargement:{' '}
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-2 text-red-600 underline hover:text-red-800"
            >
              Reessayer
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && allResults.length === 0 && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <Inbox className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              Aucune recherche sauvegardee
            </h2>
            <p className="text-gray-500 mb-6">
              {sourceFilter
                ? `Aucun resultat pour ${SOURCE_LABELS[sourceFilter]}.`
                : 'Vos resultats de recherche apparaitront ici apres sauvegarde.'}
            </p>
            <div className="flex justify-center gap-4">
              <a
                href="/niche-discovery"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Niche Discovery
              </a>
              <a
                href="/autosourcing"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                AutoSourcing
              </a>
            </div>
          </div>
        )}

        {/* Results List */}
        {!isLoading && allResults.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-gray-500">
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
                  className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
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
