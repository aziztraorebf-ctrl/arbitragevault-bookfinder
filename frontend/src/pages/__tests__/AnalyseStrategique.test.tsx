/**
 * Tests for AnalyseStrategique page
 * Phase 9 Senior Review - Gap 5
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the hooks
vi.mock('../../hooks/useStrategicViews', () => ({
  useStrategicView: vi.fn(),
}))

import AnalyseStrategique from '../AnalyseStrategique'
import { useStrategicView } from '../../hooks/useStrategicViews'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const mockViewData = {
  view_type: 'velocity',
  summary: {
    total_products: 150,
    avg_score: 7.5,
    recommendation: 'Bonne velocite globale',
  },
  metrics: {
    'Books': { score: 8.0, label: 'Excellent', description: 'High velocity', color: 'green' },
    'Electronics': { score: 5.0, label: 'Medium', description: 'Average velocity', color: 'yellow' },
  },
  calculated_at: '2025-01-01T12:00:00Z',
}

describe('AnalyseStrategique', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useStrategicView as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockViewData,
      isLoading: false,
      error: null,
    })
  })

  it('renders page title', () => {
    render(<AnalyseStrategique />, { wrapper: createWrapper() })
    expect(screen.getByText('Analyse Strategique')).toBeInTheDocument()
  })

  it('renders all 5 view tabs', () => {
    render(<AnalyseStrategique />, { wrapper: createWrapper() })

    expect(screen.getByText('Velocite')).toBeInTheDocument()
    expect(screen.getByText('Competition')).toBeInTheDocument()
    expect(screen.getByText('Volatilite')).toBeInTheDocument()
    expect(screen.getByText('Consistance')).toBeInTheDocument()
    expect(screen.getByText('Confiance')).toBeInTheDocument()
  })

  it('renders loading state', () => {
    ;(useStrategicView as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    })

    render(<AnalyseStrategique />, { wrapper: createWrapper() })
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders error state', () => {
    ;(useStrategicView as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('API Error'),
    })

    render(<AnalyseStrategique />, { wrapper: createWrapper() })
    expect(screen.getByText('Erreur')).toBeInTheDocument()
  })

  it('renders summary card with data', () => {
    render(<AnalyseStrategique />, { wrapper: createWrapper() })

    expect(screen.getByText('Resume')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument() // total_products
    expect(screen.getByText('7.5')).toBeInTheDocument() // avg_score
    expect(screen.getByText('Bonne velocite globale')).toBeInTheDocument()
  })

  it('renders metrics table', () => {
    render(<AnalyseStrategique />, { wrapper: createWrapper() })

    expect(screen.getByText('Metriques detaillees')).toBeInTheDocument()
    expect(screen.getByText('Books')).toBeInTheDocument()
    expect(screen.getByText('Electronics')).toBeInTheDocument()
  })

  it('switches views on tab click', async () => {
    render(<AnalyseStrategique />, { wrapper: createWrapper() })

    const competitionTab = screen.getByText('Competition')
    fireEvent.click(competitionTab)

    await waitFor(() => {
      expect(useStrategicView).toHaveBeenCalledWith('competition')
    })
  })

  it('renders empty state when no data', () => {
    ;(useStrategicView as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    })

    render(<AnalyseStrategique />, { wrapper: createWrapper() })
    expect(screen.getByText('Aucune donnee disponible pour cette vue.')).toBeInTheDocument()
  })
})
