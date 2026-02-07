// DailyReviewCard - Daily classification review summary card
import { Calendar, TrendingUp, Package, AlertCircle } from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DailyReviewData {
  review_date: string
  total: number
  counts: {
    STABLE: number
    JACKPOT: number
    REVENANT: number
    FLUKE: number
    REJECT: number
  }
  top_opportunities: Array<{
    asin: string
    title: string
    roi_percentage: number
    classification: string
    classification_label: string
    classification_color: string
  }>
  summary: string
}

interface DailyReviewCardProps {
  review: DailyReviewData | null
  isLoading: boolean
}

// ---------------------------------------------------------------------------
// Classification badge config
// ---------------------------------------------------------------------------

const CLASSIFICATION_COLORS: Record<string, string> = {
  STABLE: 'bg-green-500 text-white',
  JACKPOT: 'bg-yellow-500 text-white',
  REVENANT: 'bg-blue-500 text-white',
  FLUKE: 'bg-gray-500 text-white',
  REJECT: 'bg-red-500 text-white',
}

const CLASSIFICATION_ORDER: Array<keyof DailyReviewData['counts']> = [
  'STABLE',
  'JACKPOT',
  'REVENANT',
  'FLUKE',
  'REJECT',
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatReviewDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// ---------------------------------------------------------------------------
// Skeleton (loading state)
// ---------------------------------------------------------------------------

function DailyReviewSkeleton() {
  return (
    <div
      className="
        bg-vault-card rounded-vault-sm p-5
        shadow-vault-sm border border-vault-border-light
        animate-pulse
      "
    >
      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 bg-vault-border rounded" />
          <div className="h-5 w-28 bg-vault-border rounded" />
        </div>
        <div className="h-4 w-40 bg-vault-border rounded" />
      </div>

      {/* Summary skeleton */}
      <div className="h-4 w-full bg-vault-border rounded mb-2" />
      <div className="h-4 w-3/4 bg-vault-border rounded mb-4" />

      {/* Badges skeleton */}
      <div className="flex gap-2 mb-4">
        <div className="h-6 w-16 bg-vault-border rounded-full" />
        <div className="h-6 w-16 bg-vault-border rounded-full" />
        <div className="h-6 w-16 bg-vault-border rounded-full" />
      </div>

      {/* Opportunities skeleton */}
      <div className="space-y-3">
        <div className="h-12 bg-vault-border rounded" />
        <div className="h-12 bg-vault-border rounded" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function DailyReviewEmpty() {
  return (
    <div
      className="
        bg-vault-card rounded-vault-sm p-5
        shadow-vault-sm border border-vault-border-light
        flex flex-col items-center justify-center py-10
      "
    >
      <AlertCircle className="w-10 h-10 text-vault-text-muted mb-3" />
      <p className="text-sm text-vault-text-muted">
        Aucune donnee disponible
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function DailyReviewCard({ review, isLoading }: DailyReviewCardProps) {
  if (isLoading) {
    return <DailyReviewSkeleton />
  }

  if (!review) {
    return <DailyReviewEmpty />
  }

  const visibleCounts = CLASSIFICATION_ORDER.filter(
    (key) => review.counts[key] > 0
  )

  return (
    <div
      className="
        relative overflow-hidden
        bg-vault-card rounded-vault-sm p-5
        shadow-vault-sm hover:shadow-vault-md
        border border-vault-border-light
        transition-all duration-300 ease-out
        animate-fade-in
      "
    >
      {/* ---- Header ---- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-vault-accent flex-shrink-0" />
          <h3 className="text-base font-display font-semibold text-vault-text">
            Daily Review
          </h3>
        </div>
        <span className="text-xs text-vault-text-muted">
          {formatReviewDate(review.review_date)}
        </span>
      </div>

      {/* ---- Summary ---- */}
      <p className="text-sm text-vault-text-secondary mb-4 leading-relaxed">
        {review.summary}
      </p>

      {/* ---- Classification badges ---- */}
      {visibleCounts.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {visibleCounts.map((key) => (
            <span
              key={key}
              className={`
                inline-flex items-center gap-1
                px-2.5 py-0.5 rounded-full
                text-xs font-medium
                ${CLASSIFICATION_COLORS[key]}
              `}
            >
              {key}
              <span className="font-bold">{review.counts[key]}</span>
            </span>
          ))}
          <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-medium text-vault-text-muted">
            Total: {review.total}
          </span>
        </div>
      )}

      {/* ---- Top opportunities ---- */}
      {review.top_opportunities.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <TrendingUp className="w-4 h-4 text-vault-text-muted" />
            <h4 className="text-xs font-semibold text-vault-text-muted uppercase tracking-wider">
              Top Opportunities
            </h4>
          </div>

          <div className="space-y-2">
            {review.top_opportunities.slice(0, 3).map((opp) => (
              <div
                key={opp.asin}
                className="
                  flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1
                  p-2.5 rounded-lg
                  bg-vault-bg/50
                  border border-vault-border-light/50
                "
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Package className="w-4 h-4 text-vault-text-muted flex-shrink-0 hidden sm:block" />
                  <code className="text-xs font-mono text-vault-accent flex-shrink-0">
                    {opp.asin}
                  </code>
                  <span className="text-sm text-vault-text truncate">
                    {opp.title}
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 pl-6 sm:pl-0">
                  <span className="text-sm font-semibold text-vault-text">
                    {opp.roi_percentage.toFixed(1)}%
                  </span>
                  <span
                    className={`
                      inline-flex px-2 py-0.5 rounded-full
                      text-[10px] font-medium uppercase
                      ${CLASSIFICATION_COLORS[opp.classification] || 'bg-gray-400 text-white'}
                    `}
                  >
                    {opp.classification_label || opp.classification}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
