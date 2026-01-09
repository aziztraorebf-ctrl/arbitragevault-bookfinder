// Mock data for Vault Elegance Dashboard
// Focus: Realistic book arbitrage metrics

export interface KpiData {
  value: string
  label: string
  change: number
  sparkData: number[]
}

export interface ActionCardData {
  id: string
  title: string
  icon: 'BookOpen' | 'Bell' | 'FileText'
  lines: string[]
  action: {
    label: string
    href?: string
  }
}

export interface ActivityEvent {
  id: string
  type: 'analysis' | 'niche' | 'verification' | 'search_saved' | 'alert'
  timestamp: string
  message: string
}

export const mockKpiData: Record<string, KpiData> = {
  totalValue: {
    value: "$45,280.15",
    label: "Total Arbitrage Value",
    change: 12.5,
    sparkData: [32, 35, 33, 38, 42, 40, 45]
  },
  productsAnalyzed: {
    value: "2,450",
    label: "Book Inventory Count",
    change: 3.2,
    sparkData: [180, 195, 210, 205, 230, 240, 245]
  },
  avgRoi: {
    value: "28.4%",
    label: "Profit Margin (Avg)",
    change: 1.8,
    sparkData: [24, 25, 26, 27, 26, 28, 28]
  },
  pendingReviews: {
    value: "15",
    label: "Pending Deals",
    change: -2.1,
    sparkData: [22, 20, 18, 17, 16, 16, 15]
  }
}

export const mockActionCards: ActionCardData[] = [
  {
    id: "1",
    title: "New Arbitrage Opportunity",
    icon: "BookOpen",
    lines: [
      "ISBN 978-3-16-148410-0",
      "Potential Profit: $85.00 | Source: Online Retailer A",
      "Destination: B2B Market B"
    ],
    action: { label: "Analyze Deal", href: "/analyse" }
  },
  {
    id: "2",
    title: "Market Alert",
    icon: "Bell",
    lines: [
      "Price Drop Detected.",
      "Book Title: 'The Innovator's Dilemma' | Current Price: $12.50",
      "Alert: Below Threshold"
    ],
    action: { label: "View Details", href: "/niche-discovery" }
  },
  {
    id: "3",
    title: "Performance Report",
    icon: "FileText",
    lines: [
      "Monthly Analytics Ready.",
      "Period: December 2025 | Insights: Top 5",
      "Profitable Categories"
    ],
    action: { label: "Download PDF", href: "/recherches" }
  }
]

export const mockActivityFeed: ActivityEvent[] = [
  {
    id: "1",
    type: "analysis",
    timestamp: "10:45 AM",
    message: "Deal Closed: 'Zero to One' - Profit $62.50"
  },
  {
    id: "2",
    type: "alert",
    timestamp: "09:30 AM",
    message: "Price Alert: 'Sapiens' - New Low at $14.20"
  },
  {
    id: "3",
    type: "verification",
    timestamp: "Yesterday",
    message: "Inventory Update: 50 units added to 'Warehouse B'"
  },
  {
    id: "4",
    type: "search_saved",
    timestamp: "Yesterday",
    message: "Report Generated: Q4 2025 Arbitrage Analysis"
  },
  {
    id: "5",
    type: "niche",
    timestamp: "2 days ago",
    message: "Niche Found: 'Psychology Textbooks' (ROI 34%)"
  }
]

export function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return "Bonjour"
  if (hour >= 12 && hour < 18) return "Bon apres-midi"
  return "Bonsoir"
}

export function formatDate(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
