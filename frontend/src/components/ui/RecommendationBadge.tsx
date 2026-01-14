/**
 * RecommendationBadge - Clear action indicator
 *
 * Design: Vault Elegance - bold, actionable badges
 * ACHETER (green), EVALUER (amber), PASSER (red)
 */

import { Check, AlertCircle, X } from 'lucide-react'

type Recommendation = 'BUY' | 'HOLD' | 'SKIP' | string

interface RecommendationBadgeProps {
  /** Recommendation from API (BUY, HOLD, SKIP) */
  recommendation: Recommendation
  /** Show icon alongside text */
  showIcon?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Show French label or original */
  useFrenchLabel?: boolean
}

interface BadgeConfig {
  label: string
  frenchLabel: string
  bg: string
  text: string
  border: string
  icon: typeof Check
}

const BADGE_CONFIG: Record<string, BadgeConfig> = {
  'BUY': {
    label: 'BUY',
    frenchLabel: 'ACHETER',
    bg: 'bg-emerald-600',
    text: 'text-white',
    border: 'border-emerald-700',
    icon: Check,
  },
  'HOLD': {
    label: 'HOLD',
    frenchLabel: 'EVALUER',
    bg: 'bg-amber-500',
    text: 'text-white',
    border: 'border-amber-600',
    icon: AlertCircle,
  },
  'SKIP': {
    label: 'SKIP',
    frenchLabel: 'PASSER',
    bg: 'bg-red-600',
    text: 'text-white',
    border: 'border-red-700',
    icon: X,
  },
}

const SIZE_STYLES = {
  sm: {
    container: 'px-2 py-0.5 text-xs gap-1',
    icon: 12,
  },
  md: {
    container: 'px-3 py-1 text-sm gap-1.5',
    icon: 14,
  },
  lg: {
    container: 'px-4 py-1.5 text-base gap-2',
    icon: 16,
  },
}

export function RecommendationBadge({
  recommendation,
  showIcon = true,
  size = 'md',
  useFrenchLabel = true,
}: RecommendationBadgeProps) {
  // Normalize to uppercase and get config
  const normalizedRec = recommendation.toUpperCase()
  const config = BADGE_CONFIG[normalizedRec] || BADGE_CONFIG['SKIP']
  const sizeStyles = SIZE_STYLES[size]
  const Icon = config.icon

  const label = useFrenchLabel ? config.frenchLabel : config.label

  return (
    <span
      className={`
        inline-flex items-center justify-center
        ${sizeStyles.container}
        ${config.bg} ${config.text}
        border ${config.border}
        rounded-full
        font-bold
        uppercase
        tracking-wide
        shadow-sm
        transition-all duration-200
        hover:shadow-md hover:scale-105
      `}
    >
      {showIcon && (
        <Icon
          style={{ width: sizeStyles.icon, height: sizeStyles.icon }}
          strokeWidth={2.5}
          aria-hidden="true"
        />
      )}
      {label}
    </span>
  )
}

/**
 * RecommendationText - Inline text version for compact displays
 */
export function RecommendationText({
  recommendation,
  useFrenchLabel = true,
}: {
  recommendation: Recommendation
  useFrenchLabel?: boolean
}) {
  const normalizedRec = recommendation.toUpperCase()
  const config = BADGE_CONFIG[normalizedRec] || BADGE_CONFIG['SKIP']
  const label = useFrenchLabel ? config.frenchLabel : config.label

  const colorClass = normalizedRec === 'BUY'
    ? 'text-emerald-600'
    : normalizedRec === 'HOLD'
      ? 'text-amber-600'
      : 'text-red-600'

  return (
    <span className={`font-semibold ${colorClass}`}>
      {label}
    </span>
  )
}

export default RecommendationBadge
