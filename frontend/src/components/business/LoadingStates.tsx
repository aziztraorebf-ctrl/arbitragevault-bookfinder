import { RefreshCw } from 'lucide-react'

// Loading spinner component
export function LoadingSpinner({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <RefreshCw className={`animate-spin ${className}`} />
  )
}

// Skeleton for stat items
export function StatSkeleton() {
  return (
    <div className="stat-item animate-pulse">
      <div className="h-8 bg-gray-200 rounded mb-2 w-16"></div>
      <div className="h-4 bg-gray-100 rounded mb-1 w-20"></div>
      <div className="h-3 bg-gray-100 rounded w-24"></div>
    </div>
  )
}

// Skeleton for batch cards
export function BatchCardSkeleton() {
  return (
    <div className="card p-6 animate-pulse">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-6 h-6 bg-gray-200 rounded"></div>
        <div>
          <div className="h-5 bg-gray-200 rounded w-24 mb-1"></div>
          <div className="h-4 bg-gray-100 rounded w-16"></div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="h-6 bg-gray-200 rounded w-8 mb-1"></div>
          <div className="h-4 bg-gray-100 rounded w-16"></div>
        </div>
        <div>
          <div className="h-6 bg-gray-200 rounded w-12 mb-1"></div>
          <div className="h-4 bg-gray-100 rounded w-20"></div>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="h-4 bg-gray-100 rounded w-32"></div>
        <div className="w-8 h-8 bg-gray-200 rounded"></div>
      </div>
    </div>
  )
}

// Loading page skeleton for batches
export function BatchesLoadingSkeleton() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 bg-gray-200 rounded w-48 mb-2"></div>
          <div className="h-4 bg-gray-100 rounded w-64"></div>
        </div>
        <div className="flex space-x-3">
          <div className="h-10 bg-gray-200 rounded w-24"></div>
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
      </div>

      {/* Stats skeleton */}
      <div className="quick-stats">
        {[...Array(4)].map((_, i) => (
          <StatSkeleton key={i} />
        ))}
      </div>

      {/* Filter tabs skeleton */}
      <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg w-fit">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-8 bg-gray-200 rounded w-20"></div>
        ))}
      </div>

      {/* Cards grid skeleton */}
      <div className="dashboard-cards-grid">
        {[...Array(8)].map((_, i) => (
          <BatchCardSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

// Connection status indicator
export function ConnectionStatus({ 
  isConnected, 
  isChecking, 
  error 
}: { 
  isConnected: boolean
  isChecking: boolean
  error?: string 
}) {
  if (isChecking) {
    return (
      <div className="flex items-center space-x-2 text-yellow-600">
        <LoadingSpinner className="w-4 h-4" />
        <span className="text-sm">Vérification...</span>
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="flex items-center space-x-2 text-red-600" title={error}>
        <div className="w-2 h-2 bg-red-600 rounded-full"></div>
        <span className="text-sm">Déconnecté</span>
      </div>
    )
  }

  return (
    <div className="flex items-center space-x-2 text-green-600">
      <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
      <span className="text-sm">Connecté</span>
    </div>
  )
}