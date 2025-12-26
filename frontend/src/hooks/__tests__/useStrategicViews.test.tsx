/**
 * Tests for useStrategicViews hooks
 * Phase 9 Senior Review - Gap 6
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the api service module
vi.mock('../../services/api', () => ({
  apiService: {
    getAllStrategicViews: vi.fn(),
    getStrategicView: vi.fn(),
    getTargetPrices: vi.fn(),
  }
}))

import { useAllStrategicViews, useStrategicView, useTargetPrices } from '../useStrategicViews'
import { apiService } from '../../services/api'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const mockAllViews = {
  views: ['velocity', 'competition', 'volatility', 'consistency', 'confidence'],
}

const mockViewData = {
  view_type: 'velocity',
  summary: {
    total_products: 150,
    avg_score: 7.5,
    recommendation: 'Good velocity',
  },
  metrics: {
    'Books': { score: 8.0, label: 'Excellent', description: 'High', color: 'green' },
  },
  calculated_at: '2025-01-01T12:00:00Z',
}

const mockTargetPrices = {
  view_type: 'velocity',
  products: [
    { asin: 'B08N5WRWNW', title: 'Test', current_price: 20, target_price: 15, expected_roi: 30, confidence: 0.8 },
  ],
}

describe('useAllStrategicViews', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches all strategic views', async () => {
    ;(apiService.getAllStrategicViews as ReturnType<typeof vi.fn>).mockResolvedValue(mockAllViews)

    const { result } = renderHook(
      () => useAllStrategicViews(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getAllStrategicViews).toHaveBeenCalled()
    expect(result.current.data).toEqual(mockAllViews)
  })

  // Note: Error handling with custom retry logic is tested in useProductDecision.test.tsx
  // The retry function checks error instanceof ApiError, which is hard to mock properly
})

describe('useStrategicView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches specific view type', async () => {
    ;(apiService.getStrategicView as ReturnType<typeof vi.fn>).mockResolvedValue(mockViewData)

    const { result } = renderHook(
      () => useStrategicView('velocity'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getStrategicView).toHaveBeenCalledWith('velocity', undefined)
    expect(result.current.data).toEqual(mockViewData)
  })

  it('fetches view with niches filter', async () => {
    ;(apiService.getStrategicView as ReturnType<typeof vi.fn>).mockResolvedValue(mockViewData)

    const { result } = renderHook(
      () => useStrategicView('velocity', ['Books', 'Electronics']),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getStrategicView).toHaveBeenCalledWith('velocity', ['Books', 'Electronics'])
  })

  it('does not fetch when viewType is empty', () => {
    const { result } = renderHook(
      () => useStrategicView('' as 'velocity'),
      { wrapper: createWrapper() }
    )

    // Query should be disabled
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiService.getStrategicView).not.toHaveBeenCalled()
  })
})

describe('useTargetPrices', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches target prices for view type', async () => {
    ;(apiService.getTargetPrices as ReturnType<typeof vi.fn>).mockResolvedValue(mockTargetPrices)

    const { result } = renderHook(
      () => useTargetPrices('velocity'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getTargetPrices).toHaveBeenCalledWith('velocity')
    expect(result.current.data).toEqual(mockTargetPrices)
  })

  it('does not fetch when viewType is empty', () => {
    const { result } = renderHook(
      () => useTargetPrices('' as 'velocity'),
      { wrapper: createWrapper() }
    )

    expect(result.current.fetchStatus).toBe('idle')
    expect(apiService.getTargetPrices).not.toHaveBeenCalled()
  })
})
