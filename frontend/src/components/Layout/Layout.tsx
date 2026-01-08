import { useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import { Menu, X } from 'lucide-react'
import { useMobileMenu } from '../../hooks/useMobileMenu'

interface LayoutProps {
  children: ReactNode
}

// Navigation items avec emojis
const navigationItems = [
  { name: 'Dashboard', emoji: '🏠', href: '/dashboard' },
  { name: 'Analyse Manuelle', emoji: '📋', href: '/analyse' },
  { name: 'Niche Discovery', emoji: '🔍', href: '/niche-discovery' },
  { name: 'Mes Niches', emoji: '📚', href: '/mes-niches' },
  { name: 'AutoScheduler', emoji: '🤖', href: '/autoscheduler' },
  { name: 'AutoSourcing', emoji: '📊', href: '/autosourcing' },
  { name: 'Mes Recherches', emoji: '🔖', href: '/recherches' },
  { name: 'Configuration', emoji: '⚙️', href: '/config' }
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { isOpen, toggle, close } = useMobileMenu()

  // Close sidebar on route change
  useEffect(() => {
    close()
  }, [location.pathname, close])

  return (
    <div className="flex min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-50">
        <div className="flex items-center justify-between h-full px-6">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="text-xl font-bold text-gray-900">ArbitrageVault</span>
          </div>

          {/* Hamburger menu - visible on mobile only */}
          <button
            onClick={toggle}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-100 md:hidden"
            aria-label={isOpen ? 'Close menu' : 'Open menu'}
          >
            {isOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile backdrop */}
      {isOpen && (
        <div
          data-testid="mobile-backdrop"
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={close}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed left-0 top-16 bottom-0 w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto z-40
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
        data-state={isOpen ? 'open' : 'closed'}
      >
        <nav className="py-4 px-3">
          <div className="space-y-2">
            {navigationItems.map((item, index) => {
              const isActive = location.pathname === item.href ||
                             (item.href === '/dashboard' && location.pathname === '/')

              return (
                <div key={item.href}>
                  <Link
                    to={item.href}
                    onClick={close}
                    className={`
                      flex items-center space-x-3 px-4 py-3 rounded-md
                      transition-all duration-100
                      ${isActive
                        ? 'bg-blue-100 font-semibold text-blue-700'
                        : 'text-gray-700 hover:bg-blue-50'
                      }
                    `}
                  >
                    <span className="text-xl">{item.emoji}</span>
                    <span className="text-sm">{item.name}</span>
                  </Link>

                  {/* Separators after specific groups */}
                  {(index === 3 || index === 5) && (
                    <div className="my-2 border-t border-gray-200"></div>
                  )}
                </div>
              )
            })}
          </div>
        </nav>
      </aside>

      {/* Main content area */}
      <div className="flex-1 ml-0 md:ml-64 mt-16 overflow-x-hidden">
        <main className="p-2 sm:p-4 md:p-8 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
