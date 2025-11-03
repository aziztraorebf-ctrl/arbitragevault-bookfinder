/**
 * Mes Niches Page
 * Display and manage saved niches with re-run and delete actions
 * Phase 5 - Niche Bookmarks Flow
 */

import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { Loader2, Inbox } from 'lucide-react'
import { useBookmarks, useDeleteBookmark } from '../hooks/useBookmarks'
import { NicheListItem } from '../components/bookmarks/NicheListItem'
import type { SavedNiche } from '../types/bookmarks'

export default function MesNiches() {
  const { data, isLoading, error } = useBookmarks()
  const { mutate: deleteBookmark } = useDeleteBookmark()
  const [rerunningId, setRerunningId] = useState<string | null>(null)

  const handleDelete = (nicheId: string) => {
    const niche = data?.niches.find((n) => n.id === nicheId)
    if (!niche) return

    if (!window.confirm(`Supprimer la niche "${niche.niche_name}" ?`)) {
      return
    }

    deleteBookmark(nicheId, {
      onSuccess: () => {
        toast.success('Niche supprimee avec succes')
      },
      onError: (err) => {
        toast.error(
          `Erreur lors de la suppression: ${err instanceof Error ? err.message : 'Erreur inconnue'}`
        )
      },
    })
  }

  const handleRerun = async (niche: SavedNiche) => {
    setRerunningId(niche.id)

    // TODO: Task 5 - Re-run analysis implementation
    // Will fetch filters and trigger new analysis
    toast('Fonctionnalite en cours de developpement (Task 5)')

    setTimeout(() => {
      setRerunningId(null)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Mes Niches Sauvegardees
            </h1>
            <p className="text-gray-600 mt-2">
              Gerez vos niches decouvertes et relancez l'analyse
            </p>
          </div>
          <div className="text-sm text-gray-400">Phase 5</div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            <span className="ml-3 text-gray-600">
              Chargement de vos niches...
            </span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Erreur lors du chargement:{' '}
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && (!data || data.niches.length === 0) && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <Inbox className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              Aucune niche sauvegardee
            </h2>
            <p className="text-gray-500 mb-6">
              Decouvrez des niches dans la page "Niche Discovery" et
              sauvegardez-les pour y acceder rapidement.
            </p>
            <a
              href="/niche-discovery"
              className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200"
            >
              Decouvrir des niches
            </a>
          </div>
        )}

        {/* Niches List */}
        {!isLoading && data && data.niches.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              {data.total_count} niche{data.total_count > 1 ? 's' : ''}{' '}
              sauvegardee{data.total_count > 1 ? 's' : ''}
            </div>
            {data.niches.map((niche) => (
              <NicheListItem
                key={niche.id}
                niche={niche}
                onRerun={handleRerun}
                onDelete={handleDelete}
                isRerunning={rerunningId === niche.id}
              />
            ))}
          </div>
        )}

        {/* Info Footer */}
        {!isLoading && data && data.niches.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              Info: Gestion des niches
            </h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>
                • <strong>Relancer:</strong> Re-execute l'analyse avec les memes
                criteres
              </li>
              <li>
                • <strong>Supprimer:</strong> Retire la niche de vos
                favoris (irreversible)
              </li>
              <li>
                • Les scores sont mis a jour a chaque relance d'analyse
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
