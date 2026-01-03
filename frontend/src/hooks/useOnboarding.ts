import { useState, useEffect } from 'react'

/**
 * localStorage key for onboarding completion state.
 * Stores 'true' when user completes or skips the welcome wizard.
 */
const ONBOARDING_KEY = 'arbitragevault_onboarding_complete'

/**
 * Hook to manage onboarding/welcome wizard state.
 * Persists completion state in localStorage.
 *
 * @returns {Object} Onboarding state and controls
 * - showWizard: Whether to display the welcome wizard
 * - isLoading: True during initial localStorage check
 * - completeOnboarding: Mark onboarding as done
 * - resetOnboarding: Reset to show wizard again (for testing)
 */
export function useOnboarding() {
  const [showWizard, setShowWizard] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    try {
      const completed = localStorage.getItem(ONBOARDING_KEY)
      setShowWizard(!completed)
    } catch {
      // localStorage unavailable (private browsing, storage quota exceeded)
      // Skip wizard to avoid blocking the user
      setShowWizard(false)
    }
    setIsLoading(false)
  }, [])

  const completeOnboarding = () => {
    try {
      localStorage.setItem(ONBOARDING_KEY, 'true')
    } catch {
      // Silently fail - wizard will still close for this session
    }
    setShowWizard(false)
  }

  const resetOnboarding = () => {
    try {
      localStorage.removeItem(ONBOARDING_KEY)
    } catch {
      // Silently fail
    }
    setShowWizard(true)
  }

  return { showWizard, isLoading, completeOnboarding, resetOnboarding }
}
