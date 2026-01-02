/**
 * Recherche Detail Page
 * Display saved search result products with UnifiedProductTable
 * Phase 11 - Centralized Search Results
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  Loader2, ArrowLeft, Calendar, Package, Edit2,
  Trash2, Save, X, Clock
} from 'lucide-react'
import { useRechercheDetail, useUpdateRecherche, useDeleteRecherche } from '../hooks/useRecherches'
import { UnifiedProductTable } from '../components/unified'
import { SOURCE_LABELS, SOURCE_COLORS } from '../types/recherches'
import type { SearchSource } from '../types/recherches'

// Source badge component
function SourceBadge({ source }: { source: SearchSource }) {
  const colorClasses: Record<string, string> = {
    purple: 'bg-purple-100 text-purple-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
  }

  const color = SOURCE_COLORS[source] || 'gray'
  const classes = colorClasses[color] || 'bg-gray-100 text-gray-800'

  return (
    <span className={`px-3 py-1 text-sm font-medium rounded-full ${classes}`}>
      {SOURCE_LABELS[source]}
    </span>
  )
}

export default function RechercheDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error } = useRechercheDetail(id || '')
  const { mutate: updateRecherche, isPending: isUpdating } = useUpdateRecherche()
  const { mutate: deleteRecherche, isPending: isDeleting } = useDeleteRecherche()

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState('')
  const [editNotes, setEditNotes] = useState('')

  const handleBack = () => {
    navigate('/recherches')
  }

  const handleStartEdit = () => {
    if (data) {
      setEditName(data.name)
      setEditNotes(data.notes || '')
      setIsEditing(true)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditName('')
    setEditNotes('')
  }

  const handleSaveEdit = () => {
    if (!id) return

    updateRecherche(
      { id, data: { name: editName, notes: editNotes || undefined } },
      {
        onSuccess: () => {
          toast.success('Recherche mise a jour')
          setIsEditing(false)
        },
        onError: (err) => {
          toast.error(
            `Erreur: ${err instanceof Error ? err.message : 'Erreur inconnue'}`
          )
        },
      }
    )
  }

  const handleDelete = () => {
    if (!id || !data) return

    if (!window.confirm(`Supprimer "${data.name}" ?`)) {
      return
    }

    deleteRecherche(id, {
      onSuccess: () => {
        toast.success('Recherche supprimee')
        navigate('/recherches')
      },
      onError: (err) => {
        toast.error(
          `Erreur: ${err instanceof Error ? err.message : 'Erreur inconnue'}`
        )
      },
    })
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            <span className="ml-3 text-gray-600">
              Chargement des resultats...
            </span>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour
          </button>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Erreur lors du chargement:{' '}
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Not found
  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour
          </button>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">Recherche non trouvee ou expiree.</p>
          </div>
        </div>
      </div>
    )
  }

  const createdDate = new Date(data.created_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  const expiresDate = new Date(data.expires_at).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Back button */}
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour a Mes Recherches
        </button>

        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nom
                    </label>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Nom de la recherche"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <textarea
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Notes optionnelles..."
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveEdit}
                      disabled={isUpdating || !editName.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                    >
                      {isUpdating ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Save className="w-4 h-4" />
                      )}
                      Enregistrer
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      disabled={isUpdating}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      <X className="w-4 h-4" />
                      Annuler
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3 mb-2">
                    <SourceBadge source={data.source} />
                    <span className="text-sm text-gray-400">ID: {data.id.slice(0, 8)}...</span>
                  </div>
                  <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
                  {data.notes && (
                    <p className="text-gray-600 mt-2">{data.notes}</p>
                  )}
                  <div className="flex items-center gap-6 mt-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Package className="w-4 h-4" />
                      {data.product_count} produit{data.product_count !== 1 ? 's' : ''}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      Cree le {createdDate}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Expire le {expiresDate}
                    </span>
                  </div>
                </>
              )}
            </div>
            {!isEditing && (
              <div className="flex items-center gap-2 ml-4">
                <button
                  onClick={handleStartEdit}
                  className="flex items-center gap-2 px-3 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  <Edit2 className="w-4 h-4" />
                  Modifier
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex items-center gap-2 px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50"
                >
                  {isDeleting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  Supprimer
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Products Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Produits ({data.product_count})
            </h2>
          </div>
          {data.products.length > 0 ? (
            <UnifiedProductTable
              products={data.products}
              title={`Produits sauvegardes (${data.product_count})`}
              features={{
                showRecommendation: true,
                showCategory: true,
                showVerifyButton: false,
                showFooterSummary: true,
                showFilters: true,
                showAccordion: false,
              }}
            />
          ) : (
            <div className="p-8 text-center text-gray-500">
              Aucun produit dans cette recherche.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
