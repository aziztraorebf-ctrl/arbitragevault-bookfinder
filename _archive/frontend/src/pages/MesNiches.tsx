/**
 * Mes Niches Page
 * Display and manage saved niches with re-run and delete actions
 * Phase 5 - Niche Bookmarks Flow
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { Inbox } from 'lucide-react'
import { useBookmarks, useDeleteBookmark } from '../hooks/useBookmarks'
import { NicheListItem } from '../components/bookmarks/NicheListItem'
import { bookmarksService } from '../services/bookmarksService'
import { nicheDiscoveryService } from '../services/nicheDiscoveryService'
import type { SavedNiche } from '../types/bookmarks'

export default function MesNiches() {
  const navigate = useNavigate()
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
    try {
      setRerunningId(niche.id)

      const { filters } = await bookmarksService.getBookmarkFilters(niche.id)

      const result = await nicheDiscoveryService.discoverManual({
        ...filters,
        force_refresh: true,
      })

      navigate('/niche-discovery', {
        state: {
          rerunResults: result,
          fromNiche: niche,
          isRefresh: true,
        },
      })

      toast.success(`Analyse relancee pour "${niche.niche_name}"`)
    } catch (error: any) {
      console.error('Error re-running analysis:', error)
      toast.error(
        `Erreur: ${error.response?.data?.detail || 'Impossible de relancer'}`
      )
    } finally {
      setRerunningId(null)
    }
  }

  return (
    <div className="min-h-screen bg-vault-bg p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
            Mes Niches Sauvegardees
          </h1>
          <p className="text-vault-text-secondary text-sm md:text-base mt-2">
            Gerez vos niches decouvertes et relancez l'analyse
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full" />
            <span className="mt-4 text-vault-text-secondary">
              Chargement de vos niches...
            </span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
            <p className="text-vault-danger">
              Erreur lors du chargement:{' '}
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && (!data || data.niches.length === 0) && (
          <div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm p-12 text-center">
            <Inbox className="w-16 h-16 text-vault-text-muted mx-auto mb-4" />
            <h2 className="text-xl font-display font-semibold text-vault-text mb-2">
              Aucune niche sauvegardee
            </h2>
            <p className="text-vault-text-secondary mb-6">
              Decouvrez des niches dans la page "Niche Discovery" et
              sauvegardez-les pour y acceder rapidement.
            </p>
            <a
              href="/niche-discovery"
              className="inline-block px-6 py-3 bg-vault-accent hover:bg-vault-accent-hover text-white rounded-xl font-medium transition-colors duration-200"
            >
              Decouvrir des niches
            </a>
          </div>
        )}

        {/* Niches List */}
        {!isLoading && data && data.niches.length > 0 && (
          <div className="space-y-4">
            <div className="text-sm text-vault-text-secondary">
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
          <div className="bg-vault-accent-light border border-vault-accent/20 rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-vault-accent mb-2">
              Info: Gestion des niches
            </h3>
            <ul className="text-sm text-vault-text-secondary space-y-1">
              <li>
                - <strong>Relancer:</strong> Re-execute l'analyse avec les memes
                criteres
              </li>
              <li>
                - <strong>Supprimer:</strong> Retire la niche de vos
                favoris (irreversible)
              </li>
              <li>
                - Les scores sont mis a jour a chaque relance d'analyse
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
