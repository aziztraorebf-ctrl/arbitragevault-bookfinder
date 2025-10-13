import { ArrowRight, Clock, CheckCircle, XCircle, AlertCircle, Play } from 'lucide-react'
import type { Batch } from '../../hooks'

interface BatchCardProps {
  batch: Batch
  onClick?: (batch: Batch) => void
  className?: string
}

// Status configuration with colors and icons matching Dashboard design
const statusConfig = {
  completed: {
    color: 'green',
    icon: CheckCircle,
    label: 'Terminé',
    bgClass: 'card-gradient-green',
    textClass: 'text-green-100',
  },
  processing: {
    color: 'blue',
    icon: Play,
    label: 'En cours',
    bgClass: 'card-gradient-blue',
    textClass: 'text-blue-100',
  },
  failed: {
    color: 'red',
    icon: XCircle,
    label: 'Échoué',
    bgClass: 'card-gradient-red',
    textClass: 'text-red-100',
  },
  pending: {
    color: 'orange',
    icon: Clock,
    label: 'En attente',
    bgClass: 'card-gradient-orange',
    textClass: 'text-orange-100',
  },
  partial: {
    color: 'violet',
    icon: AlertCircle,
    label: 'Partiel',
    bgClass: 'card-gradient-purple',
    textClass: 'text-purple-100',
  },
} as const

// Format date helper
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return `Il y a ${diffMins}m`
  } else if (diffHours < 24) {
    return `Il y a ${diffHours}h`
  } else if (diffDays < 7) {
    return `Il y a ${diffDays}j`
  } else {
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

export default function BatchCard({ batch, onClick, className = '' }: BatchCardProps) {
  const config = statusConfig[batch.status] || statusConfig.pending
  const StatusIcon = config.icon
  
  // Calculate success rate
  const successRate = batch.total_items > 0 
    ? Math.round((batch.successful_items / batch.total_items) * 100)
    : 0

  // Calculate progress percentage
  const progressRate = batch.total_items > 0
    ? Math.round((batch.processed_items / batch.total_items) * 100)
    : 0

  return (
    <div 
      className={`${config.bgClass} relative overflow-hidden cursor-pointer hover:scale-[1.02] transition-all duration-200 ${className}`}
      onClick={() => onClick?.(batch)}
    >
      {/* Content */}
      <div className="relative z-10">
        {/* Header with icon and status */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <StatusIcon className="w-6 h-6 text-white" />
            <div>
              <div className="typography-h3 text-white font-semibold">
                Batch {batch.batch_id.split('_')[1] || batch.batch_id.substring(0, 8)}
              </div>
              <div className={`typography-body ${config.textClass}`}>
                {config.label}
              </div>
            </div>
          </div>
          <div className={`typography-secondary ${config.textClass}`}>
            {formatDate(batch.created_at)}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="typography-h2 text-white mb-1">
              {batch.total_items}
            </div>
            <div className={`typography-body ${config.textClass}`}>
              Items totaux
            </div>
          </div>
          <div>
            <div className="typography-h2 text-white mb-1">
              {successRate}%
            </div>
            <div className={`typography-body ${config.textClass}`}>
              Taux de succès
            </div>
          </div>
        </div>

        {/* Progress Bar (only for processing status) */}
        {batch.status === 'processing' && (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className={`typography-body ${config.textClass}`}>
                Progression
              </span>
              <span className={`typography-body ${config.textClass}`}>
                {progressRate}%
              </span>
            </div>
            <div className="w-full bg-blue-800/30 rounded-full h-2">
              <div 
                className="bg-white h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressRate}%` }}
              />
            </div>
          </div>
        )}

        {/* Footer with details */}
        <div className="flex items-center justify-between">
          <div className={`typography-body ${config.textClass}`}>
            {batch.successful_items} succès • {batch.failed_items} échecs
          </div>
          <button className="card-arrow-button group">
            <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>

      {/* Background Pattern (matching Dashboard cards) */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-4 right-4 text-white/20 text-6xl">
          📊
        </div>
      </div>
    </div>
  )
}