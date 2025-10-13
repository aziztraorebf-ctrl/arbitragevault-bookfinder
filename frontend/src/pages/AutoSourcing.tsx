import { useState } from 'react'
import { viewsService } from '../services/viewsService'
import type { ProductScore, StrategyProfile, ViewScoreMetadata } from '../types/views'
import { ViewResultsTable } from '../components/ViewResultsTable'

export default function AutoSourcing() {
  const [identifiers, setIdentifiers] = useState<string>('')
  const [strategy, setStrategy] = useState<StrategyProfile>('velocity')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<ProductScore[]>([])
  const [metadata, setMetadata] = useState<ViewScoreMetadata | null>(null)
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

      // Call Phase 2 endpoint with auto_sourcing view
      const response = await viewsService.scoreProductsForView(
        'auto_sourcing',
        {
          identifiers: idList,
          strategy: strategy || undefined,
        },
        true // Enable feature flag for dev/test
      )

      setResults(response.products)
      setMetadata(response.metadata)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'analyse')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setIdentifiers('')
    setResults([])
    setMetadata(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📊 AutoSourcing</h1>
            <p className="text-gray-500 mt-1">
              Analyse optimisée Velocity pour rotation rapide et liquidité
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
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              value={strategy || ''}
              onChange={(e) => setStrategy((e.target.value as StrategyProfile) || null)}
            >
              <option value="">Aucune</option>
              <option value="balanced">Balanced (équilibré)</option>
              <option value="textbook">Textbook (livres)</option>
              <option value="velocity">Velocity (rotation rapide) - Recommandé</option>
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
            >
              {loading ? 'Analyse en cours...' : '⚡ Analyser avec scoring Velocity prioritaire'}
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

        {/* Results Section - Using ViewResultsTable */}
        {results.length > 0 && metadata && (
          <ViewResultsTable
            products={results}
            metadata={metadata}
          />
        )}

        {/* Info Footer */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-purple-900 mb-2">
            💡 Scoring AutoSourcing (Phase 2)
          </h3>
          <ul className="text-sm text-purple-800 space-y-1">
            <li>• Priorité <strong>Velocity (poids 0.7)</strong> pour rotation rapide</li>
            <li>• ROI (poids 0.3) pour rentabilité minimale acceptable</li>
            <li>• Stability (poids 0.1) pour liquidité immédiate</li>
            <li>• Idéal pour produits à écoulement rapide (quick flips)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
