/**
 * Tests for useStockEstimate hook
 * Phase 9 Senior Review - Gap fix
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the api service module
vi.mock('../../services/api', () => ({
  apiService: {
    getStockEstimate: vi.fn()
  }
}))

import { useStockEstimate } from '../useStockEstimate'
import { apiService } from '../../services/api'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useStockEstimate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not fetch when asin is empty', () => {
    const { result } = renderHook(
      () => useStockEstimate(''),
      { wrapper: createWrapper() }
    )

    // Query should be disabled (enabled: !!asin = false)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiService.getStockEstimate).not.toHaveBeenCalled()
  })

  it('does not fetch when asin is less than 10 chars', () => {
    const { result } = renderHook(
      () => useStockEstimate('B0SHORT'),
      { wrapper: createWrapper() }
    )

    // Query should be disabled (asin.length < 10)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiService.getStockEstimate).not.toHaveBeenCalled()
  })

  it('fetches when asin is valid (10+ chars)', async () => {
    const mockData = {
      asin: 'B08N5WRWNW',
      estimated_stock: 42,
      confidence: 'high',
      method: 'sales_rank',
      data_points: 10,
      range: { min: 30, max: 55 }
    }

    ;(apiService.getStockEstimate as ReturnType<typeof vi.fn>).mockResolvedValue(mockData)

    const { result } = renderHook(
      () => useStockEstimate('B08N5WRWNW'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockData)
    expect(apiService.getStockEstimate).toHaveBeenCalledWith('B08N5WRWNW')
  })

  it('handles 404 error without retrying', async () => {
    const error404 = Object.assign(new Error('Not found'), { status: 404 })
    ;(apiService.getStockEstimate as ReturnType<typeof vi.fn>).mockRejectedValue(error404)

    const { result } = renderHook(
      () => useStockEstimate('B0NOTFOUND1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    // Should only be called once (no retry on 404)
    expect(apiService.getStockEstimate).toHaveBeenCalledTimes(1)
  })
})
