import React, { useState, useEffect } from 'react'
import { TrendingUp, Target, DollarSign, BarChart3, Settings, CheckCircle } from 'lucide-react'
import ConditionFilter from './ConditionFilter'
import type { AnalysisStrategy, AnalysisCriteria, ConfiguredAnalysis, AnalysisInput } from '../../types'

interface CriteriaConfigProps {
  analysisInput: AnalysisInput
  onConfigComplete: (configuredAnalysis: ConfiguredAnalysis) => void
}

const CriteriaConfig: React.FC<CriteriaConfigProps> = ({ analysisInput, onConfigComplete }) => {
  // Stratégies prédéfinies selon les spécifications
  const predefinedStrategies: AnalysisStrategy[] = [
    {
      id: 'velocity',
      name: 'Velocity',
      description: 'Rotation rapide, ROI modéré',
      criteria: { roiMin: 20, bsrMax: 250000, minSalesPerMonth: 10 },
      color: 'blue',
      icon: 'TrendingUp'
    },
    {
      id: 'balanced',
      name: 'Balanced',
      description: 'Équilibre rentabilité/risque',
      criteria: { roiMin: 30, bsrMax: 250000, minSalesPerMonth: 5 },
      color: 'green',
      icon: 'Target'
    },
    {
      id: 'profit-hunter',
      name: 'Profit Hunter',
      description: 'Maximise profit, accepte + de risque',
      criteria: { roiMin: 40, bsrMax: 500000, minSalesPerMonth: 3 },
      color: 'purple',
      icon: 'DollarSign'
    }
  ]

  const [selectedStrategy, setSelectedStrategy] = useState<AnalysisStrategy>(predefinedStrategies[1]) // Balanced par défaut
  const [customCriteria, setCustomCriteria] = useState<AnalysisCriteria>(predefinedStrategies[1].criteria)
  const [isCustomMode, setIsCustomMode] = useState(false)
  // Default: exclude 'acceptable' (only show new, very_good, good)
  const [conditionFilter, setConditionFilter] = useState<string[]>(['new', 'very_good', 'good'])

  // Synchroniser custom criteria avec stratégie sélectionnée
  useEffect(() => {
    if (!isCustomMode) {
      setCustomCriteria(selectedStrategy.criteria)
    }
  }, [selectedStrategy, isCustomMode])

  const handleStrategySelect = (strategy: AnalysisStrategy) => {
    setSelectedStrategy(strategy)
    setCustomCriteria(strategy.criteria)
    setIsCustomMode(false)
  }

  const handleCriteriaChange = (field: keyof AnalysisCriteria, value: number) => {
    const newCriteria = { ...customCriteria, [field]: value }
    setCustomCriteria(newCriteria)
    
    // Passer en mode custom si les valeurs diffèrent de la stratégie
    const isDifferentFromStrategy = JSON.stringify(newCriteria) !== JSON.stringify(selectedStrategy.criteria)
    setIsCustomMode(isDifferentFromStrategy)
  }

  const handleSubmit = () => {
    const finalStrategy: AnalysisStrategy = isCustomMode ? {
      id: 'custom',
      name: 'Configuration Personnalisée',
      description: 'Critères ajustés manuellement',
      criteria: customCriteria,
      color: 'gray',
      icon: 'Settings'
    } : selectedStrategy

    const configuredAnalysis: ConfiguredAnalysis = {
      asins: analysisInput.asins,
      source: analysisInput.source,
      csvData: analysisInput.csvData,
      strategy: finalStrategy,
      customCriteria: isCustomMode ? customCriteria : undefined,
      conditionFilter: conditionFilter,
    }

    onConfigComplete(configuredAnalysis)
  }

  const getStrategyIcon = (iconName: string) => {
    switch (iconName) {
      case 'TrendingUp': return TrendingUp
      case 'Target': return Target
      case 'DollarSign': return DollarSign
      case 'Settings': return Settings
      default: return BarChart3
    }
  }

  const getStrategyColorClasses = (color: string, isSelected: boolean) => {
    const baseClasses = "border-2 transition-all duration-200"
    
    if (isSelected) {
      switch (color) {
        case 'blue': return `${baseClasses} border-blue-500 bg-blue-50 text-blue-700`
        case 'green': return `${baseClasses} border-green-500 bg-green-50 text-green-700`
        case 'purple': return `${baseClasses} border-purple-500 bg-purple-50 text-purple-700`
        case 'gray': return `${baseClasses} border-gray-500 bg-gray-50 text-gray-700`
        default: return `${baseClasses} border-blue-500 bg-blue-50 text-blue-700`
      }
    } else {
      return `${baseClasses} border-gray-200 hover:border-gray-300 text-gray-600 hover:bg-gray-50`
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(0)}k`
    return num.toString()
  }

  return (
    <div className="space-y-6">
      {/* Header avec info input */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">2. Configuration des Critères d'Analyse</h2>
          <p className="text-sm text-gray-600">
            {analysisInput.asins.length} ASINs prêts → Choisissez votre stratégie d'analyse
          </p>
        </div>
      </div>

      {/* Sélection Stratégies Prédéfinies */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h3 className="text-md font-medium text-gray-900 mb-4">Stratégies Prédéfinies</h3>
          
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {predefinedStrategies.map((strategy) => {
              const Icon = getStrategyIcon(strategy.icon)
              const isSelected = selectedStrategy.id === strategy.id && !isCustomMode
              
              return (
                <button
                  key={strategy.id}
                  onClick={() => handleStrategySelect(strategy)}
                  className={`
                    p-4 rounded-lg text-left
                    ${getStrategyColorClasses(strategy.color, isSelected)}
                  `}
                >
                  <div className="flex items-center mb-2">
                    <Icon className="w-5 h-5 mr-2" />
                    <span className="font-medium">{strategy.name}</span>
                  </div>
                  <p className="text-sm opacity-75 mb-3">{strategy.description}</p>
                  
                  <div className="text-xs space-y-1">
                    <div>ROI min: {strategy.criteria.roiMin}%</div>
                    <div>BSR max: {formatNumber(strategy.criteria.bsrMax)}</div>
                    <div>Ventes/mois: {strategy.criteria.minSalesPerMonth}+</div>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Custom Strategy Indicator */}
          {isCustomMode && (
            <div className={`
              p-4 rounded-lg border-2 border-gray-500 bg-gray-50 text-gray-700
            `}>
              <div className="flex items-center mb-2">
                <Settings className="w-5 h-5 mr-2" />
                <span className="font-medium">Configuration Personnalisée</span>
                <span className="ml-2 text-xs bg-gray-200 px-2 py-1 rounded">ACTIF</span>
              </div>
              <p className="text-sm opacity-75">Critères ajustés manuellement</p>
            </div>
          )}
        </div>
      </div>

      {/* Ajustements Manuels */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h3 className="text-md font-medium text-gray-900 mb-4">Ajustements Manuels</h3>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* ROI Min */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ROI Minimum (%)
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={customCriteria.roiMin}
                  onChange={(e) => handleCriteriaChange('roiMin', parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>10%</span>
                  <span className="font-medium text-gray-700">{customCriteria.roiMin}%</span>
                  <span>100%</span>
                </div>
              </div>
              
              <input
                type="number"
                min="10"
                max="100"
                value={customCriteria.roiMin}
                onChange={(e) => handleCriteriaChange('roiMin', parseInt(e.target.value) || 20)}
                className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="ROI %"
              />
            </div>

            {/* BSR Max */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                BSR Maximum
              </label>
              <input
                type="number"
                min="1000"
                max="2000000"
                step="1000"
                value={customCriteria.bsrMax}
                onChange={(e) => handleCriteriaChange('bsrMax', parseInt(e.target.value) || 250000)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="ex: 250000"
              />
              <p className="text-xs text-gray-500 mt-1">
                Format: {formatNumber(customCriteria.bsrMax)} (plus bas = meilleure vente)
              </p>
            </div>

            {/* Min Sales Per Month */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ventes/mois minimum
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={customCriteria.minSalesPerMonth}
                onChange={(e) => handleCriteriaChange('minSalesPerMonth', parseInt(e.target.value) || 5)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="ex: 10"
              />
              <p className="text-xs text-gray-500 mt-1">
                Estimation ventes mensuelles minimum
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filtre par Condition */}
      <ConditionFilter
        selectedConditions={conditionFilter}
        onChange={setConditionFilter}
      />

      {/* Resume Configuration */}
      <div className="bg-blue-50 rounded-lg border border-blue-200">
        <div className="p-6">
          <h3 className="text-md font-medium text-blue-900 mb-3 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Configuration Finale
          </h3>

          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-blue-700 mb-2">
                <strong>Stratégie:</strong> {isCustomMode ? 'Configuration Personnalisée' : selectedStrategy.name}
              </p>
              <p className="text-blue-600">
                <strong>ASINs à analyser:</strong> {analysisInput.asins.length}
              </p>
            </div>
            
            <div className="space-y-1 text-blue-700">
              <p><strong>ROI min:</strong> {customCriteria.roiMin}%</p>
              <p><strong>BSR max:</strong> {formatNumber(customCriteria.bsrMax)}</p>
              <p><strong>Ventes min:</strong> {customCriteria.minSalesPerMonth}/mois</p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center"
        >
          <BarChart3 className="w-5 h-5 mr-2" />
          Lancer l'Analyse ({analysisInput.asins.length} ASINs)
        </button>
      </div>

      {/* Debug Info (Development Only) */}
      {import.meta.env.MODE === 'development' && (
        <div className="mt-6 p-4 bg-gray-100 rounded border text-xs">
          <strong>Debug - Configuration:</strong>
          <pre className="mt-2 overflow-x-auto">
            Strategy: {selectedStrategy.name} {isCustomMode && '(CUSTOM)'}
            {JSON.stringify({ customCriteria, isCustomMode }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default CriteriaConfig