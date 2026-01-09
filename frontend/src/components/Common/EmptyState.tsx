/**
 * EmptyState - Reusable empty state component
 * Provides consistent empty state UI across the application
 */

import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Inbox, Search, Package, BookOpen, TrendingUp } from 'lucide-react'

type EmptyStateVariant = 'default' | 'search' | 'products' | 'niches' | 'results'

interface EmptyStateAction {
  label: string
  href: string
  variant?: 'primary' | 'secondary'
}

interface EmptyStateProps {
  variant?: EmptyStateVariant
  title: string
  description: string
  actions?: EmptyStateAction[]
  icon?: ReactNode
  className?: string
}

const VARIANT_ICONS: Record<EmptyStateVariant, ReactNode> = {
  default: <Inbox className="w-16 h-16" />,
  search: <Search className="w-16 h-16" />,
  products: <Package className="w-16 h-16" />,
  niches: <BookOpen className="w-16 h-16" />,
  results: <TrendingUp className="w-16 h-16" />,
}

const VARIANT_COLORS: Record<EmptyStateVariant, string> = {
  default: 'text-gray-300',
  search: 'text-blue-200',
  products: 'text-purple-200',
  niches: 'text-green-200',
  results: 'text-amber-200',
}

export function EmptyState({
  variant = 'default',
  title,
  description,
  actions = [],
  icon,
  className = '',
}: EmptyStateProps) {
  const IconComponent = icon || VARIANT_ICONS[variant]
  const iconColor = VARIANT_COLORS[variant]

  return (
    <div className={`bg-white rounded-xl shadow-md border border-gray-200 p-12 text-center ${className}`}>
      {/* Icon */}
      <div className={`mx-auto mb-6 ${iconColor}`}>
        {IconComponent}
      </div>

      {/* Title */}
      <h2 className="text-xl font-semibold text-gray-700 mb-3">
        {title}
      </h2>

      {/* Description */}
      <p className="text-gray-500 mb-8 max-w-md mx-auto">
        {description}
      </p>

      {/* Actions */}
      {actions.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3">
          {actions.map((action, index) => (
            <Link
              key={index}
              to={action.href}
              className={`px-5 py-2.5 rounded-lg font-medium transition-colors ${
                action.variant === 'secondary'
                  ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              {action.label}
            </Link>
          ))}
        </div>
      )}

      {/* Helpful tips section */}
      <div className="mt-8 pt-6 border-t border-gray-100">
        <p className="text-xs text-gray-400">
          Besoin d'aide ? Consultez le{' '}
          <Link to="/dashboard" className="text-purple-500 hover:underline">
            Dashboard
          </Link>{' '}
          pour voir les actions disponibles.
        </p>
      </div>
    </div>
  )
}

/**
 * NoResultsState - Specific empty state for "no results found" scenarios
 * Different from "empty" - this means we searched but found nothing
 */
interface NoResultsStateProps {
  searchTerm?: string
  onReset?: () => void
  suggestions?: string[]
}

export function NoResultsState({
  searchTerm,
  onReset,
  suggestions = [],
}: NoResultsStateProps) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-8 text-center">
      <Search className="w-12 h-12 text-amber-300 mx-auto mb-4" />

      <h3 className="text-lg font-semibold text-amber-800 mb-2">
        Aucun resultat trouve
      </h3>

      <p className="text-amber-700 mb-4">
        {searchTerm
          ? `Aucun produit ne correspond a "${searchTerm}".`
          : 'Aucun produit ne correspond a vos criteres.'}
      </p>

      {suggestions.length > 0 && (
        <div className="text-sm text-amber-600 mb-4">
          <p className="font-medium mb-2">Suggestions :</p>
          <ul className="list-disc list-inside text-left max-w-xs mx-auto">
            {suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      {onReset && (
        <button
          onClick={onReset}
          className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
        >
          Reinitialiser les filtres
        </button>
      )}
    </div>
  )
}
