/**
 * Tooltip Component - Elegant explanations on hover
 *
 * Design: Vault Elegance - refined dark tooltips with subtle shadows
 * Uses CSS-only group-hover pattern for performance
 */

import { HelpCircle } from 'lucide-react'
import type { ReactNode } from 'react'

interface TooltipProps {
  /** Tooltip content - can be string or JSX */
  content: ReactNode
  /** Optional children to wrap */
  children?: ReactNode
  /** Tooltip position relative to trigger */
  position?: 'top' | 'bottom' | 'left' | 'right'
  /** Show help icon (?) next to children */
  showIcon?: boolean
  /** Icon size in pixels */
  iconSize?: number
  /** Custom class for the wrapper */
  className?: string
}

const positionStyles = {
  top: {
    container: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    arrow: 'top-full left-1/2 -translate-x-1/2 -mt-1 border-t-gray-900 border-x-transparent border-b-transparent',
  },
  bottom: {
    container: 'top-full left-1/2 -translate-x-1/2 mt-2',
    arrow: 'bottom-full left-1/2 -translate-x-1/2 -mb-1 border-b-gray-900 border-x-transparent border-t-transparent',
  },
  left: {
    container: 'right-full top-1/2 -translate-y-1/2 mr-2',
    arrow: 'left-full top-1/2 -translate-y-1/2 -ml-1 border-l-gray-900 border-y-transparent border-r-transparent',
  },
  right: {
    container: 'left-full top-1/2 -translate-y-1/2 ml-2',
    arrow: 'right-full top-1/2 -translate-y-1/2 -mr-1 border-r-gray-900 border-y-transparent border-l-transparent',
  },
}

export function Tooltip({
  content,
  children,
  position = 'top',
  showIcon = true,
  iconSize = 14,
  className = '',
}: TooltipProps) {
  const styles = positionStyles[position]

  return (
    <div className={`relative inline-flex items-center group ${className}`}>
      {children}

      {showIcon && (
        <HelpCircle
          className="ml-1 text-vault-text-muted cursor-help transition-colors duration-200 group-hover:text-vault-accent"
          style={{ width: iconSize, height: iconSize }}
          aria-hidden="true"
        />
      )}

      {/* Tooltip container */}
      <div
        className={`
          absolute ${styles.container}
          px-3 py-2
          text-sm text-white
          bg-gray-900
          rounded-lg
          opacity-0 invisible
          group-hover:opacity-100 group-hover:visible
          transition-all duration-200 ease-out
          z-50
          min-w-[180px] max-w-[280px]
          shadow-lg shadow-black/20
          pointer-events-none
        `}
        role="tooltip"
      >
        {content}

        {/* Arrow */}
        <div
          className={`
            absolute ${styles.arrow}
            w-0 h-0
            border-[6px]
          `}
          aria-hidden="true"
        />
      </div>
    </div>
  )
}

/**
 * TooltipText - Inline text with tooltip
 * For use in table headers and labels
 */
interface TooltipTextProps {
  text: string
  tooltip: string
  className?: string
}

export function TooltipText({ text, tooltip, className = '' }: TooltipTextProps) {
  return (
    <Tooltip content={tooltip} showIcon={true} iconSize={12}>
      <span className={className}>{text}</span>
    </Tooltip>
  )
}

export default Tooltip
