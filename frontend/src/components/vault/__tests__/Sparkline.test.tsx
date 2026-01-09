import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Sparkline } from '../Sparkline'

describe('Sparkline', () => {
  it('renders SVG with valid data', () => {
    const data = [10, 20, 30, 40, 50]
    const { container } = render(<Sparkline data={data} />)

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('returns null with less than 2 data points', () => {
    const { container } = render(<Sparkline data={[10]} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null with empty data', () => {
    const { container } = render(<Sparkline data={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders polyline for the data', () => {
    const data = [10, 20, 30]
    const { container } = render(<Sparkline data={data} />)

    const polyline = container.querySelector('polyline')
    expect(polyline).toBeInTheDocument()
    expect(polyline).toHaveAttribute('points')
  })

  it('renders end dot circle', () => {
    const data = [10, 20, 30]
    const { container } = render(<Sparkline data={data} />)

    const circle = container.querySelector('circle')
    expect(circle).toBeInTheDocument()
  })

  it('applies custom dimensions', () => {
    const { container } = render(
      <Sparkline data={[10, 20, 30]} width={100} height={50} />
    )

    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', '100')
    expect(svg).toHaveAttribute('height', '50')
  })

  it('applies custom className', () => {
    const { container } = render(
      <Sparkline data={[10, 20, 30]} className="custom-class" />
    )

    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('custom-class')
  })

  it('handles flat data (all same values)', () => {
    const data = [50, 50, 50, 50]
    const { container } = render(<Sparkline data={data} />)

    const polyline = container.querySelector('polyline')
    expect(polyline).toBeInTheDocument()
  })
})
