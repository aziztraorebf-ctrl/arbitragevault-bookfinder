import { useState } from 'react'
import { useStockEstimate } from '../hooks/useStockEstimate'

// ASIN format: B0 + 8 alphanumeric chars (Amazon standard)
const ASIN_REGEX = /^B0[A-Z0-9]{8}$/

export default function StockEstimates() {
  const [asinInput, setAsinInput] = useState('')
  const [submittedAsin, setSubmittedAsin] = useState('')
  const [formatError, setFormatError] = useState<string | null>(null)

  const { data: stockData, isLoading, error, refetch } = useStockEstimate(submittedAsin)

  const validateAsin = (asin: string): boolean => {
    return ASIN_REGEX.test(asin)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const cleanAsin = asinInput.trim().toUpperCase()

    if (!validateAsin(cleanAsin)) {
      setFormatError('Format ASIN invalide. Doit commencer par B0 suivi de 8 caracteres alphanumeriques.')
      return
    }

    setFormatError(null)
    setSubmittedAsin(cleanAsin)
  }

  const getConfidenceBadge = (confidence: string | null) => {
    const styles: Record<string, string> = {
      high: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-red-100 text-red-800',
    }
    return styles[confidence ?? ''] ?? 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Stock Estimates</h1>

      {/* ASIN Input Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <form onSubmit={handleSubmit} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="asin" className="block text-sm font-medium text-gray-700 mb-1">
              ASIN du produit
            </label>
            <input
              type="text"
              id="asin"
              value={asinInput}
              onChange={(e) => setAsinInput(e.target.value)}
              placeholder="Ex: B08N5WRWNW"
              className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              maxLength={10}
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={asinInput.trim().length < 10 || isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Analyse...' : 'Analyser'}
            </button>
          </div>
        </form>
        {formatError && (
          <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-amber-700 text-sm">
            {formatError}
          </div>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-red-800 font-semibold">Erreur</h2>
          <p className="text-red-600 text-sm mt-1">
            {(error as Error & { status?: number })?.status === 404
              ? 'ASIN non trouve dans la base de donnees'
              : (error as Error).message}
          </p>
        </div>
      )}

      {/* Results */}
      {stockData && !isLoading && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">
                Estimation pour {stockData.asin}
              </h2>
              <button
                onClick={() => refetch()}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Rafraichir
              </button>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Stock estimate */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-900">
                  {stockData.estimated_stock ?? 'N/A'}
                </div>
                <div className="text-sm text-gray-600 mt-1">Stock estime</div>
              </div>

              {/* Confidence */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <span className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${getConfidenceBadge(stockData.confidence)}`}>
                  {stockData.confidence ?? 'N/A'}
                </span>
                <div className="text-sm text-gray-600 mt-2">Confiance</div>
              </div>

              {/* Range */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-lg font-semibold text-gray-900">
                  {stockData.range
                    ? `${stockData.range.min} - ${stockData.range.max}`
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-600 mt-1">Fourchette</div>
              </div>

              {/* Data points */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-lg font-semibold text-gray-900">
                  {stockData.data_points ?? 0}
                </div>
                <div className="text-sm text-gray-600 mt-1">Points de donnees</div>
              </div>
            </div>

            {/* Method and timestamp */}
            <div className="mt-6 pt-4 border-t border-gray-200 text-sm text-gray-500">
              <div className="flex justify-between">
                <span>Methode: {stockData.method ?? 'Non specifie'}</span>
                <span>
                  MAJ: {stockData.last_updated
                    ? new Date(stockData.last_updated).toLocaleString()
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state (no ASIN submitted) */}
      {!submittedAsin && !isLoading && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">
            Entrez un ASIN pour obtenir une estimation du stock FBA
          </p>
        </div>
      )}
    </div>
  )
}
