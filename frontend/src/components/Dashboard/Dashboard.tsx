// Dashboard - Vault Elegance Design
// Premium dashboard with real-time KPIs, action cards, and activity feed
// Phase 2D: Connected to real data endpoints
import { KpiCard, ActionCard, ActivityFeed, DailyReviewCard } from '../vault'
import {
  mockActionCards,
  getGreeting,
  formatDate
} from '../../data/mockDashboard'
import type { ActivityEvent } from '../../data/mockDashboard'
import { USER_CONFIG } from '../../config/user'
import { useDashboardData } from '../../hooks'

// Skeleton loader for KPI cards
function KpiSkeleton() {
  return (
    <div className="bg-vault-card rounded-vault-sm p-6 animate-pulse">
      <div className="h-4 bg-vault-border rounded w-1/2 mb-4" />
      <div className="h-8 bg-vault-border rounded w-3/4 mb-2" />
      <div className="h-3 bg-vault-border rounded w-1/4" />
    </div>
  )
}

// Format relative time from ISO date string
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString()
}

export default function Dashboard() {
  const greeting = getGreeting()
  const dateString = formatDate()

  // Fetch real data from backend
  const {
    pendingDeals,
    totalSearches,
    purchasePipeline,
    bestRoi,
    recentJobs,
    opportunityOfDay,
    dailyReview,
    isLoading,
    isError
  } = useDashboardData()

  // Transform recent jobs into ActivityEvents
  const activityEvents: ActivityEvent[] = recentJobs.map((job) => ({
    id: job.id,
    type: 'analysis' as const,
    timestamp: formatRelativeTime(job.launched_at),
    message: `${job.profile_name} - ${job.total_selected} opportunities found`
  }))

  // Build real KPI data
  const realKpiData = {
    purchasePipeline: {
      value: String(purchasePipeline),
      label: 'Purchase Pipeline',
      change: 0,
      sparkData: [] as number[]
    },
    totalSearches: {
      value: String(totalSearches),
      label: 'Saved Searches',
      change: 0,
      sparkData: [] as number[]
    },
    bestRoi: {
      value: bestRoi !== null ? `${bestRoi.toFixed(1)}%` : 'N/A',
      label: 'Best ROI Today',
      change: 0,
      sparkData: [] as number[]
    },
    pendingDeals: {
      value: String(pendingDeals),
      label: 'Pending Deals',
      change: 0,
      sparkData: [] as number[]
    }
  }

  // Build action cards - use opportunity of day if available
  const actionCards = opportunityOfDay
    ? [
        {
          id: 'opportunity',
          title: 'Opportunity of the Day',
          icon: 'BookOpen' as const,
          lines: [
            opportunityOfDay.pick.asin,
            `ROI: ${opportunityOfDay.pick.roi_percentage.toFixed(1)}%`,
            opportunityOfDay.pick.title?.slice(0, 50) || 'View details'
          ],
          action: { label: 'Analyze', href: `/analyse?asin=${opportunityOfDay.pick.asin}` }
        },
        ...mockActionCards.slice(1) // Keep other mock cards for now
      ]
    : mockActionCards

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ========================================
          GREETING SECTION
          ======================================== */}
      <section className="mb-8">
        <h1 className="text-4xl md:text-5xl font-display font-semibold text-vault-text mb-2 tracking-tight">
          {greeting} {USER_CONFIG.displayName}
        </h1>
        <p className="text-sm md:text-base text-vault-text-secondary">
          {dateString}
        </p>
      </section>

      {/* ========================================
          KPI CARDS
          ======================================== */}
      <section>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6">
          {isLoading ? (
            <>
              <KpiSkeleton />
              <KpiSkeleton />
              <KpiSkeleton />
              <KpiSkeleton />
            </>
          ) : isError ? (
            <div className="col-span-full text-center py-8 text-vault-text-muted">
              Unable to load dashboard data. Please try again later.
            </div>
          ) : (
            <>
              <KpiCard {...realKpiData.purchasePipeline} />
              <KpiCard {...realKpiData.totalSearches} />
              <KpiCard {...realKpiData.bestRoi} />
              <KpiCard {...realKpiData.pendingDeals} />
            </>
          )}
        </div>
      </section>

      {/* ========================================
          DAILY REVIEW
          ======================================== */}
      <section>
        <DailyReviewCard review={dailyReview} isLoading={isLoading} />
      </section>

      {/* ========================================
          ACTION CARDS
          ======================================== */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          {actionCards.map((card) => (
            <ActionCard key={card.id} {...card} />
          ))}
        </div>
      </section>

      {/* ========================================
          ACTIVITY FEED
          ======================================== */}
      <section>
        <ActivityFeed events={activityEvents} />
      </section>
    </div>
  )
}
