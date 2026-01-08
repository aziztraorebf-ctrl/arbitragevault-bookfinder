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
    roi: { min_for_buy: 15, target_pct_default: 30, excellent_threshold: 50 },
    combined_score: { roi_weight: 0.6, velocity_weight: 0.4 },
    fees: { buffer_pct_default: 5 },
    velocity: { fast_threshold: 80, medium_threshold: 60, slow_threshold: 40 },
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
    expect(screen.getByText('Score combine')).toBeInTheDocument()
    expect(screen.getByText('Frais (buffer)')).toBeInTheDocument()
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

    // Find min_for_buy input and set invalid value (higher than target_pct_default which is 30)
    const inputs = document.querySelectorAll('input[type="number"]')
    const minForBuyInput = inputs[0] as HTMLInputElement

    fireEvent.change(minForBuyInput, { target: { value: '60' } }) // min > target (30)

    // Try to save
    const saveButtons = screen.getAllByText('Sauvegarder')
    fireEvent.click(saveButtons[0])

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Minimum pour achat doit etre inferieur a Cible')).toBeInTheDocument()
    })
  })
})
