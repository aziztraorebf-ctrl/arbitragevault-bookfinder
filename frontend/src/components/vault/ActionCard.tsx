// ActionCard - Notification-style action card
import { useNavigate } from 'react-router-dom'
import { BookOpen, Bell, FileText } from 'lucide-react'
import type { ActionCardData } from '../../data/mockDashboard'

const iconMap = {
  BookOpen,
  Bell,
  FileText,
}

interface ActionCardProps extends ActionCardData {
  className?: string
}

export function ActionCard({
  title,
  icon,
  lines,
  action,
  className = ''
}: ActionCardProps) {
  const navigate = useNavigate()
  const IconComponent = iconMap[icon]

  const handleAction = () => {
    if (action.href) {
      navigate(action.href)
    }
  }

  return (
    <div
      className={`
        relative overflow-hidden
        bg-vault-card rounded-vault-sm
        shadow-vault-sm hover:shadow-vault-md
        border-l-[3px] border-l-vault-accent
        transition-all duration-300 ease-out
        group
        ${className}
      `}
    >
      {/* Content */}
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-base font-semibold text-vault-text pr-8">
            {title}
          </h3>
          <IconComponent className="w-5 h-5 text-vault-text-muted flex-shrink-0" />
        </div>

        {/* Description lines */}
        <div className="space-y-1 mb-4">
          {lines.map((line, index) => (
            <p
              key={index}
              className={`text-sm ${index === 0 ? 'font-medium text-vault-text' : 'text-vault-text-secondary'}`}
            >
              {line}
            </p>
          ))}
        </div>

        {/* Action button */}
        <button
          onClick={handleAction}
          className="
            inline-flex items-center
            text-sm font-medium text-vault-accent
            hover:text-vault-accent-hover
            transition-colors duration-200
            group/btn
          "
        >
          <span className="border-b border-transparent group-hover/btn:border-vault-accent-hover transition-colors duration-200">
            {action.label}
          </span>
        </button>
      </div>
    </div>
  )
}
