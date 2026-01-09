import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ActionCard } from '../ActionCard'
import type { ActionCardData } from '../../../data/mockDashboard'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

describe('ActionCard', () => {
  const defaultProps: ActionCardData = {
    id: '1',
    title: 'Test Card',
    icon: 'BookOpen',
    lines: ['Line 1', 'Line 2', 'Line 3'],
    action: { label: 'Click Me', href: '/test' }
  }

  const renderWithRouter = (props: ActionCardData) => {
    return render(
      <BrowserRouter>
        <ActionCard {...props} />
      </BrowserRouter>
    )
  }

  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('renders title', () => {
    renderWithRouter(defaultProps)
    expect(screen.getByText('Test Card')).toBeInTheDocument()
  })

  it('renders all description lines', () => {
    renderWithRouter(defaultProps)
    expect(screen.getByText('Line 1')).toBeInTheDocument()
    expect(screen.getByText('Line 2')).toBeInTheDocument()
    expect(screen.getByText('Line 3')).toBeInTheDocument()
  })

  it('renders action button', () => {
    renderWithRouter(defaultProps)
    expect(screen.getByText('Click Me')).toBeInTheDocument()
  })

  it('navigates when action button clicked with href', () => {
    renderWithRouter(defaultProps)
    const button = screen.getByText('Click Me')
    fireEvent.click(button)
    expect(mockNavigate).toHaveBeenCalledWith('/test')
  })

  it('renders BookOpen icon', () => {
    const { container } = renderWithRouter(defaultProps)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThan(0)
  })

  it('renders Bell icon', () => {
    const props = { ...defaultProps, icon: 'Bell' as const }
    const { container } = renderWithRouter(props)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThan(0)
  })

  it('renders FileText icon', () => {
    const props = { ...defaultProps, icon: 'FileText' as const }
    const { container } = renderWithRouter(props)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThan(0)
  })

  it('applies custom className', () => {
    const { container } = render(
      <BrowserRouter>
        <ActionCard {...defaultProps} className="custom-class" />
      </BrowserRouter>
    )
    // The custom class is applied to the root container
    expect(container.querySelector('.custom-class')).toBeInTheDocument()
  })

  it('handles action without href', () => {
    const props: ActionCardData = {
      ...defaultProps,
      action: { label: 'No Navigate' }
    }
    renderWithRouter(props)
    const button = screen.getByText('No Navigate')
    fireEvent.click(button)
    // Should not navigate if no href
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})
