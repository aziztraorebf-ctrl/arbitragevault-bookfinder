// ActivityFeed - Chronological event list
import {
  Search,
  CheckCircle,
  Bookmark,
  AlertTriangle,
  TrendingUp
} from 'lucide-react'
import type { ActivityEvent } from '../../data/mockDashboard'

const iconMap = {
  analysis: TrendingUp,
  niche: Search,
  verification: CheckCircle,
  search_saved: Bookmark,
  alert: AlertTriangle,
}

const colorMap = {
  analysis: 'text-vault-success',
  niche: 'text-vault-accent',
  verification: 'text-vault-success',
  search_saved: 'text-vault-accent',
  alert: 'text-vault-warning',
}

const bgColorMap = {
  analysis: 'bg-vault-success-light',
  niche: 'bg-vault-accent-light',
  verification: 'bg-vault-success-light',
  search_saved: 'bg-vault-accent-light',
  alert: 'bg-vault-warning-light',
}

interface ActivityFeedProps {
  events: ActivityEvent[]
  className?: string
}

export function ActivityFeed({ events, className = '' }: ActivityFeedProps) {
  return (
    <div
      className={`
        bg-vault-card rounded-vault-sm shadow-vault-sm
        overflow-hidden
        ${className}
      `}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-vault-border">
        <h3 className="text-base font-semibold text-vault-text">
          Activity Feed
        </h3>
      </div>

      {/* Events */}
      <div className="divide-y divide-vault-border-light">
        {events.map((event) => {
          const IconComponent = iconMap[event.type]
          const colorClass = colorMap[event.type]
          const bgClass = bgColorMap[event.type]

          return (
            <div
              key={event.id}
              className="px-6 py-4 hover:bg-vault-hover transition-colors duration-150 cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                {/* Icon with background */}
                <div className={`p-2 rounded-full ${bgClass} flex-shrink-0`}>
                  <IconComponent className={`w-4 h-4 ${colorClass}`} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-vault-text-muted uppercase tracking-wide">
                      {event.timestamp}
                    </span>
                  </div>
                  <p className="text-sm text-vault-text leading-relaxed">
                    {event.message.split(' - ').map((part, i) => (
                      <span key={i}>
                        {i === 0 ? (
                          <span className="font-semibold">{part}</span>
                        ) : (
                          <span>: {part}</span>
                        )}
                      </span>
                    ))}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
