import React, { useState } from 'react'
import { ChevronRight, Upload, Settings, BarChart3, FileOutput, Play } from 'lucide-react'
import UploadSection from './UploadSection'
import CriteriaConfig from './CriteriaConfig'
import AnalysisProgress from './AnalysisProgress'
import ResultsView from './ResultsView'
import ExportActions from './ExportActions'
import type { AnalysisStep, AnalysisInput, ConfiguredAnalysis, AnalysisResults } from '../../types'

const ManualAnalysis: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<'upload' | 'criteria' | 'progress' | 'results' | 'export'>('upload')
  const [analysisData, setAnalysisData] = useState<AnalysisInput | null>(null)
  const [configuredAnalysis, setConfiguredAnalysis] = useState<ConfiguredAnalysis | null>(null)
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null)

  const steps: AnalysisStep[] = [
    { step: 'upload', title: 'Upload & Validation', completed: !!analysisData },
    { step: 'criteria', title: 'Configuration Critères', completed: !!configuredAnalysis },
    { step: 'progress', title: 'Analyse en Cours', completed: !!analysisResults },
    { step: 'results', title: 'Résultats & Vues', completed: !!analysisResults },
    { step: 'export', title: 'Export & Actions', completed: !!analysisResults },
  ]

  const handleDataUploaded = (data: AnalysisInput) => {
    setAnalysisData(data)
    setCurrentStep('criteria') // Auto-advance to criteria step
    console.log('Analysis data uploaded:', data)
  }

  const handleConfigComplete = (configured: ConfiguredAnalysis) => {
    setConfiguredAnalysis(configured)
    setCurrentStep('progress') // Auto-advance to progress step
    console.log('Configuration completed:', configured)
  }

  const handleAnalysisComplete = (results: AnalysisResults) => {
    setAnalysisResults(results)
    setCurrentStep('results') // Auto-advance to results
    console.log('Analysis completed:', results)
  }

  const handleExportReady = (results: AnalysisResults) => {
    // Results are ready for export, no state change needed
    console.log('Export ready:', results.successful.length, 'results')
  }

  const handleNewAnalysis = () => {
    // Reset all state and start over
    setAnalysisData(null)
    setConfiguredAnalysis(null)
    setAnalysisResults(null)
    setCurrentStep('upload')
    console.log('Starting new analysis')
  }

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'upload': return Upload
      case 'criteria': return Settings
      case 'progress': return Play
      case 'results': return BarChart3
      case 'export': return FileOutput
      default: return Upload
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 'upload':
        return <UploadSection onDataUploaded={handleDataUploaded} />
      case 'criteria':
        return analysisData ? (
          <CriteriaConfig 
            analysisInput={analysisData}
            onConfigComplete={handleConfigComplete}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
            <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Veuillez d'abord compléter l'étape Upload</p>
          </div>
        )
      case 'progress':
        return configuredAnalysis ? (
          <AnalysisProgress 
            configuredAnalysis={configuredAnalysis}
            onAnalysisComplete={handleAnalysisComplete}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
            <Play className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Veuillez d'abord compléter la configuration</p>
          </div>
        )
      case 'results':
        return analysisResults ? (
          <ResultsView 
            results={analysisResults}
            onExportReady={handleExportReady}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Aucun résultat disponible</p>
          </div>
        )
      case 'export':
        return analysisResults ? (
          <ExportActions 
            results={analysisResults}
            onNewAnalysis={handleNewAnalysis}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
            <FileOutput className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Aucun résultat à exporter</p>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">Analyse Manuelle</h1>
          <p className="text-sm text-gray-600 mt-1">
            Upload CSV ou saisie ASINs → Configuration → Analyse → Résultats → Export
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => {
                const Icon = getStepIcon(step.step)
                const isActive = currentStep === step.step
                const isCompleted = step.completed
                const isClickable = step.step === 'upload' || 
                                   (step.step === 'criteria' && analysisData) ||
                                   (step.step === 'results' && analysisResults) ||
                                   (step.step === 'export' && analysisResults)

                return (
                  <div key={step.step} className="flex items-center">
                    {/* Step */}
                    <div className="flex items-center">
                      <div
                        className={`
                          flex items-center justify-center w-10 h-10 rounded-full border-2 
                          transition-colors duration-200
                          ${isActive 
                            ? 'bg-blue-500 border-blue-500 text-white' 
                            : isCompleted
                            ? 'bg-green-500 border-green-500 text-white'
                            : isClickable
                            ? 'border-gray-300 text-gray-400 hover:border-blue-300 cursor-pointer'
                            : 'border-gray-200 text-gray-300'
                          }
                        `}
                        onClick={() => {
                          if (isClickable && step.step !== currentStep) {
                            setCurrentStep(step.step)
                          }
                        }}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="ml-3">
                        <p className={`text-sm font-medium ${isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'}`}>
                          {step.title}
                        </p>
                      </div>
                    </div>

                    {/* Connector */}
                    {index < steps.length - 1 && (
                      <ChevronRight className="w-5 h-5 text-gray-300 mx-4" />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Current Step Content */}
        <div className="min-h-96">
          {renderStepContent()}
        </div>

        {/* Debug Info (Development Only) */}
        {process.env.NODE_ENV === 'development' && (analysisData || configuredAnalysis || analysisResults) && (
          <div className="mt-8 p-4 bg-gray-100 rounded border text-xs">
            <strong>Debug - État actuel:</strong>
            <div className="mt-2 space-y-2">
              {analysisData && (
                <div>
                  <strong>Step 1 - Upload Data:</strong>
                  <pre className="overflow-x-auto bg-white p-2 rounded mt-1">
                    {JSON.stringify({ asins: analysisData.asins.length, source: analysisData.source }, null, 2)}
                  </pre>
                </div>
              )}
              {configuredAnalysis && (
                <div>
                  <strong>Step 2 - Configuration:</strong>
                  <pre className="overflow-x-auto bg-white p-2 rounded mt-1">
                    {JSON.stringify({ 
                      strategy: configuredAnalysis.strategy.name,
                      criteria: configuredAnalysis.strategy.criteria,
                      customMode: configuredAnalysis.strategy.id === 'custom'
                    }, null, 2)}
                  </pre>
                </div>
              )}
              {analysisResults && (
                <div>
                  <strong>Step 3+ - Analysis Results:</strong>
                  <pre className="overflow-x-auto bg-white p-2 rounded mt-1">
                    {JSON.stringify({ 
                      successful: analysisResults.successful.length,
                      failed: analysisResults.failed.length,
                      batch_id: analysisResults.batchInfo.batch_id,
                      processing_time: analysisResults.batchInfo.processing_time
                    }, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ManualAnalysis