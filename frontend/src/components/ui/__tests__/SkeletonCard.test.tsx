import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SkeletonCard } from '../SkeletonCard'

describe('SkeletonCard', () => {
  it('renders with default props', () => {
    const { container } = render(<SkeletonCard />)

    const card = container.firstChild as HTMLElement
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('bg-white', 'shadow-md', 'rounded-xl', 'p-6', 'animate-pulse')
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonCard className="w-full max-w-md" />)

    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('w-full', 'max-w-md')
    // Should still have base classes
    expect(card).toHaveClass('animate-pulse')
  })

  it('renders skeleton placeholder elements', () => {
    const { container } = render(<SkeletonCard />)

    // Should have multiple gray placeholder divs
    const placeholders = container.querySelectorAll('.bg-gray-200')
    expect(placeholders.length).toBeGreaterThanOrEqual(3)
  })

  it('has proper structure for KPI card skeleton', () => {
    const { container } = render(<SkeletonCard />)

    // Icon placeholder (w-6 h-6)
    const iconPlaceholder = container.querySelector('.w-6.h-6')
    expect(iconPlaceholder).toBeInTheDocument()

    // Value placeholder (h-8)
    const valuePlaceholder = container.querySelector('.h-8')
    expect(valuePlaceholder).toBeInTheDocument()
  })
})
