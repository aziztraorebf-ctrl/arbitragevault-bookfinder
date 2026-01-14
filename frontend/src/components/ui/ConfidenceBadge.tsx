/**
 * ConfidenceBadge - Visual indicator of data reliability
 *
 * Design: Vault Elegance - subtle glow effect on badges
 * Colors match confidence level semantically
 */

interface ConfidenceBadgeProps {
  /** Confidence level in French */
  level: 'Fiable' | 'Modere' | 'Incertain' | 'Donnees insuffisantes' | string
  /** Show text label or just the dot */
  showLabel?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

interface BadgeStyle {
  bg: string
  text: string
  dot: string
  glow: string
}

const BADGE_STYLES: Record<string, BadgeStyle> = {
  'Fiable': {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    dot: 'bg-emerald-500',
    glow: 'shadow-emerald-500/30',
  },
  'Modere': {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    dot: 'bg-amber-500',
    glow: 'shadow-amber-500/30',
  },
  'Incertain': {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    dot: 'bg-orange-500',
    glow: 'shadow-orange-500/30',
  },
  'Donnees insuffisantes': {
    bg: 'bg-red-50',
    text: 'text-red-700',
    dot: 'bg-red-500',
    glow: 'shadow-red-500/30',
  },
}

const SIZE_STYLES = {
  sm: {
    container: 'px-2 py-0.5 text-xs gap-1',
    dot: 'w-1.5 h-1.5',
  },
  md: {
    container: 'px-2.5 py-1 text-xs gap-1.5',
    dot: 'w-2 h-2',
  },
  lg: {
    container: 'px-3 py-1.5 text-sm gap-2',
    dot: 'w-2.5 h-2.5',
  },
}

export function ConfidenceBadge({
  level,
  showLabel = true,
  size = 'md',
}: ConfidenceBadgeProps) {
  // Default to 'Incertain' if unknown level
  const styles = BADGE_STYLES[level] || BADGE_STYLES['Incertain']
  const sizeStyles = SIZE_STYLES[size]

  return (
    <span
      className={`
        inline-flex items-center
        ${sizeStyles.container}
        ${styles.bg} ${styles.text}
        rounded-full
        font-medium
        transition-all duration-200
        hover:shadow-md ${styles.glow}
      `}
      title={`Niveau de confiance: ${level}`}
    >
      {/* Animated dot with pulse on hover */}
      <span
        className={`
          ${sizeStyles.dot}
          ${styles.dot}
          rounded-full
          transition-transform duration-200
          group-hover:scale-110
        `}
        aria-hidden="true"
      />

      {showLabel && (
        <span className="whitespace-nowrap">
          {level}
        </span>
      )}
    </span>
  )
}

/**
 * ConfidenceDot - Just the colored dot without label
 * For compact displays like table cells
 */
export function ConfidenceDot({ level }: { level: string }) {
  const styles = BADGE_STYLES[level] || BADGE_STYLES['Incertain']

  return (
    <span
      className={`
        inline-block w-2.5 h-2.5 rounded-full
        ${styles.dot}
        shadow-sm ${styles.glow}
      `}
      title={level}
      aria-label={`Confiance: ${level}`}
    />
  )
}

export default ConfidenceBadge
