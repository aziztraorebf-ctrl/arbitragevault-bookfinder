import React from 'react'
import { Filter } from 'lucide-react'

interface ConditionFilterProps {
  selectedConditions: string[]
  onChange: (conditions: string[]) => void
}

const CONDITIONS = [
  { key: 'new', label: 'Neuf', description: 'Produits neufs' },
  { key: 'very_good', label: 'Tres Bon', description: 'Usage - Tres bon etat' },
  { key: 'good', label: 'Bon', description: 'Usage - Bon etat' },
  { key: 'acceptable', label: 'Acceptable', description: 'Usage - Etat acceptable' },
]

const ConditionFilter: React.FC<ConditionFilterProps> = ({
  selectedConditions,
  onChange,
}) => {
  const toggleCondition = (key: string) => {
    if (selectedConditions.includes(key)) {
      // Don't allow deselecting all conditions
      if (selectedConditions.length > 1) {
        onChange(selectedConditions.filter(c => c !== key))
      }
    } else {
      onChange([...selectedConditions, key])
    }
  }

  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex items-center mb-3">
        <Filter className="w-4 h-4 mr-2 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Filtrer par condition</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {CONDITIONS.map(({ key, label, description }) => (
          <button
            key={key}
            onClick={() => toggleCondition(key)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              selectedConditions.includes(key)
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={description}
          >
            {label}
          </button>
        ))}
      </div>
      <p className="mt-2 text-xs text-gray-500">
        Par defaut, les produits "Acceptable" sont exclus (qualite insuffisante pour revente)
      </p>
    </div>
  )
}

export default ConditionFilter
