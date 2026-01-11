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
    <div className="min-h-screen bg-vault-bg p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6 md:space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
              AutoScheduler
            </h1>
            <p className="text-vault-text-secondary mt-2">
              Planification automatique des analyses
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover font-medium transition-colors shadow-vault-sm"
          >
            Nouvelle tache
          </button>
        </div>

        {/* Feature status banner */}
        <div className="bg-vault-warning-light border border-vault-warning/20 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-vault-warning/20 flex items-center justify-center">
              <span className="text-vault-warning font-bold text-lg">!</span>
            </div>
            <div className="flex-1">
              <h3 className="text-vault-text font-display font-semibold text-lg">
                Fonctionnalite a venir - Phase 12
              </h3>
              <p className="text-vault-text-secondary mt-2">
                L'AutoScheduler sera disponible apres l'integration N8N (Phase 12).
                En attendant, utilisez{' '}
                <a href="/autosourcing" className="text-vault-accent underline font-medium hover:text-vault-accent-hover transition-colors">
                  AutoSourcing
                </a>{' '}
                pour lancer des analyses manuellement, ou{' '}
                <a href="/niche-discovery" className="text-vault-accent underline font-medium hover:text-vault-accent-hover transition-colors">
                  Niche Discovery
                </a>{' '}
                pour explorer des niches.
              </p>
              <p className="text-vault-text-muted text-sm mt-3">
                Cette interface montre les fonctionnalites prevues pour la planification automatique.
              </p>
            </div>
          </div>
        </div>

        {/* Scheduled tasks list */}
        <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border overflow-hidden">
          <div className="px-6 py-4 border-b border-vault-border">
            <h2 className="font-display font-semibold text-vault-text text-lg">
              Taches planifiees
            </h2>
          </div>
          <div className="divide-y divide-vault-border">
            {MOCK_SCHEDULES.map((schedule) => (
              <div
                key={schedule.id}
                className="p-4 md:p-6 hover:bg-vault-hover transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        schedule.status === 'active'
                          ? 'bg-vault-success'
                          : 'bg-vault-text-muted'
                      }`}
                    />
                    <div>
                      <h3 className="font-medium text-vault-text">
                        {schedule.name}
                      </h3>
                      <p className="text-sm text-vault-text-muted mt-1">
                        {FREQUENCY_LABELS[schedule.frequency]} |{' '}
                        Prochaine execution:{' '}
                        {new Date(schedule.nextRun).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 text-xs font-medium rounded-full ${
                        schedule.status === 'active'
                          ? 'bg-vault-success-light text-vault-success'
                          : 'bg-vault-hover text-vault-text-muted'
                      }`}
                    >
                      {schedule.status === 'active' ? 'Actif' : 'En pause'}
                    </span>
                    <button
                      className="p-2 text-vault-text-muted hover:text-vault-text-secondary transition-colors rounded-lg hover:bg-vault-hover"
                      disabled
                    >
                      ...
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Planned features section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6">
            <div className="w-12 h-12 rounded-xl bg-vault-accent-light flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-vault-accent"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-vault-text mb-2">
              Analyse automatique
            </h3>
            <p className="text-sm text-vault-text-secondary">
              Planifiez des scans Keepa automatiques pour surveiller vos niches favorites.
            </p>
          </div>
          <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6">
            <div className="w-12 h-12 rounded-xl bg-vault-accent-light flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-vault-accent"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-vault-text mb-2">
              Alertes prix
            </h3>
            <p className="text-sm text-vault-text-secondary">
              Recevez des notifications quand les prix ou BSR changent significativement.
            </p>
          </div>
          <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6">
            <div className="w-12 h-12 rounded-xl bg-vault-accent-light flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-vault-accent"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-vault-text mb-2">
              Rapports automatiques
            </h3>
            <p className="text-sm text-vault-text-secondary">
              Generez des rapports periodiques sur vos opportunites d'arbitrage.
            </p>
          </div>
        </div>

        {/* Create modal (concept) */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-vault-card rounded-2xl shadow-vault-lg border border-vault-border max-w-md w-full">
              <div className="px-6 py-5 border-b border-vault-border">
                <h2 className="text-xl font-display font-semibold text-vault-text">
                  Nouvelle tache planifiee
                </h2>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <label className="block text-sm font-medium text-vault-text mb-2">
                    Nom de la tache
                  </label>
                  <input
                    type="text"
                    className="w-full border border-vault-border rounded-xl px-4 py-2.5 bg-vault-bg text-vault-text placeholder:text-vault-text-muted focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent transition-colors"
                    placeholder="Ex: Scan Books US"
                    disabled
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-vault-text mb-2">
                    Frequence
                  </label>
                  <select
                    className="w-full border border-vault-border rounded-xl px-4 py-2.5 bg-vault-bg text-vault-text focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent transition-colors"
                    disabled
                  >
                    <option>Quotidien</option>
                    <option>Hebdomadaire</option>
                    <option>Mensuel</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-vault-text mb-2">
                    Type d'action
                  </label>
                  <select
                    className="w-full border border-vault-border rounded-xl px-4 py-2.5 bg-vault-bg text-vault-text focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent transition-colors"
                    disabled
                  >
                    <option>Scan Keepa</option>
                    <option>Analyse strategique</option>
                    <option>Rapport</option>
                  </select>
                </div>
                <div className="bg-vault-warning-light border border-vault-warning/20 rounded-xl p-4">
                  <p className="text-sm text-vault-text-secondary">
                    Cette fonctionnalite n'est pas encore disponible.
                  </p>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-vault-border flex justify-end gap-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-5 py-2.5 text-vault-text-secondary hover:bg-vault-hover rounded-xl font-medium transition-colors"
                >
                  Fermer
                </button>
                <button
                  className="px-5 py-2.5 bg-vault-hover text-vault-text-muted rounded-xl font-medium cursor-not-allowed"
                  disabled
                >
                  Creer (bientot)
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
