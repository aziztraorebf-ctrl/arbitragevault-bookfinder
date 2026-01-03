import { useState, useEffect } from 'react'

const ONBOARDING_KEY = 'arbitragevault_onboarding_complete'

export function useOnboarding() {
  const [showWizard, setShowWizard] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_KEY)
    setShowWizard(!completed)
    setIsLoading(false)
  }, [])

  const completeOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    setShowWizard(false)
  }

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY)
    setShowWizard(true)
  }

  return { showWizard, isLoading, completeOnboarding, resetOnboarding }
}
