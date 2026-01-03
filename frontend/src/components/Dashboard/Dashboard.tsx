import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { KeepaHealthResponse } from '../../types/keepa'

/**
 * Dashboard - Main application dashboard with KPI cards and quick actions
 *
 * UX Constants:
 * - min-h-[44px]: Minimum touch target size per Apple HIG guidelines
 *   Ensures buttons are easily tappable on mobile devices
 * - py-3 (12px): Vertical padding for comfortable touch interaction
 */

const API_URL =
  import.meta.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com'

export default function Dashboard() {
  const navigate = useNavigate()
  const [balance, setBalance] = useState<number | null>(null)
  const [lastCheck, setLastCheck] = useState<Date | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkBalance = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/v1/keepa/health`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data: KeepaHealthResponse = await response.json()
      setBalance(data.tokens.remaining)
      setLastCheck(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch balance')
      console.error('Failed to check Keepa balance:', err)
    } finally {
      setLoading(false)
    }
  }

  const getBalanceColor = (): string => {
    if (balance === null) return 'gray'
    if (balance >= 100) return 'green'
    if (balance >= 20) return 'yellow'
    return 'red'
  }

  const getTimeSinceCheck = (): string => {
    if (!lastCheck) return ''
    const seconds = Math.floor((Date.now() - lastCheck.getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ago`
  }

  return (
    <div className="space-y-8">
      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* KPI 1: Analyses ce mois */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">📈</span>
            <span className="text-gray-500 text-sm">Analyses ce mois</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">1 247</div>
          <div className="text-sm text-gray-500 mt-1">produits</div>
        </div>

        {/* KPI 2: Niches découvertes */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">🔍</span>
            <span className="text-gray-500 text-sm">Niches découvertes</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">89</div>
          <div className="text-sm text-gray-500 mt-1">niches actives</div>
        </div>

        {/* KPI 3: ROI moyen */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">💰</span>
            <span className="text-gray-500 text-sm">ROI moyen</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">43,2 %</div>
        </div>

        {/* KPI 4: Keepa API Balance */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-between">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">🔑</span>
            <span className="text-gray-500 text-sm">Keepa API Balance</span>
          </div>

          <button
            onClick={checkBalance}
            disabled={loading}
            className="w-full px-4 py-3 min-h-[44px] bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 text-sm font-medium"
          >
            {loading ? 'Checking...' : 'Check Balance'}
          </button>

          {balance !== null && (
            <div className="mt-3 w-full">
              <div className={`text-2xl font-bold text-${getBalanceColor()}-600`}>
                {balance} tokens
              </div>
              {lastCheck && (
                <div className="text-sm text-gray-500 mt-1">
                  Last check: {getTimeSinceCheck()}
                </div>
              )}
              {balance < 100 && (
                <div className="text-sm text-yellow-600 mt-2 flex items-center gap-1">
                  <span>⚠️</span>
                  <span>Low balance warning</span>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="mt-2 text-sm text-red-500 w-full">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Section Title */}
      <div>
        <h2 className="text-xl font-semibold text-gray-700">Actions Rapides</h2>
      </div>

      {/* Row 3: Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Analyser Manuellement */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => navigate('/analyse')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/analyse')}
          className="h-56 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200 active:scale-[0.98]"
        >
          <div className="text-4xl">📄</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Analyser<br />Manuellement
            </h3>
            <p className="text-sm text-white/80">
              (CSV/ASINs)
            </p>
          </div>
        </div>

        {/* Card 2: Decouvrir */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => navigate('/niche-discovery')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/niche-discovery')}
          className="h-56 bg-gradient-to-br from-purple-500 to-purple-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200 active:scale-[0.98]"
        >
          <div className="text-4xl">🔍</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Decouvrir
            </h3>
            <p className="text-sm text-white/80">
              Nouvelles Niches
            </p>
          </div>
        </div>

        {/* Card 3: Mes Niches */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => navigate('/mes-niches')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/mes-niches')}
          className="h-56 bg-gradient-to-br from-green-500 to-green-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200 active:scale-[0.98]"
        >
          <div className="text-4xl">📚</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Mes Niches
            </h3>
            <p className="text-sm text-white/80">
              Sauvegardees<br />
              (23)
            </p>
          </div>
        </div>
      </div>

      {/* Row 4: Footer Stats */}
      <div className="mt-12 pt-4 border-t border-gray-100 text-center">
        <div className="flex items-center justify-center gap-8 text-gray-500 text-sm py-4">
          <div>
            <span className="font-medium">AutoScheduler:</span> <span className="text-green-600 font-semibold">ACTIF</span>
          </div>
          <div className="text-gray-300">•</div>
          <div>
            <span className="font-medium">Stock validé:</span> 892 produits
          </div>
        </div>
      </div>
    </div>
  )
}