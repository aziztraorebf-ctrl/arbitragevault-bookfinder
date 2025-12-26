/**
 * Tests for useConfig hooks
 * Phase 9 Senior Review - Gap 6
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the api service module
vi.mock('../../services/api', () => ({
  apiService: {
    getConfig: vi.fn(),
    getConfigStats: vi.fn(),
    updateConfig: vi.fn(),
  }
}))

import { useEffectiveConfig, useConfigStats, useUpdateConfig } from '../useConfig'
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

const mockConfig = {
  scope: 'global',
  effective_config: {
    roi_thresholds: { minimum: 15, target: 30, excellent: 50 },
    bsr_limits: { max_acceptable: 500000, ideal_max: 100000 },
  },
  version: 1,
  updated_at: '2025-01-01T00:00:00Z',
}

const mockStats = {
  total_configs: 5,
  by_scope: { global: 1, domain: 4 },
  cache_status: 'hit',
  last_updated: '2025-01-01T00:00:00Z',
}

describe('useEffectiveConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches config with default parameters', async () => {
    ;(apiService.getConfig as ReturnType<typeof vi.fn>).mockResolvedValue(mockConfig)

    const { result } = renderHook(
      () => useEffectiveConfig(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getConfig).toHaveBeenCalledWith(1, 'books')
    expect(result.current.data).toEqual(mockConfig)
  })

  it('fetches config with custom domain and category', async () => {
    ;(apiService.getConfig as ReturnType<typeof vi.fn>).mockResolvedValue(mockConfig)

    const { result } = renderHook(
      () => useEffectiveConfig(2, 'electronics'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getConfig).toHaveBeenCalledWith(2, 'electronics')
  })

  // Note: Error handling with custom retry logic is tested in useProductDecision.test.tsx
  // The retry function checks error instanceof ApiError, which is hard to mock properly
})

describe('useConfigStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches config stats', async () => {
    ;(apiService.getConfigStats as ReturnType<typeof vi.fn>).mockResolvedValue(mockStats)

    const { result } = renderHook(
      () => useConfigStats(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(apiService.getConfigStats).toHaveBeenCalled()
    expect(result.current.data).toEqual(mockStats)
  })
})

describe('useUpdateConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls updateConfig API on mutation', async () => {
    const updatedConfig = { ...mockConfig, version: 2 }
    ;(apiService.updateConfig as ReturnType<typeof vi.fn>).mockResolvedValue(updatedConfig)

    const { result } = renderHook(
      () => useUpdateConfig(),
      { wrapper: createWrapper() }
    )

    await result.current.mutateAsync({
      scope: 'global',
      request: { config: { roi_thresholds: { minimum: 20 } } }
    })

    expect(apiService.updateConfig).toHaveBeenCalledWith('global', {
      config: { roi_thresholds: { minimum: 20 } }
    })
  })
})
