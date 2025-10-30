/**
 * Cache Hit/Miss Indicator Component
 * Shows if data came from cache or fresh API call
 */

interface CacheIndicatorProps {
  cacheHit: boolean
  className?: string
}

export function CacheIndicator({ cacheHit, className = '' }: CacheIndicatorProps) {
  if (cacheHit) {
    return (
      <div
        className={`inline-flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium ${className}`}
      >
        <span className="text-lg">⚡</span>
        <span>Cache HIT</span>
        <span className="text-xs opacity-75">(~50ms)</span>
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium ${className}`}
    >
      <span className="text-lg">🔄</span>
      <span>Fresh Data</span>
      <span className="text-xs opacity-75">(~2-3s)</span>
    </div>
  )
}
