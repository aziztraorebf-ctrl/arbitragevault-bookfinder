import React, { useState, useRef, useCallback } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle, Eye, X } from 'lucide-react'
import type { UploadedCSVData, ValidationResult, AnalysisInput } from '../../types'

interface UploadSectionProps {
  onDataUploaded: (data: AnalysisInput) => void
}

const UploadSection: React.FC<UploadSectionProps> = ({ onDataUploaded }) => {
  const [uploadMethod, setUploadMethod] = useState<'csv' | 'manual'>('csv')
  const [csvData, setCsvData] = useState<UploadedCSVData | null>(null)
  const [manualInput, setManualInput] = useState('')
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // ASIN Validation Regex
  const ASIN_REGEX = /^B[0-9A-Z]{9}$/

  const validateASINs = useCallback((asins: string[]): ValidationResult => {
    const validASINs: string[] = []
    const invalidASINs: string[] = []
    const errors: string[] = []

    asins.forEach(asin => {
      const cleanASIN = asin.trim().toUpperCase()
      if (cleanASIN === '') return // Skip empty lines
      
      if (ASIN_REGEX.test(cleanASIN)) {
        validASINs.push(cleanASIN)
      } else {
        invalidASINs.push(asin)
      }
    })

    // Generate error/warning messages
    if (validASINs.length === 0) {
      errors.push('Aucun ASIN valide trouvé')
    }
    if (validASINs.length > 200) {
      errors.push(`Limite dépassée: ${validASINs.length} ASINs (max 200)`)
    }
    if (invalidASINs.length > 0 && validASINs.length > 0) {
      errors.push(`${invalidASINs.length} ASIN(s) invalide(s) seront ignoré(s) - Continuer avec ${validASINs.length} ASIN(s) valide(s)`)
    }
    if (invalidASINs.length > 0 && validASINs.length === 0) {
      errors.push(`${invalidASINs.length} ASIN(s) invalide(s) détecté(s) - Aucun ASIN valide`)
    }

    return {
      isValid: validASINs.length > 0 && validASINs.length <= 200,  // Permet continuation même avec ASINs invalides
      validASINs,
      invalidASINs,
      errors
    }
  }, [])

  const parseCSV = useCallback((csvText: string, fileName: string): UploadedCSVData => {
    const lines = csvText.trim().split('\n')
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
    const rows: Record<string, string>[] = []

    // Find ASIN column
    const asinColumnIndex = headers.findIndex(header => 
      header.toLowerCase().includes('asin') || 
      header.toLowerCase() === 'id' ||
      header.toLowerCase() === 'identifier'
    )

    // Parse data rows
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''))
      const row: Record<string, string> = {}
      
      headers.forEach((header, index) => {
        row[header] = values[index] || ''
      })
      
      rows.push(row)
    }

    return {
      headers,
      rows,
      fileName,
      totalRows: rows.length,
      asinColumnIndex: asinColumnIndex >= 0 ? asinColumnIndex : undefined
    }
  }, [])

  const handleFileSelect = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Seuls les fichiers CSV sont acceptés')
      return
    }

    setIsProcessing(true)
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const csvText = e.target?.result as string
        const parsed = parseCSV(csvText, file.name)
        setCsvData(parsed)
        
        // Auto-validate ASINs from CSV
        if (parsed.asinColumnIndex !== undefined) {
          const asins = parsed.rows.map(row => row[parsed.headers[parsed.asinColumnIndex!]])
          const validation = validateASINs(asins)
          setValidationResult(validation)
        } else {
          setValidationResult({
            isValid: false,
            validASINs: [],
            invalidASINs: [],
            errors: ['Colonne ASIN non trouvée. Colonnes disponibles: ' + parsed.headers.join(', ')]
          })
        }
        
        setShowPreview(true)
      } catch (error) {
        alert('Erreur lors du parsing CSV: ' + (error as Error).message)
      } finally {
        setIsProcessing(false)
      }
    }
    
    reader.readAsText(file)
  }, [parseCSV, validateASINs])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  const handleManualInput = useCallback((value: string) => {
    setManualInput(value)
    
    if (value.trim()) {
      const asins = value.split('\n').filter(line => line.trim())
      const validation = validateASINs(asins)
      setValidationResult(validation)
    } else {
      setValidationResult(null)
    }
  }, [validateASINs])

  const handleSubmit = () => {
    if (!validationResult?.isValid) return

    const analysisInput: AnalysisInput = {
      asins: validationResult.validASINs,
      source: uploadMethod,
      csvData: uploadMethod === 'csv' ? csvData || undefined : undefined
    }

    onDataUploaded(analysisInput)
  }

  const resetUpload = () => {
    setCsvData(null)
    setManualInput('')
    setValidationResult(null)
    setShowPreview(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Method Selection */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">1. Méthode de Saisie</h2>
          
          <div className="flex space-x-4">
            <button
              onClick={() => setUploadMethod('csv')}
              className={`
                flex items-center px-4 py-3 rounded-lg border transition-colors
                ${uploadMethod === 'csv' 
                  ? 'border-blue-500 bg-blue-50 text-blue-700' 
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <FileText className="w-5 h-5 mr-2" />
              Upload CSV
            </button>
            
            <button
              onClick={() => setUploadMethod('manual')}
              className={`
                flex items-center px-4 py-3 rounded-lg border transition-colors
                ${uploadMethod === 'manual' 
                  ? 'border-blue-500 bg-blue-50 text-blue-700' 
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <Upload className="w-5 h-5 mr-2" />
              Saisie Manuelle
            </button>
          </div>
        </div>
      </div>

      {/* CSV Upload */}
      {uploadMethod === 'csv' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">2. Upload Fichier CSV</h2>
            
            {!csvData ? (
              <div
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center transition-colors
                  ${isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
                `}
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onDragEnter={() => setIsDragging(true)}
                onDragLeave={() => setIsDragging(false)}
              >
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-lg text-gray-600 mb-2">
                  Glissez votre fichier CSV ici ou cliquez pour sélectionner
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Format requis: Colonne ASIN obligatoire. Colonnes optionnelles: Title, BuyPrice, Source, Notes
                </p>
                
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Traitement...' : 'Choisir un fichier'}
                </button>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  className="hidden"
                />
              </div>
            ) : (
              /* CSV Preview */
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 text-gray-500 mr-2" />
                    <div>
                      <p className="font-medium text-gray-900">{csvData.fileName}</p>
                      <p className="text-sm text-gray-600">{csvData.totalRows} lignes, {csvData.headers.length} colonnes</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowPreview(!showPreview)}
                      className="flex items-center px-3 py-1 text-blue-600 hover:text-blue-800"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      {showPreview ? 'Masquer' : 'Aperçu'}
                    </button>
                    <button
                      onClick={resetUpload}
                      className="flex items-center px-3 py-1 text-red-600 hover:text-red-800"
                    >
                      <X className="w-4 h-4 mr-1" />
                      Supprimer
                    </button>
                  </div>
                </div>

                {showPreview && (
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h3 className="font-medium mb-2">Aperçu des données:</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr>
                            {csvData.headers.map((header, index) => (
                              <th 
                                key={index} 
                                className={`
                                  px-3 py-2 text-left font-medium
                                  ${index === csvData.asinColumnIndex 
                                    ? 'bg-blue-100 text-blue-800' 
                                    : 'bg-gray-100 text-gray-700'
                                  }
                                `}
                              >
                                {header}
                                {index === csvData.asinColumnIndex && (
                                  <span className="ml-1 text-xs">(ASIN)</span>
                                )}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {csvData.rows.slice(0, 3).map((row, index) => (
                            <tr key={index}>
                              {csvData.headers.map((header, colIndex) => (
                                <td key={colIndex} className="px-3 py-2 border-t text-gray-600">
                                  {row[header] || '-'}
                                </td>
                              ))}
                            </tr>
                          ))}
                          {csvData.rows.length > 3 && (
                            <tr>
                              <td colSpan={csvData.headers.length} className="px-3 py-2 border-t text-center text-gray-500">
                                ... et {csvData.rows.length - 3} ligne(s) de plus
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Input */}
      {uploadMethod === 'manual' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">2. Saisie Manuelle des ASINs</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Liste des ASINs (un par ligne)
                </label>
                <textarea
                  value={manualInput}
                  onChange={(e) => handleManualInput(e.target.value)}
                  placeholder={`B00FLIJJSA\nB01MXY6GEF\nB00A4DQZH4\n...\n\n(Maximum 200 ASINs)`}
                  className="w-full h-48 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {manualInput.trim() && (
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-600">
                    {manualInput.split('\n').filter(line => line.trim()).length} ASIN(s) saisi(s)
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Validation Results */}
      {validationResult && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">3. Validation</h2>
            
            <div className="space-y-3">
              {/* Summary */}
              <div className={`
                flex items-start p-4 rounded-lg
                ${validationResult.isValid 
                  ? validationResult.invalidASINs.length > 0
                    ? 'bg-yellow-50 border border-yellow-200'  // Warning: valides + invalides
                    : 'bg-green-50 border border-green-200'    // Success: tous valides
                  : 'bg-red-50 border border-red-200'          // Error: aucun valide
                }
              `}>
                {validationResult.isValid ? (
                  validationResult.invalidASINs.length > 0 ? (
                    <AlertCircle className="w-5 h-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                  )
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <p className={`font-medium ${
                    validationResult.isValid 
                      ? validationResult.invalidASINs.length > 0 
                        ? 'text-yellow-800' 
                        : 'text-green-800'
                      : 'text-red-800'
                  }`}>
                    {validationResult.isValid 
                      ? validationResult.invalidASINs.length > 0 
                        ? 'Validation avec avertissements'
                        : 'Validation réussie'
                      : 'Erreurs détectées'
                    }
                  </p>
                  <p className={`text-sm mt-1 ${
                    validationResult.isValid 
                      ? validationResult.invalidASINs.length > 0 
                        ? 'text-yellow-700' 
                        : 'text-green-700'
                      : 'text-red-700'
                  }`}>
                    {validationResult.validASINs.length} ASIN(s) valide(s)
                    {validationResult.invalidASINs.length > 0 && `, ${validationResult.invalidASINs.length} invalide(s)`}
                  </p>
                </div>
              </div>

              {/* Errors */}
              {validationResult.errors.length > 0 && (
                <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                  {validationResult.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              )}

              {/* Invalid ASINs */}
              {validationResult.invalidASINs.length > 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <p className="text-sm font-medium text-yellow-800 mb-2">ASINs invalides:</p>
                  <p className="text-xs text-yellow-700 font-mono">
                    {validationResult.invalidASINs.slice(0, 10).join(', ')}
                    {validationResult.invalidASINs.length > 10 && ` (+ ${validationResult.invalidASINs.length - 10} autres)`}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Action Button */}
      {validationResult?.isValid && (
        <div className="flex justify-between items-center">
          {validationResult.invalidASINs.length > 0 && (
            <div className="text-sm text-yellow-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {validationResult.invalidASINs.length} ASIN(s) seront ignoré(s)
            </div>
          )}
          
          <button
            onClick={handleSubmit}
            className={`
              px-6 py-3 rounded-lg font-medium transition-colors
              ${validationResult.invalidASINs.length > 0 
                ? 'bg-yellow-600 text-white hover:bg-yellow-700' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
              }
            `}
          >
            {validationResult.invalidASINs.length > 0 
              ? `Continuer malgré tout (${validationResult.validASINs.length} ASINs valides)`
              : `Continuer vers Configuration (${validationResult.validASINs.length} ASINs)`
            }
          </button>
        </div>
      )}
    </div>
  )
}

export default UploadSection