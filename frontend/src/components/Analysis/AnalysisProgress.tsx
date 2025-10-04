import React, { useState, useEffect } from 'react'
import { Play, Clock, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { runAnalysis, type IngestResponse } from '../../services/api'
import type { ConfiguredAnalysis, AnalysisProgress, AnalysisResults } from '../../types'

interface AnalysisProgressProps {
  configuredAnalysis: ConfiguredAnalysis
  onAnalysisComplete: (results: AnalysisResults) => void
}

const AnalysisProgressComponent: React.FC<AnalysisProgressProps> = ({
  configuredAnalysis,
  onAnalysisComplete
}) => {
  const [progress, setProgress] = useState<AnalysisProgress>({
    status: 'idle',
    processed: 0,
    total: configuredAnalysis.asins.length,
    percentage: 0,
    successful: 0,
    failed: 0
  })

  const [currentASINs, setCurrentASINs] = useState<Record<string, 'pending' | 'processing' | 'completed' | 'failed'>>(
    Object.fromEntries(configuredAnalysis.asins.map(asin => [asin, 'pending']))
  )

  const [startTime, setStartTime] = useState<Date | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const [isStarted, setIsStarted] = useState(false)

  // Start analysis when component mounts
  useEffect(() => {
    if (!isStarted) {
      setIsStarted(true)
      startAnalysis()
    }
  }, [isStarted])

  const startAnalysis = async () => {
    let progressSimulation: NodeJS.Timeout | undefined
    try {
      setProgress(prev => ({ ...prev, status: 'running', startTime: new Date() }))
      setStartTime(new Date())
      setError(null)

      // Simulate progress during API call (since it's synchronous)
      progressSimulation = setInterval(() => {
        setProgress(prev => {
          if (prev.status === 'running') {
            const newProcessed = Math.min(prev.processed + 1, prev.total - 1)
            return {
              ...prev,
              processed: newProcessed,
              percentage: Math.round((newProcessed / prev.total) * 100)
            }
          }
          return prev
        })
      }, 200) // Update every 200ms for smooth progress

      console.log('Starting analysis with:', configuredAnalysis)

      // Make actual API call - extract ASINs from configured analysis
      const response: IngestResponse = await runAnalysis(configuredAnalysis.asins, 'default')
      
      clearInterval(progressSimulation)

      // ✅ PATTERN Context7: Mapping explicite Backend → Frontend avec defensive checks
      // IngestResponse → AnalysisResults transformation
      
      // Defensive check: Vérifier que results existe et est un array
      if (!response || !Array.isArray(response.results)) {
        throw new Error('Invalid API response: missing or invalid results array')
      }

      // Filter successful avec defensive checks - Pattern safeParse Zod appliqué au runtime
      const successfulResults = response.results
        .filter(r => {
          // Defensive: vérifier que l'objet existe et a les propriétés attendues
          return r && r.status === 'success' && r.analysis != null
        })
        .map(r => r.analysis!) // Safe car déjà filtré

      // Filter failed avec defensive checks
      const failedResults = response.results
        .filter(r => r && r.status !== 'success')

      // Update final progress
      setProgress({
        status: response.successful === response.total_items ? 'completed' : 'partial',
        processed: response.processed,
        total: response.total_items,
        percentage: 100,
        successful: response.successful,
        failed: response.failed,
        startTime,
        endTime: new Date()
      })

      // Update ASIN statuses - Defensive check sur chaque result
      const finalASINStates: Record<string, 'completed' | 'failed'> = {}
      response.results.forEach(result => {
        // ✅ Defensive: vérifier que result et identifier existent
        if (result && result.identifier) {
          finalASINStates[result.identifier] = result.status === 'success' ? 'completed' : 'failed'
        }
      })
      setCurrentASINs(prev => ({ ...prev, ...finalASINStates }))

      // ✅ Mapping final avec defensive checks sur toutes propriétés - Pattern Nullish Coalescing
      const analysisResults: AnalysisResults = {
        successful: successfulResults,
        failed: failedResults,
        batchInfo: {
          batch_id: response.batch_id ?? 'unknown_batch', // Fallback si undefined/null
          trace_id: response.trace_id ?? 'unknown_trace',
          total_items: response.total_items ?? response.results.length,
          processing_time: startTime ? (new Date().getTime() - startTime.getTime()) / 1000 : undefined
        }
      }

      // Auto-advance to results after brief delay
      setTimeout(() => {
        onAnalysisComplete(analysisResults)
      }, 2000)

    } catch (err) {
      if (progressSimulation) clearInterval(progressSimulation)
      
      // Message d'erreur amélioré selon le type d'erreur
      let errorMessage = 'Erreur lors de l\'analyse'
      if (err instanceof Error) {
        errorMessage = err.message
        
        // Message spécifique pour timeout
        if (err.message.includes('timeout') || err.message.includes('temps')) {
          errorMessage = `Analyse trop longue (${configuredAnalysis.asins.length} produits). L'analyse continue côté serveur, mais l'affichage a expiré. Vérifiez la page Batches dans quelques minutes.`
        }
      }
      
      setError(errorMessage)
      setProgress(prev => ({ 
        ...prev, 
        status: 'error',
        endTime: new Date()
      }))
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'partial': return <AlertCircle className="w-5 h-5 text-yellow-600" />
      case 'error': return <XCircle className="w-5 h-5 text-red-600" />
      default: return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusMessage = () => {
    switch (progress.status) {
      case 'running': return 'Analyse en cours...'
      case 'completed': return 'Analyse terminée avec succès'
      case 'partial': return `Analyse terminée avec ${progress.failed} échec(s)`
      case 'error': return 'Erreur lors de l\'analyse'
      default: return 'Préparation...'
    }
  }

  const getASINStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-gray-400" />
      case 'processing': return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
    }
  }

  const formatElapsedTime = () => {
    if (!startTime) return '0s'
    const endTime = progress.endTime || new Date()
    const elapsed = Math.floor((endTime.getTime() - startTime.getTime()) / 1000)
    return elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`
  }

  return (
    <div className="space-y-6">
      {/* Header with Strategy Info */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
            <Play className="w-5 h-5 mr-2" />
            3. Analyse en Cours
          </h2>
          <p className="text-sm text-gray-600">
            Stratégie: <strong>{configuredAnalysis.strategy.name}</strong> 
            • ROI min: {configuredAnalysis.strategy.criteria.roiMin}%
            • ASINs: {configuredAnalysis.asins.length}
          </p>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              {getStatusIcon(progress.status)}
              <h3 className="text-md font-medium text-gray-900 ml-2">
                {getStatusMessage()}
              </h3>
            </div>
            <div className="text-sm text-gray-500">
              {formatElapsedTime()}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{progress.processed}/{progress.total} ASINs traités</span>
              <span>{progress.percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-600">{progress.successful}</div>
              <div className="text-sm text-green-700">Réussies</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-xl font-bold text-red-600">{progress.failed}</div>
              <div className="text-sm text-red-700">Échouées</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600">{progress.total - progress.processed}</div>
              <div className="text-sm text-blue-700">Restantes</div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700 font-medium">Erreur d'analyse</span>
              </div>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          )}
        </div>
      </div>

      {/* ASIN Status List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h3 className="text-md font-medium text-gray-900 mb-4">
            Détail par ASIN ({configuredAnalysis.asins.length})
          </h3>
          
          <div className="max-h-64 overflow-y-auto">
            <div className="space-y-2">
              {configuredAnalysis.asins.map((asin) => (
                <div key={asin} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center">
                    {getASINStatusIcon(currentASINs[asin])}
                    <span className="ml-2 font-mono text-sm">{asin}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded capitalize ${
                    currentASINs[asin] === 'completed' ? 'bg-green-100 text-green-700' :
                    currentASINs[asin] === 'failed' ? 'bg-red-100 text-red-700' :
                    currentASINs[asin] === 'processing' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {currentASINs[asin] === 'pending' ? 'En attente' :
                     currentASINs[asin] === 'processing' ? 'En cours' :
                     currentASINs[asin] === 'completed' ? 'Complété' : 'Échec'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Debug Info */}
      {import.meta.env.MODE === 'development' && (
        <div className="p-4 bg-gray-100 rounded border text-xs">
          <strong>Debug - Analysis Progress:</strong>
          <pre className="mt-2 overflow-x-auto">
            {JSON.stringify({ progress, error, elapsed: formatElapsedTime() }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default AnalysisProgressComponent