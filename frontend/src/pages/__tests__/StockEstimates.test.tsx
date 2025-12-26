/**
 * Tests for StockEstimates page
 * Phase 9 Senior Review - Gap 5
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the hooks
vi.mock('../../hooks/useStockEstimate', () => ({
  useStockEstimate: vi.fn(),
}))

import StockEstimates from '../StockEstimates'
import { useStockEstimate } from '../../hooks/useStockEstimate'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const mockStockData = {
  asin: 'B08N5WRWNW',
  estimated_stock: 42,
  confidence: 'high',
  method: 'sales_rank',
  data_points: 10,
  range: { min: 30, max: 55 },
  last_updated: '2025-01-01T12:00:00Z',
}

describe('StockEstimates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  it('renders page title', () => {
    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByText('Stock Estimates')).toBeInTheDocument()
  })

  it('renders ASIN input form', () => {
    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByLabelText('ASIN du produit')).toBeInTheDocument()
    expect(screen.getByText('Analyser')).toBeInTheDocument()
  })

  it('shows empty state before search', () => {
    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByText('Entrez un ASIN pour obtenir une estimation du stock FBA')).toBeInTheDocument()
  })

  it('validates ASIN format - rejects invalid format', async () => {
    render(<StockEstimates />, { wrapper: createWrapper() })

    const input = screen.getByLabelText('ASIN du produit')
    const button = screen.getByText('Analyser')

    // Enter invalid ASIN (doesn't start with B0)
    fireEvent.change(input, { target: { value: 'INVALIDASIN' } })
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Format ASIN invalide/)).toBeInTheDocument()
    })
  })

  it('validates ASIN format - accepts valid B0 format', async () => {
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockStockData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })

    const input = screen.getByLabelText('ASIN du produit')
    const button = screen.getByText('Analyser')

    fireEvent.change(input, { target: { value: 'B08N5WRWNW' } })
    fireEvent.click(button)

    // Should not show format error
    await waitFor(() => {
      expect(screen.queryByText(/Format ASIN invalide/)).not.toBeInTheDocument()
    })
  })

  it('renders loading state', () => {
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders error state', () => {
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('API Error'),
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByText('Erreur')).toBeInTheDocument()
  })

  it('renders 404 error with specific message', () => {
    const error404 = Object.assign(new Error('Not found'), { status: 404 })
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: error404,
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByText('ASIN non trouve dans la base de donnees')).toBeInTheDocument()
  })

  it('renders stock data results', () => {
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockStockData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })

    expect(screen.getByText('42')).toBeInTheDocument() // estimated_stock
    expect(screen.getByText('high')).toBeInTheDocument() // confidence
    expect(screen.getByText('30 - 55')).toBeInTheDocument() // range
    expect(screen.getByText('10')).toBeInTheDocument() // data_points
  })

  it('has refresh button', () => {
    ;(useStockEstimate as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockStockData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(<StockEstimates />, { wrapper: createWrapper() })
    expect(screen.getByText('Rafraichir')).toBeInTheDocument()
  })
})
