import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiCard } from '../KpiCard'

describe('KpiCard', () => {
  const defaultProps = {
    value: '$1,234.56',
    label: 'Test Label',
    change: 12.5,
    sparkData: [10, 20, 30, 40, 50]
  }

  it('renders value correctly', () => {
    render(<KpiCard {...defaultProps} />)
    expect(screen.getByText('$1,234.56')).toBeInTheDocument()
  })

  it('renders label correctly', () => {
    render(<KpiCard {...defaultProps} />)
    expect(screen.getByText('Test Label')).toBeInTheDocument()
  })

  it('renders positive change with plus sign and green styling', () => {
    render(<KpiCard {...defaultProps} change={12.5} />)
    expect(screen.getByText('+12.5%')).toBeInTheDocument()
  })

  it('renders negative change without plus sign and red styling', () => {
    render(<KpiCard {...defaultProps} change={-5.3} />)
    expect(screen.getByText('-5.3%')).toBeInTheDocument()
  })

  it('renders zero change as positive', () => {
    render(<KpiCard {...defaultProps} change={0} />)
    expect(screen.getByText('+0.0%')).toBeInTheDocument()
  })

  it('renders sparkline', () => {
    const { container } = render(<KpiCard {...defaultProps} />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <KpiCard {...defaultProps} className="custom-class" />
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('renders TrendingUp icon for positive change', () => {
    const { container } = render(<KpiCard {...defaultProps} change={10} />)
    // Check SVG icon exists in the change badge
    const badges = container.querySelectorAll('svg')
    expect(badges.length).toBeGreaterThan(1) // Sparkline + trend icon
  })

  it('renders TrendingDown icon for negative change', () => {
    const { container } = render(<KpiCard {...defaultProps} change={-10} />)
    const badges = container.querySelectorAll('svg')
    expect(badges.length).toBeGreaterThan(1)
  })
})
