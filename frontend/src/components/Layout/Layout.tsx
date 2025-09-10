import { useState } from 'react'
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

const navigation = [
  { name: 'Dashboard', icon: Home, href: '/', active: true },
  { name: 'Analyse manuelle', icon: Upload, href: '/manual-analysis' },
  { name: 'Niche Discovery', icon: Search, href: '/niche-discovery' },
  { name: 'Mes Niches', icon: BookMarked, href: '/my-niches' },
  { name: 'AutoScheduler', icon: Bot, href: '/autoscheduler' },
  { name: 'AutoSourcing', icon: BarChart3, href: '/autosourcing' },
  { name: 'Analyse Stratégique', icon: TrendingUp, href: '/strategic-analysis' },
  { name: 'Stock Estimates', icon: Package, href: '/stock-estimates' },
  { name: 'Configuration', icon: Settings, href: '/settings' },
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-100">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 gradient-bg rounded-lg flex items-center justify-center">
              <div className="w-4 h-4 bg-white rounded-sm"></div>
            </div>
            <span className="text-xl font-bold text-gray-900">ArbitrageVault</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-md text-gray-500 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.name}
                className={`
                  w-full flex items-center space-x-3 px-3 py-3 text-left rounded-xl transition-colors duration-200
                  ${item.active 
                    ? 'gradient-bg text-white shadow-lg' 
                    : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-100">
          <div className="flex items-center justify-between h-16 px-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700"
              >
                <Menu className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard principal</h1>
            </div>

            <div className="flex items-center space-x-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Rechercher..."
                  className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              </div>
              
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
                <span className="text-sm font-medium text-gray-700">Utilisateur</span>
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