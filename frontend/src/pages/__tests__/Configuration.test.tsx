/**
 * Tests for Configuration page
 * Phase 9 Senior Review - Gap 5
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the hooks
vi.mock('../../hooks/useConfig', () => ({
  useEffectiveConfig: vi.fn(),
  useConfigStats: vi.fn(),
  useUpdateConfig: vi.fn(),
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

import Configuration from '../Configuration'
import { useEffectiveConfig, useConfigStats, useUpdateConfig } from '../../hooks/useConfig'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const mockConfig = {
  effective_config: {
    roi_thresholds: { minimum: 15, target: 30, excellent: 50 },
    bsr_limits: { max_acceptable: 500000, ideal_max: 100000 },
    pricing: { min_profit_margin: 20, fee_estimate_percent: 15 },
    velocity: { min_score: 5, weight_in_scoring: 0.3 },
  },
}

const mockStats = {
  total_configs: 5,
  cache_status: 'hit',
  last_updated: '2025-01-01T00:00:00Z',
}

describe('Configuration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useEffectiveConfig as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockConfig,
      isLoading: false,
      error: null,
    })
    ;(useConfigStats as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockStats,
    })
    ;(useUpdateConfig as ReturnType<typeof vi.fn>).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    })
  })

  it('renders page title', () => {
    render(<Configuration />, { wrapper: createWrapper() })
    expect(screen.getByText('Configuration')).toBeInTheDocument()
  })

  it('renders loading state', () => {
    ;(useEffectiveConfig as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    })

    render(<Configuration />, { wrapper: createWrapper() })
    // Check for skeleton loader
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders error state', () => {
    ;(useEffectiveConfig as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('API Error'),
    })

    render(<Configuration />, { wrapper: createWrapper() })
    expect(screen.getByText('Erreur de chargement')).toBeInTheDocument()
  })

  it('renders config sections', () => {
    render(<Configuration />, { wrapper: createWrapper() })

    expect(screen.getByText('Seuils ROI')).toBeInTheDocument()
    expect(screen.getByText('Limites BSR')).toBeInTheDocument()
    expect(screen.getByText('Tarification')).toBeInTheDocument()
    expect(screen.getByText('Velocite')).toBeInTheDocument()
  })

  it('renders stats card', () => {
    render(<Configuration />, { wrapper: createWrapper() })

    expect(screen.getByText('Statistiques')).toBeInTheDocument()
    // Stats values are rendered - check for content structure
    expect(screen.getByText(/Configs totales/)).toBeInTheDocument()
    expect(screen.getByText(/Cache/)).toBeInTheDocument()
  })

  it('toggles edit mode', () => {
    render(<Configuration />, { wrapper: createWrapper() })

    const editButton = screen.getByText('Modifier')
    fireEvent.click(editButton)

    expect(screen.getByText('Annuler')).toBeInTheDocument()
    // Should show save buttons in edit mode
    expect(screen.getAllByText('Sauvegarder').length).toBeGreaterThan(0)
  })

  it('validates ROI thresholds coherence', async () => {
    render(<Configuration />, { wrapper: createWrapper() })

    // Enter edit mode
    fireEvent.click(screen.getByText('Modifier'))

    // Find minimum input and set invalid value (higher than target)
    const inputs = document.querySelectorAll('input[type="number"]')
    const minimumInput = inputs[0] as HTMLInputElement

    fireEvent.change(minimumInput, { target: { value: '60' } }) // min > target (30)

    // Try to save
    const saveButtons = screen.getAllByText('Sauvegarder')
    fireEvent.click(saveButtons[0])

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Minimum doit etre inferieur a Cible')).toBeInTheDocument()
    })
  })
})
