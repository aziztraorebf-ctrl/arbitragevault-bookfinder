import { useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import { 
  Home, 
  Upload, 
  Search, 
  BookMarked, 
  Bot, 
  BarChart3, 
  TrendingUp, 
  Package,
  Settings,
  Menu,
  X
} from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

const navigationSections = [
  {
    title: "🔍 Analyse",
    items: [
      { name: 'Dashboard', icon: Home, href: '/', description: 'Vue d\'ensemble générale' },
      { name: 'Analyse manuelle', icon: Upload, href: '/manual-analysis', description: 'Upload CSV et ASINs' },
      { name: 'Niche Discovery', icon: Search, href: '/niche-discovery', description: 'Découverte automatique' },
      { name: 'Mes Niches', icon: BookMarked, href: '/my-niches', description: 'Niches sauvegardées' },
    ]
  },
  {
    title: "⚙️ Automatisation", 
    items: [
      { name: 'AutoScheduler', icon: Bot, href: '/autoscheduler', description: 'Automatisation tâches' },
      { name: 'AutoSourcing', icon: BarChart3, href: '/autosourcing', description: 'Recherche produits' },
      { name: 'Analyse Stratégique', icon: TrendingUp, href: '/strategic-analysis', description: '5 vues d\'analyse' },
    ]
  },
  {
    title: "📦 Gestion",
    items: [
      { name: 'Stock Estimates', icon: Package, href: '/stock-estimates', description: 'Vérification stock' },
    ]
  },
  {
    title: "🔧 Système",
    items: [
      { name: 'Configuration', icon: Settings, href: '/settings', description: 'Paramètres système' },
    ]
  }
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 lg:w-sidebar-large
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-20 px-8 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 gradient-bg rounded-xl flex items-center justify-center">
              <div className="w-6 h-6 bg-white rounded-lg"></div>
            </div>
            <span className="text-2xl font-bold text-gray-900">ArbitrageVault</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="flex-1 px-8 py-8 space-y-8">
          {navigationSections.map((section, sectionIndex) => (
            <div key={section.title}>
              <div className="typography-secondary uppercase tracking-wide mb-4 px-2">
                {section.title}
              </div>
              <div className="space-y-2">
                {section.items.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`
                        w-full flex items-center space-x-4 px-6 py-4 text-left rounded-xl transition-all duration-200 hover:transform hover:translateX-1
                        ${isActive 
                          ? 'gradient-bg text-white shadow-lg' 
                          : 'text-gray-700 hover:bg-gray-50 hover:shadow-sm'
                        }
                      `}
                    >
                      <Icon className="w-6 h-6" />
                      <div className="flex-1">
                        <div className="typography-h3" style={{fontWeight: 600, color: isActive ? 'white' : '#111827'}}>{item.name}</div>
                        <div className={`typography-secondary mt-1 ${
                          isActive ? 'text-blue-100' : ''
                        }`}>
                          {item.description}
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>
              {sectionIndex < navigationSections.length - 1 && (
                <div className="border-t border-gray-200 mt-6"></div>
              )}
            </div>
          ))}
          

        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-100">
          <div className="flex items-center justify-between h-20 px-8">
            <div className="flex items-center space-x-6">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700"
              >
                <Menu className="w-6 h-6" />
              </button>
              <h1 className="typography-h1">Dashboard principal</h1>
              <div className="typography-secondary ml-6">
                Mercredi Septembre 9
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="relative">
                <input
                  type="text"
                  placeholder="10 activités"
                  className="pl-12 pr-6 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 text-base w-48"
                />
                <Search className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-500 rounded-full"></div>
                <span className="text-base font-medium text-gray-700">1</span>
                <div className="w-10 h-10 bg-gray-300 rounded-full ml-2"></div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}