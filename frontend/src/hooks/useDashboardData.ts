/**
 * React Query hook for Dashboard data aggregation
 * Phase 2D - Real data integration for Dashboard KPIs
 *
 * Aggregates data from existing endpoints:
 * - /autosourcing/stats -> action counts, pending deals
 * - /autosourcing/jobs -> recent activity
 * - /autosourcing/opportunity-of-day -> best opportunity
 * - /recherches/stats -> saved searches count
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

// =============================================================================
// TYPES
// =============================================================================

interface AutoSourcingStats {
  action_counts: {
    pending: number
    to_buy: number
    purchased: number
    ignored: number
    favorited: number
    [key: string]: number
  }
  total_actions_taken: number
  purchase_pipeline: number
  engagement_rate: string
}

interface AutoSourcingJob {
  id: string
  profile_name: string
  launched_at: string
  completed_at: string | null
  status: string
  total_tested: number
  total_selected: number
}

interface OpportunityPick {
  asin: string
  title: string
  roi_percentage: number
  current_price: number | null
  bsr: number | null
}

interface OpportunityOfDay {
  pick: OpportunityPick
  job_profile: string
  found_at: string
  message: string
}

interface RecherchesStats {
  total: number
  niche_discovery?: number
  autosourcing?: number
  manual_analysis?: number
}

// Dashboard aggregated data
export interface DashboardData {
  // KPIs
  pendingDeals: number
  totalSearches: number
  purchasePipeline: number
  bestRoi: number | null

  // Activity
  recentJobs: AutoSourcingJob[]
  opportunityOfDay: OpportunityOfDay | null

  // Metadata
  isLoading: boolean
  isError: boolean
  errorMessage: string | null
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

async function fetchAutoSourcingStats(): Promise<AutoSourcingStats | null> {
  try {
    const response = await api.get('/api/v1/autosourcing/stats')
    return response.data
  } catch (error) {
    console.warn('[Dashboard] AutoSourcing stats not available:', error)
    return null
  }
}

async function fetchRecentJobs(limit: number = 5): Promise<AutoSourcingJob[]> {
  try {
    const response = await api.get('/api/v1/autosourcing/jobs', {
      params: { limit }
    })
    return response.data || []
  } catch (error) {
    console.warn('[Dashboard] Recent jobs not available:', error)
    return []
  }
}

async function fetchOpportunityOfDay(): Promise<OpportunityOfDay | null> {
  try {
    const response = await api.get('/api/v1/autosourcing/opportunity-of-day')
    return response.data
  } catch (error) {
    console.warn('[Dashboard] Opportunity of day not available:', error)
    return null
  }
}

async function fetchRecherchesStats(): Promise<RecherchesStats | null> {
  try {
    const response = await api.get('/api/v1/recherches/stats')
    return response.data
  } catch (error) {
    console.warn('[Dashboard] Recherches stats not available:', error)
    return null
  }
}

// =============================================================================
// AGGREGATOR
// =============================================================================

async function fetchDashboardData(): Promise<Omit<DashboardData, 'isLoading' | 'isError' | 'errorMessage'>> {
  // Fetch all data in parallel for performance
  const [autoStats, jobs, opportunity, rechercheStats] = await Promise.all([
    fetchAutoSourcingStats(),
    fetchRecentJobs(5),
    fetchOpportunityOfDay(),
    fetchRecherchesStats()
  ])

  return {
    // KPIs - with fallbacks
    pendingDeals: autoStats?.action_counts?.pending ?? 0,
    totalSearches: rechercheStats?.total ?? 0,
    purchasePipeline: autoStats?.purchase_pipeline ?? 0,
    bestRoi: opportunity?.pick?.roi_percentage ?? null,

    // Activity
    recentJobs: jobs,
    opportunityOfDay: opportunity,
  }
}

// =============================================================================
// HOOK
// =============================================================================

export const dashboardKeys = {
  all: ['dashboard'] as const,
  data: () => [...dashboardKeys.all, 'data'] as const,
}

export function useDashboardData() {
  const query = useQuery({
    queryKey: dashboardKeys.data(),
    queryFn: fetchDashboardData,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    retry: 1, // Only retry once on failure
  })

  return {
    // KPIs
    pendingDeals: query.data?.pendingDeals ?? 0,
    totalSearches: query.data?.totalSearches ?? 0,
    purchasePipeline: query.data?.purchasePipeline ?? 0,
    bestRoi: query.data?.bestRoi ?? null,

    // Activity
    recentJobs: query.data?.recentJobs ?? [],
    opportunityOfDay: query.data?.opportunityOfDay ?? null,

    // Metadata
    isLoading: query.isLoading,
    isError: query.isError,
    errorMessage: query.error?.message ?? null,

    // Actions
    refetch: query.refetch,
  }
}
