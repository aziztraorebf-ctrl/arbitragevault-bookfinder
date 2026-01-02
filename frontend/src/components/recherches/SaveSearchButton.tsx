/**
 * Save Search Button Component
 * Reusable button for saving search results from any module
 * Phase 11 - Centralized Search Results
 */

import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { Save, Loader2, Check } from 'lucide-react'
import { useCreateRecherche } from '../../hooks/useRecherches'
import type { SearchSource, SearchResultCreateRequest } from '../../types/recherches'
import type { DisplayableProduct } from '../../types/unified'

interface SaveSearchButtonProps {
  products: DisplayableProduct[]
  source: SearchSource
  defaultName?: string
  searchParams?: Record<string, unknown>
  disabled?: boolean
  className?: string
}

export function SaveSearchButton({
  products,
  source,
  defaultName,
  searchParams,
  disabled = false,
  className = '',
}: SaveSearchButtonProps) {
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState(defaultName || '')
  const [notes, setNotes] = useState('')
  const { mutate: createRecherche, isPending, isSuccess } = useCreateRecherche()

  const handleOpen = () => {
    // Generate default name with timestamp
    const timestamp = new Date().toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    setName(defaultName || `Recherche ${timestamp}`)
    setNotes('')
    setShowModal(true)
  }

  const handleSave = () => {
    if (!name.trim()) {
      toast.error('Le nom est requis')
      return
    }

    const request: SearchResultCreateRequest = {
      name: name.trim(),
      source,
      products,
      search_params: searchParams,
      notes: notes.trim() || undefined,
    }

    createRecherche(request, {
      onSuccess: () => {
        toast.success(`Recherche sauvegardee (${products.length} produits)`)
        setShowModal(false)
      },
      onError: (err) => {
        toast.error(`Erreur: ${err instanceof Error ? err.message : 'Erreur inconnue'}`)
      },
    })
  }

  if (products.length === 0) {
    return null
  }

  return (
    <>
      <button
        onClick={handleOpen}
        disabled={disabled || isPending}
        className={`flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${className}`}
        title="Sauvegarder cette recherche"
      >
        {isSuccess ? (
          <>
            <Check className="w-4 h-4" />
            Sauvegarde
          </>
        ) : (
          <>
            <Save className="w-4 h-4" />
            Sauvegarder ({products.length})
          </>
        )}
      </button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Sauvegarder la recherche
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Nom de la recherche"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optionnel)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Notes sur cette recherche..."
                />
              </div>

              <div className="text-sm text-gray-500">
                {products.length} produit{products.length !== 1 ? 's' : ''} seront sauvegardes.
                Les resultats seront conserves pendant 30 jours.
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                disabled={isPending}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                onClick={handleSave}
                disabled={isPending || !name.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sauvegarde...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Sauvegarder
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
