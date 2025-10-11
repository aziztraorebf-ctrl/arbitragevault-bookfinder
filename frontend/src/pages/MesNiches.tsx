import { useState } from 'react'
import { viewsService } from '../services/viewsService'
import type { ProductScore, StrategyProfile } from '../types/views'

export default function MesNiches() {
  const [identifiers, setIdentifiers] = useState<string>('')
  const [strategy, setStrategy] = useState<StrategyProfile>('balanced')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<ProductScore[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!identifiers.trim()) {
      setError('Veuillez entrer au moins un ASIN ou ISBN')
      return
    }

    setLoading(true)
    setError(null)
    setResults([])

    try {
      // Parse identifiers (comma or newline separated)
      const idList = identifiers
        .split(/[,\n\r]+/)
        .map((id) => id.trim())
        .filter((id) => id.length > 0)

      if (idList.length === 0) {
        throw new Error('Aucun identifiant valide trouvé')
      }

      // Call Phase 2 endpoint with mes_niches view
      const response = await viewsService.scoreProductsForView(
        'mes_niches',
        {
          identifiers: idList,
          strategy: strategy || undefined,
        },
        true // Enable feature flag for dev/test
      )

      setResults(response.products)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'analyse')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setIdentifiers('')
    setResults([])
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📚 Mes Niches</h1>
            <p className="text-gray-500 mt-1">
              Analyse optimisée ROI pour vos niches sauvegardées
            </p>
          </div>
          <div className="text-sm text-gray-400">
            Phase 2 • View-Specific Scoring
          </div>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ASINs / ISBNs à analyser
            </label>
            <textarea
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              placeholder="Entrez vos ASINs ou ISBNs (séparés par virgules ou retours à la ligne)&#10;Exemple: 0593655036, B08X6F12YZ"
              value={identifiers}
              onChange={(e) => setIdentifiers(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stratégie de boost (optionnel)
            </label>
            <select
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              value={strategy || ''}
              onChange={(e) => setStrategy((e.target.value as StrategyProfile) || null)}
            >
              <option value="">Aucune</option>
              <option value="balanced">Balanced (équilibré)</option>
              <option value="textbook">Textbook (livres)</option>
              <option value="velocity">Velocity (rotation rapide)</option>
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
            >
              {loading ? 'Analyse en cours...' : '🔍 Analyser avec scoring ROI prioritaire'}
            </button>
            <button
              onClick={handleClear}
              disabled={loading}
              className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
            >
              Effacer
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">❌ {error}</p>
          </div>
        )}

        {/* Results Section */}
        {results.length > 0 && (
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Résultats ({results.length} produits)
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Scores calculés avec priorité <span className="font-semibold">ROI (0.6)</span> pour Mes Niches
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ASIN
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Titre
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ROI %
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Velocity
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stability
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.map((product, idx) => (
                    <tr key={product.asin || idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        {product.asin || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate">
                        {product.title || 'Titre non disponible'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                            product.score >= 20
                              ? 'bg-green-100 text-green-800'
                              : product.score >= 10
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {product.score.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-900">
                        {product.raw_metrics.roi_percentage.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-900">
                        {product.raw_metrics.velocity_score.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-900">
                        {product.raw_metrics.stability_score.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            💡 Scoring Mes Niches (Phase 2)
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Priorité <strong>ROI (poids 0.6)</strong> pour maximiser rentabilité</li>
            <li>• Velocity (poids 0.4) pour rotation raisonnable</li>
            <li>• Stability (poids 0.5) pour limiter risques</li>
            <li>• Scores différents selon la vue (dashboard, auto_sourcing, etc.)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
