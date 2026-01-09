// Dashboard - Vault Elegance Design
// Premium dashboard with KPIs, action cards, and activity feed
import { KpiCard, ActionCard, ActivityFeed } from '../vault'
import {
  mockKpiData,
  mockActionCards,
  mockActivityFeed,
  getGreeting,
  formatDate
} from '../../data/mockDashboard'
import { USER_CONFIG } from '../../config/user'

export default function Dashboard() {
  const greeting = getGreeting()
  const dateString = formatDate()

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
          <KpiCard {...mockKpiData.totalValue} />
          <KpiCard {...mockKpiData.productsAnalyzed} />
          <KpiCard {...mockKpiData.avgRoi} />
          <KpiCard {...mockKpiData.pendingReviews} />
        </div>
      </section>

      {/* ========================================
          ACTION CARDS
          ======================================== */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          {mockActionCards.map((card) => (
            <ActionCard key={card.id} {...card} />
          ))}
        </div>
      </section>

      {/* ========================================
          ACTIVITY FEED
          ======================================== */}
      <section>
        <ActivityFeed events={mockActivityFeed} />
      </section>
    </div>
  )
}
