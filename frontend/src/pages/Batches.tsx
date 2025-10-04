import { useState } from 'react'
import { RefreshCw, Plus, AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react'
import { useBatches, useBatchesStats, useConnectionStatus } from '../hooks'
import { BatchCard, BatchesLoadingSkeleton, ConnectionStatus } from '../components/business'
import type { Batch } from '../hooks'

export default function Batches() {
  const [page, setPage] = useState(1)
  // const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null) // TODO: Implement batch detail view
  const pageSize = 12

  // Fetch batches and stats
  const { 
    data: batchesData, 
    isLoading, 
    isError, 
    error, 
    refetch,
    isFetching 
  } = useBatches(page, pageSize)

  const { stats, isLoading: statsLoading } = useBatchesStats()
  
  // Connection status for monitoring
  const connectionStatus = useConnectionStatus()

  // Handle batch card click
  const handleBatchClick = (batch: Batch) => {
    // setSelectedBatch(batch) // TODO: Implement batch detail view
    // Could navigate to batch detail page or open modal
    console.log('Selected batch:', batch)
  }

  // Handle page navigation
  const handleNextPage = () => {
    if (batchesData?.has_next) {
      setPage(prev => prev + 1)
    }
  }

  const handlePrevPage = () => {
    if (batchesData?.has_prev) {
      setPage(prev => Math.max(1, prev - 1))
    }
  }

  // Loading state
  if (isLoading) {
    return <BatchesLoadingSkeleton />
  }

  // Error state
  if (isError) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="typography-h1">Batches d'Analyse</h1>
          <button
            onClick={() => refetch()}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Réessayer</span>
          </button>
        </div>

        {/* Error state */}
        <div className="card p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="typography-h2 mb-2">Erreur de chargement</h2>
          <p className="typography-body text-gray-600 mb-4">
            Impossible de charger les batches d'analyse.
          </p>
          <p className="typography-secondary text-red-600 mb-4">
            {error instanceof Error ? error.message : 'Une erreur inconnue est survenue'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn-primary"
          >
            Réessayer
          </button>
        </div>
      </div>
    )
  }

  const batches = batchesData?.batches || []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="typography-h1">Batches d'Analyse</h1>
          <p className="typography-body text-gray-600 mt-1">
            Gérez et surveillez vos analyses de produits
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <ConnectionStatus 
            isConnected={connectionStatus.isConnected}
            isChecking={connectionStatus.isChecking}
            error={connectionStatus.error}
          />
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          <button className="btn-primary flex items-center space-x-2">
            <Plus className="w-4 h-4" />
            <span>Nouvelle Analyse</span>
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="quick-stats">
        <div className="stat-item">
          <div className="stat-number color-blue">{statsLoading ? '...' : stats.total}</div>
          <div className="stat-label">Total Batches</div>
          <div className="text-xs color-blue mt-1">📊 Analyses créées</div>
        </div>
        <div className="stat-item">
          <div className="stat-number color-green">{statsLoading ? '...' : stats.completed}</div>
          <div className="stat-label">Terminés</div>
          <div className="text-xs color-green mt-1">✅ Avec succès</div>
        </div>
        <div className="stat-item">
          <div className="stat-number color-violet">{statsLoading ? '...' : stats.processing}</div>
          <div className="stat-label">En cours</div>
          <div className="text-xs color-violet mt-1">⚡ Traitement actif</div>
        </div>
        <div className="stat-item">
          <div className="stat-number color-orange">{statsLoading ? '...' : `${stats.successRate}%`}</div>
          <div className="stat-label">Taux Succès</div>
          <div className="text-xs color-orange mt-1">🎯 Efficacité globale</div>
        </div>
      </div>

      {/* Status Filter Tabs (Future enhancement) */}
      <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg w-fit">
        {[
          { key: 'all', label: 'Tous', icon: null },
          { key: 'completed', label: 'Terminés', icon: CheckCircle },
          { key: 'processing', label: 'En cours', icon: Clock },
          { key: 'failed', label: 'Échoués', icon: XCircle },
        ].map((filter) => (
          <button
            key={filter.key}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter.key === 'all' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              {filter.icon && <filter.icon className="w-4 h-4" />}
              <span>{filter.label}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Batches Grid */}
      {batches.length > 0 ? (
        <div className="dashboard-cards-grid">
          {batches.map((batch) => (
            <BatchCard
              key={batch.batch_id}
              batch={batch}
              onClick={handleBatchClick}
              className="h-full"
            />
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="card p-8 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="typography-h2 mb-2">Aucun batch trouvé</h2>
          <p className="typography-body text-gray-600 mb-4">
            Vous n'avez pas encore créé d'analyse de produits.
          </p>
          <button className="btn-primary flex items-center space-x-2 mx-auto">
            <Plus className="w-4 h-4" />
            <span>Créer votre première analyse</span>
          </button>
        </div>
      )}

      {/* Pagination */}
      {batchesData && batches.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="typography-body text-gray-600">
            Page {page} sur {Math.ceil((batchesData.total || 0) / pageSize)} • {batchesData.total} batch(es) au total
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrevPage}
              disabled={!batchesData.has_prev}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Précédent
            </button>
            <button
              onClick={handleNextPage}
              disabled={!batchesData.has_next}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Suivant
            </button>
          </div>
        </div>
      )}
    </div>
  )
}