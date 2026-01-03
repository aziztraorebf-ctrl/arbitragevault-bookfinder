interface SkeletonCardProps {
  className?: string
}

export function SkeletonCard({ className = '' }: SkeletonCardProps) {
  return (
    <div className={`bg-white shadow-md rounded-xl p-6 animate-pulse ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-6 h-6 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
      <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-12"></div>
    </div>
  )
}
