import { useState, useEffect } from 'react'
import { useEffectiveConfig, useConfigStats, useUpdateConfig } from '../hooks/useConfig'
import toast from 'react-hot-toast'

export default function Configuration() {
  const [domainId, setDomainId] = useState(1)
  const [category, setCategory] = useState('books')
  const [editMode, setEditMode] = useState(false)

  const { data: config, isLoading, error } = useEffectiveConfig(domainId, category)
  const { data: stats } = useConfigStats()
  const updateMutation = useUpdateConfig()

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-red-800 font-semibold">Erreur de chargement</h2>
          <p className="text-red-600 text-sm mt-1">
            Impossible de charger la configuration: {(error as Error).message}
          </p>
        </div>
      </div>
    )
  }

  const handleSave = async (sectionKey: string, newValues: Record<string, number>) => {
    try {
      await updateMutation.mutateAsync({
        scope: 'global',
        request: { config: { [sectionKey]: newValues }, description: 'Update from UI' }
      })
      toast.success('Configuration sauvegardee')
      setEditMode(false)
    } catch {
      toast.error('Erreur lors de la sauvegarde')
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
        <button
          onClick={() => setEditMode(!editMode)}
          className={`px-4 py-2 rounded-lg font-medium ${
            editMode
              ? 'bg-gray-200 text-gray-700'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {editMode ? 'Annuler' : 'Modifier'}
        </button>
      </div>

      {/* Domain/Category selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domaine Amazon
            </label>
            <select
              value={domainId}
              onChange={(e) => setDomainId(Number(e.target.value))}
              className="border rounded-lg px-3 py-2"
            >
              <option value={1}>US (.com)</option>
              <option value={2}>UK (.co.uk)</option>
              <option value={3}>DE (.de)</option>
              <option value={4}>FR (.fr)</option>
              <option value={6}>CA (.ca)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categorie
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="border rounded-lg px-3 py-2"
            >
              <option value="books">Livres</option>
              <option value="electronics">Electronique</option>
              <option value="toys">Jouets</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats card */}
      {stats && (
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-blue-900 mb-2">Statistiques</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-blue-600">Configs totales:</span>{' '}
              <span className="font-semibold">{stats.total_configs}</span>
            </div>
            <div>
              <span className="text-blue-600">Cache:</span>{' '}
              <span className="font-semibold">{stats.cache_status}</span>
            </div>
            <div>
              <span className="text-blue-600">Derniere MAJ:</span>{' '}
              <span className="font-semibold">
                {stats.last_updated ? new Date(stats.last_updated).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Config sections */}
      {config?.effective_config && (
        <div className="space-y-6">
          <ConfigSection
            title="Seuils ROI"
            sectionKey="roi_thresholds"
            config={config.effective_config.roi_thresholds || {}}
            fields={[
              { key: 'minimum', label: 'Minimum (%)', type: 'number' },
              { key: 'target', label: 'Cible (%)', type: 'number' },
              { key: 'excellent', label: 'Excellent (%)', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('roi_thresholds', values)}
          />

          <ConfigSection
            title="Limites BSR"
            sectionKey="bsr_limits"
            config={config.effective_config.bsr_limits || {}}
            fields={[
              { key: 'max_acceptable', label: 'Max acceptable', type: 'number' },
              { key: 'ideal_max', label: 'Ideal max', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('bsr_limits', values)}
          />

          <ConfigSection
            title="Tarification"
            sectionKey="pricing"
            config={config.effective_config.pricing || {}}
            fields={[
              { key: 'min_profit_margin', label: 'Marge min (%)', type: 'number' },
              { key: 'fee_estimate_percent', label: 'Estimation frais (%)', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('pricing', values)}
          />

          <ConfigSection
            title="Velocite"
            sectionKey="velocity"
            config={config.effective_config.velocity || {}}
            fields={[
              { key: 'min_score', label: 'Score minimum', type: 'number' },
              { key: 'weight_in_scoring', label: 'Poids scoring', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('velocity', values)}
          />
        </div>
      )}
    </div>
  )
}

// Config section component
interface ConfigSectionProps {
  title: string
  sectionKey: string
  config: Record<string, number>
  fields: Array<{ key: string; label: string; type: string }>
  editMode: boolean
  onSave: (values: Record<string, number>) => void
}

function ConfigSection({ title, config, fields, editMode, onSave }: ConfigSectionProps) {
  const [values, setValues] = useState<Record<string, number>>(config)

  // Sync local state when config changes (e.g., domain/category switch)
  useEffect(() => {
    setValues(config)
  }, [config])

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: Number(value) }))
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {fields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm text-gray-600 mb-1">{field.label}</label>
              {editMode ? (
                <input
                  type={field.type}
                  value={values[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              ) : (
                <div className="text-lg font-semibold text-gray-900">
                  {config[field.key]?.toLocaleString() ?? 'N/A'}
                </div>
              )}
            </div>
          ))}
        </div>
        {editMode && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => onSave(values)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Sauvegarder
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
