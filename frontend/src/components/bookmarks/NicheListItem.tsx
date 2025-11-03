/**
 * Niche List Item Component
 * Displays a saved niche with actions (re-run, delete)
 * Phase 5 - Niche Bookmarks Flow
 */

import { RefreshCw, Trash2 } from 'lucide-react'
import type { SavedNiche } from '../../types/bookmarks'

interface NicheListItemProps {
  niche: SavedNiche
  onRerun: (niche: SavedNiche) => void
  onDelete: (nicheId: string) => void
  isRerunning: boolean
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return `Il y a ${diffMins}m`
  } else if (diffHours < 24) {
    return `Il y a ${diffHours}h`
  } else if (diffDays < 7) {
    return `Il y a ${diffDays}j`
  } else {
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }
}

export function NicheListItem({
  niche,
  onRerun,
  onDelete,
  isRerunning,
}: NicheListItemProps) {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-200 hover:border-purple-300 p-6">
      <div className="flex items-start justify-between">
        {/* Niche Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-xl font-bold text-gray-900 mb-2 truncate">
            {niche.niche_name}
          </h3>

          {niche.category_name && (
            <p className="text-sm text-gray-600 mb-1">
              Categorie: {niche.category_name}
            </p>
          )}

          {niche.description && (
            <p className="text-sm text-gray-500 mb-3 line-clamp-2">
              {niche.description}
            </p>
          )}

          <div className="flex items-center gap-4 text-sm text-gray-500">
            {niche.last_score !== undefined && (
              <div className="flex items-center gap-1">
                <span className="font-medium">Score:</span>
                <span
                  className={
                    niche.last_score >= 7
                      ? 'text-green-600 font-bold'
                      : niche.last_score >= 5
                        ? 'text-blue-600 font-bold'
                        : 'text-gray-600 font-bold'
                  }
                >
                  {niche.last_score.toFixed(1)}/10
                </span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <span className="font-medium">Cree:</span>
              <span>{formatDate(niche.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => onRerun(niche)}
            disabled={isRerunning}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg transition-colors duration-200"
            title="Relancer l'analyse"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRerunning ? 'animate-spin' : ''}`}
            />
            <span className="hidden sm:inline">
              {isRerunning ? 'Analyse...' : 'Relancer'}
            </span>
          </button>

          <button
            onClick={() => onDelete(niche.id)}
            disabled={isRerunning}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg transition-colors duration-200"
            title="Supprimer cette niche"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">Supprimer</span>
          </button>
        </div>
      </div>
    </div>
  )
}
