import { useState } from 'react'
import { useAllStrategicViews, useStrategicView } from '../hooks/useStrategicViews'
import type { ViewType, StrategicMetric } from '../types/strategic'

const VIEW_LABELS: Record<ViewType, { label: string; description: string }> = {
  velocity: { label: 'Velocite', description: 'Analyse de la vitesse de vente' },
  competition: { label: 'Competition', description: 'Analyse des concurrents' },
  volatility: { label: 'Volatilite', description: 'Stabilite des prix' },
  consistency: { label: 'Consistance', description: 'Regularite des ventes' },
  confidence: { label: 'Confiance', description: 'Score de fiabilite global' },
}

export default function AnalyseStrategique() {
  const [selectedView, setSelectedView] = useState<ViewType>('velocity')

  const { data: allViews, isLoading: loadingAll } = useAllStrategicViews()
  const { data: viewData, isLoading: loadingView, error } = useStrategicView(selectedView)

  if (loadingAll) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analyse Strategique</h1>

      {/* View selector tabs */}
      <div className="flex space-x-2 mb-6 border-b border-gray-200">
        {(Object.keys(VIEW_LABELS) as ViewType[]).map((viewType) => (
          <button
            key={viewType}
            onClick={() => setSelectedView(viewType)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              selectedView === viewType
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {VIEW_LABELS[viewType].label}
          </button>
        ))}
      </div>

      {/* View description */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <p className="text-blue-800">{VIEW_LABELS[selectedView].description}</p>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <h2 className="text-red-800 font-semibold">Erreur</h2>
          <p className="text-red-600 text-sm mt-1">
            {(error as Error).message}
          </p>
        </div>
      )}

      {/* Loading state for view data */}
      {loadingView && (
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      )}

      {/* View data display */}
      {viewData && !loadingView && (
        <div className="space-y-6">
          {/* Summary card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Resume</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {viewData.summary?.total_products ?? 0}
                </div>
                <div className="text-sm text-gray-600">Produits analyses</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {viewData.summary?.avg_score?.toFixed(1) ?? 'N/A'}
                </div>
                <div className="text-sm text-gray-600">Score moyen</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-900">
                  {viewData.summary?.recommendation ?? 'Aucune recommandation'}
                </div>
                <div className="text-sm text-gray-600">Recommandation</div>
              </div>
            </div>
          </div>

          {/* Metrics table */}
          {viewData.metrics && Object.keys(viewData.metrics).length > 0 && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">Metriques detaillees</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Niche
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Label
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Description
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(viewData.metrics).map(([niche, metric]) => {
                      const typedMetric = metric as StrategicMetric
                      const colorClasses: Record<string, string> = {
                        green: 'bg-green-100 text-green-800',
                        yellow: 'bg-yellow-100 text-yellow-800',
                        red: 'bg-red-100 text-red-800',
                        gray: 'bg-gray-100 text-gray-800',
                      }
                      const badgeClass = colorClasses[typedMetric?.color ?? 'gray'] ?? colorClasses.gray

                      return (
                        <tr key={niche} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {niche}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${badgeClass}`}>
                              {typedMetric?.score?.toFixed(1) ?? 'N/A'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {typedMetric?.label ?? '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {typedMetric?.description ?? '-'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Calculated at timestamp */}
          <div className="text-sm text-gray-500 text-right">
            Calcule le: {viewData.calculated_at ? new Date(viewData.calculated_at).toLocaleString() : 'N/A'}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loadingView && !viewData && !error && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">Aucune donnee disponible pour cette vue.</p>
        </div>
      )}
    </div>
  )
}
