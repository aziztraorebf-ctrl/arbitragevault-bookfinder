// DocsLayout - Layout wrapper for documentation pages
// Vault Elegance Design System - Premium documentation experience
import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  BookOpen,
  Search,
  BarChart3,
  Bookmark,
  HelpCircle,
  ArrowLeft,
  ChevronRight,
  Bot,
  Package,
  Sparkles,
  FileText
} from 'lucide-react'

interface DocsLayoutProps {
  children: ReactNode
  title: string
  description?: string
  badge?: string
}

const docsSections = [
  {
    title: 'Getting Started',
    items: [
      { name: 'Introduction', href: '/docs', icon: BookOpen },
      { name: 'Premier Lancement', href: '/docs/getting-started', icon: ChevronRight },
    ]
  },
  {
    title: 'Modules',
    items: [
      { name: 'Recherche', href: '/docs/search', icon: Search },
      { name: 'Analyse', href: '/docs/analysis', icon: BarChart3 },
      { name: 'Produits Sauvegardes', href: '/docs/saved-products', icon: Bookmark },
      { name: 'Scheduler', href: '/docs/scheduler', icon: Bot },
      { name: 'Auto-Sourcing', href: '/docs/sourcing', icon: Package },
    ]
  },
  {
    title: 'Automatisation',
    items: [
      { name: 'Daily Review', href: '/docs/daily-review', icon: Sparkles },
    ]
  },
  {
    title: 'Reference',
    items: [
      { name: 'Glossaire', href: '/docs/glossary', icon: BookOpen },
      { name: 'Troubleshooting', href: '/docs/troubleshooting', icon: HelpCircle },
    ]
  }
]

export default function DocsLayout({ children, title, description, badge }: DocsLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-[calc(100vh-4rem)]">
      {/* Header Banner */}
      <div className="mb-8 flex items-center justify-between">
        <Link
          to="/dashboard"
          className="group inline-flex items-center gap-2 text-sm text-vault-text-secondary hover:text-vault-accent transition-all duration-200"
        >
          <span className="w-8 h-8 rounded-lg bg-vault-hover group-hover:bg-vault-accent-light flex items-center justify-center transition-colors">
            <ArrowLeft className="w-4 h-4 group-hover:text-vault-accent" />
          </span>
          <span className="group-hover:underline underline-offset-2">Retour a l'application</span>
        </Link>
        <div className="flex items-center gap-2 text-xs text-vault-text-secondary">
          <FileText className="w-4 h-4" />
          <span>Documentation v1.0</span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Navigation */}
        <aside className="lg:w-72 flex-shrink-0">
          <div className="lg:sticky lg:top-24">
            {/* Search placeholder for future */}
            <div className="hidden lg:block mb-6 p-3 bg-vault-bg rounded-xl border border-vault-border">
              <div className="flex items-center gap-2 text-vault-text-secondary text-sm">
                <Search className="w-4 h-4" />
                <span>Rechercher dans la doc...</span>
              </div>
            </div>

            <nav className="space-y-6 bg-vault-card lg:bg-transparent p-4 lg:p-0 rounded-xl lg:rounded-none border lg:border-0 border-vault-border">
              {docsSections.map((section) => (
                <div key={section.title}>
                  <h3 className="text-[11px] font-bold text-vault-text-secondary uppercase tracking-widest mb-3 px-3 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-vault-accent"></span>
                    {section.title}
                  </h3>
                  <ul className="space-y-1">
                    {section.items.map((item) => {
                      const isActive = location.pathname === item.href
                      const Icon = item.icon
                      return (
                        <li key={item.href}>
                          <Link
                            to={item.href}
                            className={`
                              relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm
                              transition-all duration-200 group
                              ${isActive
                                ? 'bg-vault-accent text-white font-medium shadow-vault-sm'
                                : 'text-vault-text hover:bg-vault-hover hover:translate-x-1'
                              }
                            `}
                          >
                            <span className={`
                              w-7 h-7 rounded-lg flex items-center justify-center transition-colors
                              ${isActive
                                ? 'bg-white/20'
                                : 'bg-vault-hover group-hover:bg-vault-accent-light'
                              }
                            `}>
                              <Icon className={`w-4 h-4 ${isActive ? '' : 'group-hover:text-vault-accent'}`} />
                            </span>
                            {item.name}
                            {isActive && (
                              <ChevronRight className="w-4 h-4 ml-auto" />
                            )}
                          </Link>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-md overflow-hidden">
            {/* Header with gradient accent */}
            <header className="relative px-6 lg:px-8 pt-8 pb-6 border-b border-vault-border bg-gradient-to-br from-vault-card to-vault-bg">
              {/* Decorative accent */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-vault-accent via-vault-accent-light to-transparent"></div>

              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl lg:text-3xl font-bold text-vault-text">
                      {title}
                    </h1>
                    {badge && (
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-vault-accent/10 text-vault-accent border border-vault-accent/20">
                        {badge}
                      </span>
                    )}
                  </div>
                  {description && (
                    <p className="text-vault-text-secondary max-w-2xl">
                      {description}
                    </p>
                  )}
                </div>
              </div>
            </header>

            {/* Content with better typography */}
            <article className="p-6 lg:p-8 prose prose-vault max-w-none">
              {children}
            </article>
          </div>
        </main>
      </div>
    </div>
  )
}
