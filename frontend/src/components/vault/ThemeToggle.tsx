// ThemeToggle - Elegant sun/moon toggle for dark mode
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative w-10 h-10 flex items-center justify-center
        rounded-full transition-all duration-300 ease-out
        hover:bg-vault-hover
        focus:outline-none focus-visible:ring-2 focus-visible:ring-vault-accent focus-visible:ring-offset-2
        ${className}
      `}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <div className="relative w-5 h-5">
        {/* Sun icon */}
        <Sun
          className={`
            absolute inset-0 w-5 h-5 text-vault-text
            transition-all duration-300 ease-out
            ${isDark ? 'opacity-0 rotate-90 scale-0' : 'opacity-100 rotate-0 scale-100'}
          `}
        />
        {/* Moon icon */}
        <Moon
          className={`
            absolute inset-0 w-5 h-5 text-vault-text
            transition-all duration-300 ease-out
            ${isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'}
          `}
        />
      </div>
    </button>
  )
}
