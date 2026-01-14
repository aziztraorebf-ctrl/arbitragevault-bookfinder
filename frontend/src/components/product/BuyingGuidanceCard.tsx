/**
 * BuyingGuidanceCard - Clear buy/sell recommendations
 *
 * Design: Vault Elegance - clean card with visual hierarchy
 * Shows: Max buy price, Target sell price, Estimated profit
 *
 * This is the CORE decision-making component for users.
 */

import { Tooltip } from '../ui/Tooltip'
import { ConfidenceBadge } from '../ui/ConfidenceBadge'
import { RecommendationBadge } from '../ui/RecommendationBadge'
import { Clock, TrendingUp, DollarSign, ShoppingCart, Tag } from 'lucide-react'

export interface BuyingGuidance {
  max_buy_price: number
  target_sell_price: number
  estimated_profit: number
  estimated_roi_pct: number
  price_range: string
  estimated_days_to_sell: number
  recommendation: 'BUY' | 'HOLD' | 'SKIP'
  recommendation_reason: string
  confidence_label: string
  explanations: Record<string, string>
}

interface BuyingGuidanceCardProps {
  guidance: BuyingGuidance
  /** @deprecated Not currently used, may be removed in future */
  _sourcePrice?: number
  compact?: boolean
}

/**
 * Format currency with $ sign
 */
function formatCurrency(value: number): string {
  if (value <= 0) return 'N/A'
  return `$${value.toFixed(2)}`
}

/**
 * Format percentage
 */
function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`
}

/**
 * Full BuyingGuidanceCard - for detail views and expanded rows
 */
export function BuyingGuidanceCard({
  guidance,
  compact = false,
}: BuyingGuidanceCardProps) {
  if (compact) {
    return <BuyingGuidanceCompact guidance={guidance} />
  }

  return (
    <div className="bg-white rounded-vault-sm shadow-vault-md border border-vault-border overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 to-white border-b border-vault-border-light">
        <h3 className="text-base font-semibold text-vault-text flex items-center gap-2">
          <ShoppingCart className="w-4 h-4 text-vault-accent" />
          Guide Achat/Vente
        </h3>
        <div className="flex items-center gap-2">
          <ConfidenceBadge level={guidance.confidence_label} size="sm" />
          <RecommendationBadge recommendation={guidance.recommendation} size="sm" />
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-3 gap-0 divide-x divide-vault-border-light">
        {/* Max Buy Price */}
        <MetricCell
          icon={<Tag className="w-4 h-4" />}
          label="Achete max"
          value={formatCurrency(guidance.max_buy_price)}
          tooltip={guidance.explanations?.max_buy_price || "Prix maximum pour garantir le ROI cible"}
          colorClass="text-blue-600"
          bgClass="bg-blue-50/50"
        />

        {/* Target Sell Price */}
        <MetricCell
          icon={<DollarSign className="w-4 h-4" />}
          label="Vends cible"
          value={formatCurrency(guidance.target_sell_price)}
          subtitle={guidance.price_range}
          tooltip={guidance.explanations?.target_sell_price || "Prix median des 90 derniers jours"}
          colorClass="text-emerald-600"
          bgClass="bg-emerald-50/50"
        />

        {/* Estimated Profit */}
        <MetricCell
          icon={<TrendingUp className="w-4 h-4" />}
          label="Profit"
          value={formatCurrency(guidance.estimated_profit)}
          subtitle={`${formatPercent(guidance.estimated_roi_pct)} ROI`}
          tooltip={guidance.explanations?.estimated_profit || "Profit net apres frais Amazon"}
          colorClass="text-purple-600"
          bgClass="bg-purple-50/50"
        />
      </div>

      {/* Footer - Secondary Info */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-t border-vault-border-light text-sm">
        <Tooltip
          content={guidance.explanations?.estimated_days_to_sell || "Temps moyen pour vendre"}
          showIcon={false}
        >
          <div className="flex items-center gap-1.5 text-vault-text-secondary">
            <Clock className="w-3.5 h-3.5" />
            <span>~{guidance.estimated_days_to_sell}j pour vendre</span>
          </div>
        </Tooltip>

        <Tooltip
          content={guidance.explanations?.confidence || "Fiabilite des donnees"}
          showIcon={false}
        >
          <div className="text-vault-text-muted italic text-xs max-w-[200px] truncate">
            {guidance.recommendation_reason}
          </div>
        </Tooltip>
      </div>
    </div>
  )
}

/**
 * MetricCell - Individual metric display
 */
interface MetricCellProps {
  icon: React.ReactNode
  label: string
  value: string
  subtitle?: string
  tooltip: string
  colorClass: string
  bgClass: string
}

function MetricCell({
  icon,
  label,
  value,
  subtitle,
  tooltip,
  colorClass,
  bgClass,
}: MetricCellProps) {
  return (
    <div className={`text-center p-4 ${bgClass} transition-colors duration-200 hover:bg-opacity-80`}>
      <Tooltip content={tooltip} showIcon={false}>
        <div className="flex items-center justify-center gap-1 text-vault-text-secondary mb-1">
          <span className={colorClass}>{icon}</span>
          <span className="text-xs font-medium">{label}</span>
        </div>
      </Tooltip>
      <div className={`text-xl font-bold ${colorClass}`}>
        {value}
      </div>
      {subtitle && (
        <div className="text-xs text-vault-text-muted mt-0.5">
          {subtitle}
        </div>
      )}
    </div>
  )
}

/**
 * BuyingGuidanceCompact - For table rows
 */
function BuyingGuidanceCompact({ guidance }: { guidance: BuyingGuidance }) {
  return (
    <div className="flex items-center gap-3">
      <div className="text-sm">
        <span className="text-vault-text-muted">Max:</span>{' '}
        <span className="font-semibold text-blue-600">
          {formatCurrency(guidance.max_buy_price)}
        </span>
      </div>
      <div className="text-sm">
        <span className="text-vault-text-muted">Vente:</span>{' '}
        <span className="font-semibold text-emerald-600">
          {formatCurrency(guidance.target_sell_price)}
        </span>
      </div>
      <RecommendationBadge recommendation={guidance.recommendation} size="sm" showIcon={false} />
    </div>
  )
}

/**
 * BuyingGuidanceInline - Single line for very compact displays
 */
export function BuyingGuidanceInline({ guidance }: { guidance: BuyingGuidance }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm">
      <span className="text-blue-600 font-medium">
        Max {formatCurrency(guidance.max_buy_price)}
      </span>
      <span className="text-vault-text-muted">/</span>
      <span className="text-emerald-600 font-medium">
        Vente {formatCurrency(guidance.target_sell_price)}
      </span>
      <span className="text-vault-text-muted">/</span>
      <span className="text-purple-600 font-medium">
        {formatPercent(guidance.estimated_roi_pct)} ROI
      </span>
    </span>
  )
}

export default BuyingGuidanceCard
