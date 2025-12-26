/**
 * Tests for useProductDecision hook
 * Phase 8 Senior Review
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the api service module
vi.mock('../../services/api', () => ({
  apiService: {
    getProductDecision: vi.fn()
  },
  ApiError: class ApiError extends Error {
    status?: number
    constructor(message: string, status?: number) {
      super(message)
      this.status = status
    }
  }
}))

import { useProductDecision } from '../useProductDecision'
import { apiService } from '../../services/api'

const createWrapper = (options = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        ...options,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useProductDecision', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading state initially when asin provided', async () => {
    ;(apiService.getProductDecision as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves - stays loading
    )

    const { result } = renderHook(
      () => useProductDecision('TEST123'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()
  })

  it('returns data on successful API call', async () => {
    const mockData = {
      asin: 'TEST123',
      title: 'Test Book',
      recommendation: { recommendation: 'BUY', confidence_percent: 75 },
      velocity: { velocity_score: 80 },
      risk: { risk_score: 30, risk_level: 'LOW' }
    }

    ;(apiService.getProductDecision as any).mockResolvedValue(mockData)

    const { result } = renderHook(
      () => useProductDecision('TEST123'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.data?.recommendation.recommendation).toBe('BUY')
  })

  it('handles API error correctly', async () => {
    const apiError = new Error('API Error')
    ;(apiService.getProductDecision as any).mockRejectedValue(apiError)

    const { result } = renderHook(
      () => useProductDecision('TEST123'),
      { wrapper: createWrapper() }
    )

    // Wait for the query to finish all retries and reach error state
    // The hook retries up to 2 times with exponential backoff: 1s, 2s
    // Total wait: initial + retry1 (1s) + retry2 (2s) = ~3.5s
    await waitFor(
      () => {
        expect(result.current.isError).toBe(true)
      },
      { timeout: 6000, interval: 200 }
    )

    expect(result.current.error).toBeDefined()
  })

  it('does not fetch when asin is empty', () => {
    const { result } = renderHook(
      () => useProductDecision(''),  // Empty ASIN
      { wrapper: createWrapper() }
    )

    // Should not be loading because query is disabled (enabled: !!asin = false)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiService.getProductDecision).not.toHaveBeenCalled()
  })
})
