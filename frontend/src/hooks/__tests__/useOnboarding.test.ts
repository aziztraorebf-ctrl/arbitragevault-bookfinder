import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useOnboarding } from '../useOnboarding'

// localStorage key used by the hook
const ONBOARDING_KEY = 'arbitragevault_onboarding_complete'

describe('useOnboarding', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should show wizard when localStorage is empty (new user)', async () => {
    const { result } = renderHook(() => useOnboarding())

    // Wait for useEffect to complete
    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.showWizard).toBe(true)
  })

  it('should hide wizard when onboarding is already completed', async () => {
    // Pre-set localStorage to simulate returning user
    localStorage.setItem(ONBOARDING_KEY, 'true')

    const { result } = renderHook(() => useOnboarding())

    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.showWizard).toBe(false)
  })

  it('should complete onboarding and hide wizard', async () => {
    const { result } = renderHook(() => useOnboarding())

    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.showWizard).toBe(true)

    act(() => {
      result.current.completeOnboarding()
    })

    expect(result.current.showWizard).toBe(false)
    expect(localStorage.getItem(ONBOARDING_KEY)).toBe('true')
  })

  it('should reset onboarding and show wizard again', async () => {
    // Start with completed onboarding
    localStorage.setItem(ONBOARDING_KEY, 'true')

    const { result } = renderHook(() => useOnboarding())

    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.showWizard).toBe(false)

    act(() => {
      result.current.resetOnboarding()
    })

    expect(result.current.showWizard).toBe(true)
    expect(localStorage.getItem(ONBOARDING_KEY)).toBeNull()
  })

  it('should handle localStorage errors gracefully (private browsing)', async () => {
    // Mock localStorage to throw an error (simulates private browsing)
    const originalGetItem = localStorage.getItem
    const originalSetItem = localStorage.setItem

    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('localStorage is not available')
    })

    const { result } = renderHook(() => useOnboarding())

    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Should skip wizard when localStorage fails (defensive behavior)
    expect(result.current.showWizard).toBe(false)

    // Restore mocks
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(originalGetItem)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(originalSetItem)
  })

  it('should transition from loading to loaded state', async () => {
    const { result } = renderHook(() => useOnboarding())

    // After useEffect completes, isLoading should be false
    await vi.waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // showWizard should have a defined value (either true or false)
    expect(typeof result.current.showWizard).toBe('boolean')
  })
})
