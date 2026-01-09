import { useState } from 'react'

// Mock data for concept UI
const MOCK_SCHEDULES = [
  { id: '1', name: 'Scan Livres US', frequency: 'daily', nextRun: '2025-01-01T08:00:00Z', status: 'active' },
  { id: '2', name: 'Analyse Competition', frequency: 'weekly', nextRun: '2025-01-03T10:00:00Z', status: 'active' },
  { id: '3', name: 'Refresh Prix', frequency: 'hourly', nextRun: '2025-01-01T12:00:00Z', status: 'paused' },
]

const FREQUENCY_LABELS: Record<string, string> = {
  hourly: 'Toutes les heures',
  daily: 'Quotidien',
  weekly: 'Hebdomadaire',
  monthly: 'Mensuel',
}

export default function AutoScheduler() {
  const [showCreateModal, setShowCreateModal] = useState(false)

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AutoScheduler</h1>
          <p className="text-gray-600 mt-1">Planification automatique des analyses</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Nouvelle tache
        </button>
      </div>

      {/* Feature status banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 text-amber-500 text-xl">!</div>
          <div>
            <h3 className="text-amber-800 font-semibold">Fonctionnalite a venir - Phase 12</h3>
            <p className="text-amber-700 text-sm mt-1">
              L'AutoScheduler sera disponible apres l'integration N8N (Phase 12).
              En attendant, utilisez <a href="/autosourcing" className="underline font-medium">AutoSourcing</a> pour
              lancer des analyses manuellement, ou <a href="/niche-discovery" className="underline font-medium">Niche Discovery</a> pour
              explorer des niches.
            </p>
            <p className="text-amber-600 text-xs mt-2">
              Cette interface montre les fonctionnalites prevues pour la planification automatique.
            </p>
          </div>
        </div>
      </div>

      {/* Scheduled tasks list */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Taches planifiees</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {MOCK_SCHEDULES.map((schedule) => (
            <div key={schedule.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    schedule.status === 'active' ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <div>
                    <h3 className="font-medium text-gray-900">{schedule.name}</h3>
                    <p className="text-sm text-gray-500">
                      {FREQUENCY_LABELS[schedule.frequency]} |
                      Prochaine execution: {new Date(schedule.nextRun).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    schedule.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {schedule.status === 'active' ? 'Actif' : 'En pause'}
                  </span>
                  <button className="p-2 text-gray-400 hover:text-gray-600" disabled>
                    ...
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Planned features section */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Analyse automatique</h3>
          <p className="text-sm text-gray-600">
            Planifiez des scans Keepa automatiques pour surveiller vos niches favorites.
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Alertes prix</h3>
          <p className="text-sm text-gray-600">
            Recevez des notifications quand les prix ou BSR changent significativement.
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Rapports automatiques</h3>
          <p className="text-sm text-gray-600">
            Generez des rapports periodiques sur vos opportunites d'arbitrage.
          </p>
        </div>
      </div>

      {/* Create modal (concept) */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Nouvelle tache planifiee</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de la tache
                </label>
                <input
                  type="text"
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Ex: Scan Books US"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Frequence
                </label>
                <select className="w-full border rounded-lg px-3 py-2" disabled>
                  <option>Quotidien</option>
                  <option>Hebdomadaire</option>
                  <option>Mensuel</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type d'action
                </label>
                <select className="w-full border rounded-lg px-3 py-2" disabled>
                  <option>Scan Keepa</option>
                  <option>Analyse strategique</option>
                  <option>Rapport</option>
                </select>
              </div>
              <p className="text-sm text-amber-600 bg-amber-50 p-2 rounded">
                Cette fonctionnalite n'est pas encore disponible.
              </p>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Fermer
              </button>
              <button
                className="px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
                disabled
              >
                Creer (bientot)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
