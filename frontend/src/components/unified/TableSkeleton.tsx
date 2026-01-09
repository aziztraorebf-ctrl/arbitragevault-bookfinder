/**
 * TableSkeleton - Loading skeleton for UnifiedProductTable
 * Shows animated placeholder rows while data is loading
 */

interface TableSkeletonProps {
  rows?: number
  showScore?: boolean
  showRank?: boolean
}

export function TableSkeleton({
  rows = 5,
  showScore = false,
  showRank = false
}: TableSkeletonProps) {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Header skeleton */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
            <div className="h-5 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      </div>

      {/* Table skeleton */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 w-12">
                <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
              </th>
              {showRank && (
                <th className="hidden md:table-cell px-4 py-3">
                  <div className="h-4 w-12 bg-gray-200 rounded animate-pulse mx-auto" />
                </th>
              )}
              <th className="px-4 py-3">
                <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
              </th>
              <th className="px-4 py-3">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
              </th>
              {showScore && (
                <th className="hidden md:table-cell px-4 py-3">
                  <div className="h-4 w-14 bg-gray-200 rounded animate-pulse mx-auto" />
                </th>
              )}
              <th className="px-4 py-3">
                <div className="h-4 w-12 bg-gray-200 rounded animate-pulse mx-auto" />
              </th>
              <th className="hidden md:table-cell px-4 py-3">
                <div className="h-4 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
              </th>
              <th className="hidden md:table-cell px-4 py-3">
                <div className="h-4 w-14 bg-gray-200 rounded animate-pulse mx-auto" />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i} className="hover:bg-gray-50">
                {/* Expand button */}
                <td className="px-4 py-3">
                  <div className="h-5 w-5 bg-gray-200 rounded animate-pulse" />
                </td>
                {/* Rank */}
                {showRank && (
                  <td className="hidden md:table-cell px-4 py-3">
                    <div className="h-5 w-8 bg-gray-200 rounded animate-pulse mx-auto" />
                  </td>
                )}
                {/* ASIN */}
                <td className="px-4 py-3">
                  <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
                </td>
                {/* Title */}
                <td className="px-4 py-3">
                  <div className="space-y-2">
                    <div className="h-4 w-40 bg-gray-200 rounded animate-pulse" />
                    <div className="h-3 w-24 bg-gray-100 rounded animate-pulse" />
                  </div>
                </td>
                {/* Score */}
                {showScore && (
                  <td className="hidden md:table-cell px-4 py-3">
                    <div className="h-5 w-10 bg-gray-200 rounded animate-pulse mx-auto" />
                  </td>
                )}
                {/* ROI */}
                <td className="px-4 py-3">
                  <div className="h-5 w-14 bg-gray-200 rounded animate-pulse mx-auto" />
                </td>
                {/* Velocity */}
                <td className="hidden md:table-cell px-4 py-3">
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-5 w-8 bg-gray-200 rounded animate-pulse" />
                    <div className="w-16 h-2 bg-gray-200 rounded-full animate-pulse" />
                  </div>
                </td>
                {/* BSR */}
                <td className="hidden md:table-cell px-4 py-3">
                  <div className="h-5 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
