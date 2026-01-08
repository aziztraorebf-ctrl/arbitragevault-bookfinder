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
    <div className="p-4 md:p-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className="text-xl md:text-2xl font-bold text-gray-900">Configuration</h1>
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
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 min-w-0">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domaine Amazon
            </label>
            <select
              value={domainId}
              onChange={(e) => setDomainId(Number(e.target.value))}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value={1}>US (.com)</option>
              <option value={2}>UK (.co.uk)</option>
              <option value={3}>DE (.de)</option>
              <option value={4}>FR (.fr)</option>
              <option value={6}>CA (.ca)</option>
            </select>
          </div>
          <div className="flex-1 min-w-0">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categorie
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
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
        <div className="bg-blue-50 rounded-lg p-4 mb-6 overflow-hidden">
          <h3 className="font-medium text-blue-900 mb-2">Statistiques</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 text-sm">
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

      {/* Config sections - Keys match backend DEFAULT_BUSINESS_CONFIG */}
      {config?.effective_config && (
        <div className="space-y-6">
          <ConfigSection
            title="Seuils ROI"
            sectionKey="roi"
            config={config.effective_config.roi || {}}
            fields={[
              { key: 'min_for_buy', label: 'Minimum pour achat (%)', type: 'number' },
              { key: 'target_pct_default', label: 'Cible par defaut (%)', type: 'number' },
              { key: 'excellent_threshold', label: 'Seuil excellent (%)', type: 'number' },
            ]}
            editMode={editMode}
            isSaving={updateMutation.isPending}
            onSave={(values) => handleSave('roi', values)}
          />

          <ConfigSection
            title="Score combine"
            sectionKey="combined_score"
            config={config.effective_config.combined_score || {}}
            fields={[
              { key: 'roi_weight', label: 'Poids ROI (0-1)', type: 'number' },
              { key: 'velocity_weight', label: 'Poids Velocite (0-1)', type: 'number' },
            ]}
            editMode={editMode}
            isSaving={updateMutation.isPending}
            onSave={(values) => handleSave('combined_score', values)}
          />

          <ConfigSection
            title="Frais (buffer)"
            sectionKey="fees"
            config={config.effective_config.fees || {}}
            fields={[
              { key: 'buffer_pct_default', label: 'Buffer securite (%)', type: 'number' },
            ]}
            editMode={editMode}
            isSaving={updateMutation.isPending}
            onSave={(values) => handleSave('fees', values)}
          />

          <ConfigSection
            title="Velocite"
            sectionKey="velocity"
            config={config.effective_config.velocity || {}}
            fields={[
              { key: 'fast_threshold', label: 'Seuil rapide', type: 'number' },
              { key: 'medium_threshold', label: 'Seuil moyen', type: 'number' },
              { key: 'slow_threshold', label: 'Seuil lent', type: 'number' },
            ]}
            editMode={editMode}
            isSaving={updateMutation.isPending}
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
  isSaving: boolean
  onSave: (values: Record<string, number>) => void
}

function ConfigSection({ title, sectionKey, config, fields, editMode, isSaving, onSave }: ConfigSectionProps) {
  const [values, setValues] = useState<Record<string, number>>(config)
  const [validationError, setValidationError] = useState<string | null>(null)

  // Sync local state when config changes (e.g., domain/category switch)
  useEffect(() => {
    setValues(config)
    setValidationError(null)
  }, [config])

  const handleChange = (key: string, value: string) => {
    const numValue = Number(value)
    setValues((prev) => ({ ...prev, [key]: numValue }))
    setValidationError(null)
  }

  // Validation rules per section
  const validateValues = (): string | null => {
    // All values must be >= 0
    for (const field of fields) {
      if ((values[field.key] ?? 0) < 0) {
        return `${field.label} ne peut pas etre negatif`
      }
    }

    // ROI: min_for_buy < target_pct_default < excellent_threshold
    if (sectionKey === 'roi') {
      const { min_for_buy, target_pct_default, excellent_threshold } = values
      if (min_for_buy !== undefined && target_pct_default !== undefined && min_for_buy >= target_pct_default) {
        return 'Minimum pour achat doit etre inferieur a Cible'
      }
      if (target_pct_default !== undefined && excellent_threshold !== undefined && target_pct_default >= excellent_threshold) {
        return 'Cible doit etre inferieur a Seuil excellent'
      }
    }

    // Combined score: weights must sum to 1
    if (sectionKey === 'combined_score') {
      const { roi_weight, velocity_weight } = values
      if (roi_weight !== undefined && velocity_weight !== undefined) {
        const sum = roi_weight + velocity_weight
        if (Math.abs(sum - 1.0) > 0.01) {
          return `Les poids doivent totaliser 1.0 (actuellement ${sum.toFixed(2)})`
        }
      }
    }

    // Velocity: fast > medium > slow
    if (sectionKey === 'velocity') {
      const { fast_threshold, medium_threshold, slow_threshold } = values
      if (fast_threshold !== undefined && medium_threshold !== undefined && fast_threshold < medium_threshold) {
        return 'Seuil rapide doit etre superieur au seuil moyen'
      }
      if (medium_threshold !== undefined && slow_threshold !== undefined && medium_threshold < slow_threshold) {
        return 'Seuil moyen doit etre superieur au seuil lent'
      }
    }

    return null
  }

  const handleSave = () => {
    const error = validateValues()
    if (error) {
      setValidationError(error)
      return
    }
    onSave(values)
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="mt-4">
            {validationError && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {validationError}
              </div>
            )}
            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Sauvegarde...' : 'Sauvegarder'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
