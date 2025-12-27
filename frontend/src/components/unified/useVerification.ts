/**
 * useVerification - Hook for product verification across all modules
 */

import { useState, useCallback } from 'react'
import {
  verificationService,
  type VerificationResponse,
  type VerificationRequest,
} from '../../services/verificationService'
import type { DisplayableProduct } from '../../types/unified'

interface VerificationState {
  loading: boolean
  result?: VerificationResponse
  error?: string
}

export function useVerification() {
  const [verificationStates, setVerificationStates] = useState<Record<string, VerificationState>>({})
  const [expandedVerification, setExpandedVerification] = useState<string | null>(null)

  const verifyProduct = useCallback(async (product: DisplayableProduct) => {
    const asin = product.asin

    // Set loading state
    setVerificationStates((prev) => ({
      ...prev,
      [asin]: { loading: true },
    }))

    try {
      const request: VerificationRequest = {
        asin,
        saved_price: product.current_price ?? product.market_buy_price,
        saved_bsr: product.bsr,
        saved_fba_count: product.fba_seller_count,
      }

      const result = await verificationService.verifyProduct(request)

      setVerificationStates((prev) => ({
        ...prev,
        [asin]: { loading: false, result },
      }))

      // Auto-expand
      setExpandedVerification(asin)

      return result
    } catch (error) {
      setVerificationStates((prev) => ({
        ...prev,
        [asin]: {
          loading: false,
          error: error instanceof Error ? error.message : 'Erreur de verification',
        },
      }))
      throw error
    }
  }, [])

  const getVerificationState = useCallback(
    (asin: string): VerificationState | undefined => verificationStates[asin],
    [verificationStates]
  )

  const isVerificationExpanded = useCallback(
    (asin: string): boolean => expandedVerification === asin,
    [expandedVerification]
  )

  const toggleVerificationExpansion = useCallback((asin: string) => {
    setExpandedVerification((prev) => (prev === asin ? null : asin))
  }, [])

  const clearVerification = useCallback((asin: string) => {
    setVerificationStates((prev) => {
      const next = { ...prev }
      delete next[asin]
      return next
    })
    if (expandedVerification === asin) {
      setExpandedVerification(null)
    }
  }, [expandedVerification])

  return {
    verifyProduct,
    getVerificationState,
    isVerificationExpanded,
    toggleVerificationExpansion,
    clearVerification,
  }
}
