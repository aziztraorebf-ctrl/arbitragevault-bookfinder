// SearchBar - Elegant rounded search input
import { Search } from 'lucide-react'

interface SearchBarProps {
  placeholder?: string
  className?: string
}

export function SearchBar({
  placeholder = "Search books, ISBN, authors...",
  className = ''
}: SearchBarProps) {
  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-muted" />
      <input
        type="text"
        placeholder={placeholder}
        className="
          w-full h-10 pl-11 pr-4
          bg-vault-bg border border-vault-border
          rounded-full text-sm text-vault-text font-sans
          placeholder:text-vault-text-muted
          focus:outline-none focus:ring-2 focus:ring-vault-accent focus:border-transparent
          hover:border-vault-accent/50
          transition-all duration-200
        "
      />
    </div>
  )
}
