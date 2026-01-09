/**
 * Cache Hit/Miss Indicator Component
 * Shows if data came from cache or fresh API call
 * Vault Elegance Design
 */

import { Zap, RefreshCw } from 'lucide-react'

interface CacheIndicatorProps {
  cacheHit: boolean
  className?: string
}

export function CacheIndicator({ cacheHit, className = '' }: CacheIndicatorProps) {
  if (cacheHit) {
    return (
      <div
        className={`inline-flex items-center gap-2 px-3 py-1.5 bg-vault-accent-light text-vault-accent rounded-full text-sm font-medium ${className}`}
      >
        <Zap className="w-4 h-4" />
        <span>Cache HIT</span>
        <span className="text-xs opacity-75">(~50ms)</span>
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded-full text-sm font-medium ${className}`}
    >
      <RefreshCw className="w-4 h-4" />
      <span>Fresh Data</span>
      <span className="text-xs opacity-75">(~2-3s)</span>
    </div>
  )
}
