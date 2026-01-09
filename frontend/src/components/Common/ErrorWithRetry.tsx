/**
 * ErrorWithRetry - Error state component with retry functionality
 * Provides consistent error UI with automatic and manual retry options
 */

import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react'

interface ErrorWithRetryProps {
  error: Error | string
  onRetry: () => void
  isRetrying?: boolean
  autoRetry?: boolean
  autoRetryDelay?: number
  maxAutoRetries?: number
  title?: string
  className?: string
}

export function ErrorWithRetry({
  error,
  onRetry,
  isRetrying = false,
  autoRetry = false,
  autoRetryDelay = 5000,
  maxAutoRetries = 3,
  title = 'Une erreur est survenue',
  className = '',
}: ErrorWithRetryProps) {
  const [autoRetryCount, setAutoRetryCount] = useState(0)
  const [countdown, setCountdown] = useState<number | null>(null)

  const errorMessage = typeof error === 'string' ? error : error.message

  // Determine if error is retryable
  const isRetryable = !errorMessage.includes('401') && !errorMessage.includes('403')

  // Auto-retry logic
  useEffect(() => {
    if (!autoRetry || !isRetryable || autoRetryCount >= maxAutoRetries || isRetrying) {
      return
    }

    setCountdown(Math.ceil(autoRetryDelay / 1000))

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev === null || prev <= 1) {
          return null
        }
        return prev - 1
      })
    }, 1000)

    const timeout = setTimeout(() => {
      setAutoRetryCount((prev) => prev + 1)
      onRetry()
    }, autoRetryDelay)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [autoRetry, autoRetryCount, maxAutoRetries, autoRetryDelay, isRetrying, isRetryable, onRetry])

  const handleManualRetry = useCallback(() => {
    setAutoRetryCount(0)
    setCountdown(null)
    onRetry()
  }, [onRetry])

  return (
    <div className={`bg-red-50 border border-red-200 rounded-xl p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-800 mb-2">{title}</h3>
          <p className="text-red-700 mb-4">{errorMessage}</p>

          {isRetryable && (
            <div className="flex items-center gap-4">
              <button
                onClick={handleManualRetry}
                disabled={isRetrying}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {isRetrying ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Nouvelle tentative...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Reessayer
                  </>
                )}
              </button>

              {autoRetry && countdown !== null && autoRetryCount < maxAutoRetries && (
                <span className="text-sm text-red-600">
                  Nouvelle tentative dans {countdown}s ({autoRetryCount + 1}/{maxAutoRetries})
                </span>
              )}

              {autoRetry && autoRetryCount >= maxAutoRetries && (
                <span className="text-sm text-red-600">
                  Tentatives automatiques epuisees
                </span>
              )}
            </div>
          )}

          {!isRetryable && (
            <p className="text-sm text-red-600">
              Cette erreur ne peut pas etre resolue par une nouvelle tentative.
              Verifiez vos identifiants ou contactez le support.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Simple error alert without retry - for non-critical errors
 */
interface ErrorAlertProps {
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorAlert({ message, onDismiss, className = '' }: ErrorAlertProps) {
  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-800">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-500 hover:text-red-700"
            aria-label="Fermer"
          >
            &times;
          </button>
        )}
      </div>
    </div>
  )
}
