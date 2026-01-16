import React, { useState } from 'react'
import { FileOutput, Download, Package, RefreshCw, CheckCircle } from 'lucide-react'
import type { AnalysisResults, AnalysisAPIResult } from '../../types'

// Helper: Get best ROI from all conditions
const getBestRoi = (pricing: AnalysisAPIResult['pricing']): number | null => {
  if (!pricing) return null
  const conditions = ['new', 'very_good', 'good', 'acceptable'] as const
  let bestRoi: number | null = null
  for (const condition of conditions) {
    const detail = pricing[condition]
    if (detail?.roi_percentage !== null && detail?.roi_percentage !== undefined) {
      if (bestRoi === null || detail.roi_percentage > bestRoi) {
        bestRoi = detail.roi_percentage
      }
    }
  }
  return bestRoi
}

interface ExportActionsProps {
  results: AnalysisResults
  onNewAnalysis: () => void
}

const ExportActions: React.FC<ExportActionsProps> = ({ results, onNewAnalysis }) => {
  const [isExporting, setIsExporting] = useState(false)
  const [exportSuccess, setExportSuccess] = useState(false)

  const exportToCSV = async () => {
    if (results.successful.length === 0) {
      alert('Aucun résultat à exporter')
      return
    }

    setIsExporting(true)

    try {
      // Preparer les donnees CSV
      const headers = [
        'ASIN',
        'Title',
        'BSR',
        'Amazon_Present',
        'Price_New',
        'Price_VeryGood',
        'Price_Good',
        'Best_ROI',
        'Velocity_Score',
        'Velocity_Category',
        'Overall_Rating',
        'Recommendation',
        'Risk_Factors',
        'Readable_Summary'
      ]

      const csvRows = [
        headers.join(','),
        ...results.successful.map(result => {
          const bestRoi = getBestRoi(result?.pricing)
          return [
            result.asin,
            `"${(result.title || '').replace(/"/g, '""')}"`,
            result.current_bsr ?? '',
            result.amazon_on_listing ? 'TRUE' : 'FALSE',
            result.pricing?.new?.current_price ?? '',
            result.pricing?.very_good?.current_price ?? '',
            result.pricing?.good?.current_price ?? '',
            bestRoi ?? '',
            result.velocity?.velocity_score ?? '',
            result.velocity?.velocity_category ?? result.velocity?.velocity_tier ?? '',
            result.overall_rating,
            result.recommendation,
            `"${result.risk_factors?.join('; ') ?? ''}"`,
            `"${(result.readable_summary || '').replace(/"/g, '""')}"`
          ].join(',')
        })
      ]

      // Créer et télécharger le fichier
      const csvContent = csvRows.join('\n')
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      
      // Nom de fichier avec timestamp
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-')
      const filename = `analysis_results_${timestamp}.csv`
      
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()

      setExportSuccess(true)
      setTimeout(() => setExportSuccess(false), 3000)

    } catch (error) {
      console.error('Erreur lors de l\'export:', error)
      alert('Erreur lors de l\'export CSV')
    } finally {
      setIsExporting(false)
    }
  }

  const getProfitableCount = () => {
    const successful = Array.isArray(results.successful) ? results.successful : [];
    return successful.filter(r => {
      const bestRoi = getBestRoi(r?.pricing)
      return bestRoi !== null && bestRoi >= 20
    }).length
  }

  const getExcellentCount = () => {
    const successful = Array.isArray(results.successful) ? results.successful : [];
    return successful.filter(r => r.overall_rating === 'EXCELLENT').length
  }

  const getAverageROI = () => {
    const successful = Array.isArray(results.successful) ? results.successful : [];
    if (successful.length === 0) return '0'
    const rois = successful.map(r => getBestRoi(r?.pricing)).filter((roi): roi is number => roi !== null)
    if (rois.length === 0) return '0'
    const total = rois.reduce((sum, roi) => sum + roi, 0)
    return (total / rois.length).toFixed(1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
            <FileOutput className="w-5 h-5 mr-2" />
            5. Export & Actions
          </h2>
          <p className="text-sm text-gray-600">
            Exportez vos résultats ou lancez de nouvelles actions sur les produits rentables
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <div className="text-2xl font-bold text-green-600">{getProfitableCount()}</div>
              <div className="text-sm text-gray-600">Produits rentables</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Package className="w-8 h-8 text-blue-500 mr-3" />
            <div>
              <div className="text-2xl font-bold text-blue-600">{getExcellentCount()}</div>
              <div className="text-sm text-gray-600">Opportunités excellentes</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <RefreshCw className="w-8 h-8 text-purple-500 mr-3" />
            <div>
              <div className="text-2xl font-bold text-purple-600">{getAverageROI()}%</div>
              <div className="text-sm text-gray-600">ROI moyen</div>
            </div>
          </div>
        </div>
      </div>

      {/* Export Actions */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h3 className="font-medium text-gray-900 mb-4">Actions disponibles</h3>
          
          <div className="space-y-4">
            {/* Export CSV */}
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border">
              <div className="flex items-center">
                <Download className="w-6 h-6 text-blue-600 mr-3" />
                <div>
                  <h4 className="font-medium text-blue-900">Export CSV</h4>
                  <p className="text-sm text-blue-700">
                    Téléchargez tous les résultats ({results.successful.length} lignes) au format CSV
                  </p>
                </div>
              </div>
              <button
                onClick={exportToCSV}
                disabled={isExporting || results.successful.length === 0}
                className={`
                  px-4 py-2 rounded-lg font-medium transition-colors flex items-center
                  ${exportSuccess 
                    ? 'bg-green-600 text-white' 
                    : isExporting 
                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                    : results.successful.length > 0
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }
                `}
              >
                {exportSuccess ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Exporté !
                  </>
                ) : isExporting ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                    Export...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-1" />
                    Exporter
                  </>
                )}
              </button>
            </div>

            {/* Stock Estimates Placeholder */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-dashed">
              <div className="flex items-center">
                <Package className="w-6 h-6 text-gray-400 mr-3" />
                <div>
                  <h4 className="font-medium text-gray-600">Vérification Stock</h4>
                  <p className="text-sm text-gray-500">
                    Vérifiez la disponibilité des {getProfitableCount()} produits rentables
                  </p>
                </div>
              </div>
              <button
                disabled
                className="px-4 py-2 rounded-lg font-medium bg-gray-200 text-gray-500 cursor-not-allowed"
              >
                Bientôt disponible
              </button>
            </div>

            {/* New Analysis */}
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border">
              <div className="flex items-center">
                <RefreshCw className="w-6 h-6 text-green-600 mr-3" />
                <div>
                  <h4 className="font-medium text-green-900">Nouvelle Analyse</h4>
                  <p className="text-sm text-green-700">
                    Recommencer le processus avec de nouveaux ASINs ou critères
                  </p>
                </div>
              </div>
              <button
                onClick={onNewAnalysis}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                Nouvelle Analyse
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Batch Information */}
      <div className="bg-gray-50 rounded-lg border p-6">
        <h3 className="font-medium text-gray-900 mb-3">Informations de l'analyse</h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div><strong>Batch ID:</strong> <code className="bg-white px-1 rounded">{results.batchInfo.batch_id}</code></div>
          <div><strong>Trace ID:</strong> <code className="bg-white px-1 rounded">{results.batchInfo.trace_id}</code></div>
          <div><strong>Total traité:</strong> {results.batchInfo.total_items} ASINs</div>
          <div><strong>Temps de traitement:</strong> {results.batchInfo.processing_time?.toFixed(1)}s</div>
        </div>
      </div>

      {/* Debug Info */}
      {import.meta.env.MODE === 'development' && (
        <div className="p-4 bg-gray-100 rounded border text-xs">
          <strong>Debug - Export Actions:</strong>
          <pre className="mt-2 overflow-x-auto">
            {JSON.stringify({
              successful_results: results.successful.length,
              profitable_count: getProfitableCount(),
              excellent_count: getExcellentCount(),
              average_roi: getAverageROI(),
              export_ready: results.successful.length > 0
            }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default ExportActions