// Layout - Vault Elegance Design System
// Premium sidebar navigation with collapsible behavior
import { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import {
  Menu,
  X,
  LayoutDashboard,
  Bot,
  Package,
  Settings,
  BookOpen
} from 'lucide-react'
import { ThemeToggle, SearchBar } from '../vault'
import { USER_CONFIG } from '../../config/user'

interface LayoutProps {
  children: ReactNode
}

const navigationItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { type: 'separator' as const },
  { name: 'Sourcing', icon: Package, href: '/autosourcing' },
  { name: 'Scheduler', icon: Bot, href: '/autoscheduler' },
  { type: 'separator' as const },
  { name: 'Settings', icon: Settings, href: '/config' },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSidebarHovered, setIsSidebarHovered] = useState(false)

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isMobileMenuOpen])

  const sidebarExpanded = isSidebarHovered || isMobileMenuOpen

  return (
    <div className="min-h-screen bg-vault-bg font-sans">
      {/* ========================================
          HEADER
          ======================================== */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-vault-card border-b border-vault-border z-50">
        <div className="flex items-center justify-between h-full px-4 lg:px-6">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-vault-accent rounded-xl flex items-center justify-center shadow-vault-sm">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl tracking-tight hidden sm:block">
              <span className="font-normal text-vault-text">Arbitrage</span>
              <span className="font-bold text-vault-text">Vault</span>
            </span>
          </div>

          {/* Center: Search (hidden on mobile) */}
          <div className="hidden lg:block flex-1 max-w-md mx-8">
            <SearchBar />
          </div>

          {/* Right: Theme toggle + Avatar + Mobile menu */}
          <div className="flex items-center gap-2">
            <ThemeToggle />

            {/* Avatar */}
            <div className="w-10 h-10 rounded-full bg-vault-accent/10 border-2 border-vault-accent flex items-center justify-center overflow-hidden">
              <span className="text-sm font-semibold text-vault-accent">{USER_CONFIG.initials}</span>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-xl hover:bg-vault-hover transition-colors duration-150 lg:hidden"
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6 text-vault-text" />
              ) : (
                <Menu className="w-6 h-6 text-vault-text" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ========================================
          MOBILE BACKDROP
          ======================================== */}
      <div
        className={`
          fixed inset-0 bg-black/50 z-30 lg:hidden
          transition-opacity duration-300
          ${isMobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
        `}
        onClick={() => setIsMobileMenuOpen(false)}
        aria-hidden="true"
      />

      {/* ========================================
          SIDEBAR
          ======================================== */}
      <aside
        onMouseEnter={() => setIsSidebarHovered(true)}
        onMouseLeave={() => setIsSidebarHovered(false)}
        className={`
          fixed left-0 top-16 bottom-0 bg-vault-sidebar border-r border-vault-border z-40
          transition-all duration-300 ease-out
          ${isMobileMenuOpen
            ? 'w-64 translate-x-0'
            : '-translate-x-full lg:translate-x-0'
          }
          ${sidebarExpanded ? 'lg:w-64' : 'lg:w-[72px]'}
        `}
      >
        <nav className="h-full py-4 px-2 overflow-y-auto overflow-x-hidden">
          <div className="space-y-1">
            {navigationItems.map((item, index) => {
              if (item.type === 'separator') {
                return (
                  <div
                    key={`sep-${index}`}
                    className="my-3 mx-3 border-t border-vault-border"
                  />
                )
              }

              const isActive =
                location.pathname === item.href ||
                (item.href === '/dashboard' && location.pathname === '/')
              const Icon = item.icon!

              return (
                <Link
                  key={item.href}
                  to={item.href!}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`
                    relative flex items-center gap-3 px-3 py-3 rounded-xl
                    transition-all duration-150 group
                    ${isActive
                      ? 'bg-vault-accent-light text-vault-accent'
                      : 'text-vault-text-secondary hover:bg-vault-hover hover:text-vault-text'
                    }
                  `}
                >
                  {/* Active indicator bar */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-8 bg-vault-accent rounded-r-full" />
                  )}

                  <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-vault-accent' : ''}`} />

                  <span
                    className={`
                      text-sm font-medium whitespace-nowrap
                      transition-all duration-200
                      ${sidebarExpanded ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-2 lg:opacity-0'}
                    `}
                  >
                    {item.name}
                  </span>

                  {/* Tooltip for collapsed state */}
                  {!sidebarExpanded && (
                    <div className="
                      absolute left-full ml-2 px-2 py-1
                      bg-vault-card border border-vault-border rounded-lg shadow-vault-md
                      text-sm font-medium text-vault-text whitespace-nowrap
                      opacity-0 invisible group-hover:opacity-100 group-hover:visible
                      transition-all duration-150
                      hidden lg:block
                    ">
                      {item.name}
                    </div>
                  )}
                </Link>
              )
            })}
          </div>
        </nav>
      </aside>

      {/* ========================================
          MAIN CONTENT
          ======================================== */}
      <main
        className={`
          pt-16 min-h-screen
          transition-all duration-300 ease-out
          ${sidebarExpanded ? 'lg:ml-64' : 'lg:ml-[72px]'}
        `}
      >
        <div className="p-4 md:p-6 lg:p-8 max-w-[1400px]">
          {children}
        </div>
      </main>
    </div>
  )
}
