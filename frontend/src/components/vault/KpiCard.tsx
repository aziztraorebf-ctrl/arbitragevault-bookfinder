// KpiCard - Premium metric card with sparkline
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Sparkline } from './Sparkline'
import type { KpiData } from '../../data/mockDashboard'

interface KpiCardProps extends KpiData {
  className?: string
}

export function KpiCard({
  value,
  label,
  change,
  sparkData,
  className = ''
}: KpiCardProps) {
  const isPositive = change >= 0

  return (
    <div
      className={`
        relative overflow-hidden
        bg-vault-card rounded-vault p-6
        shadow-vault-sm hover:shadow-vault-md
        transition-all duration-300 ease-out
        border border-vault-border-light
        group
        ${className}
      `}
    >
      {/* Subtle gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-vault-accent-light to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="relative">
        {/* Header: Sparkline + Change badge */}
        <div className="flex items-start justify-between mb-4">
          <Sparkline data={sparkData} width={80} height={32} />

          <div
            className={`
              flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
              ${isPositive
                ? 'bg-vault-success-light text-vault-success'
                : 'bg-vault-danger-light text-vault-danger'
              }
            `}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span>{isPositive ? '+' : ''}{change.toFixed(1)}%</span>
          </div>
        </div>

        {/* Value */}
        <div className="text-[28px] font-bold text-vault-text font-sans tracking-tight mb-1">
          {value}
        </div>

        {/* Label */}
        <div className="text-sm text-vault-text-secondary font-medium">
          {label}
        </div>
      </div>
    </div>
  )
}
