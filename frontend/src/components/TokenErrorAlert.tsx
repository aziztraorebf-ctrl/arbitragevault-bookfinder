/**
 * Token Error Alert Component - Phase 5
 * Affiche message convivial quand HTTP 429 (tokens insuffisants)
 */

import React from 'react'
import { parseTokenError, formatTokenErrorMessage, isTokenError } from '../utils/tokenErrorHandler'

interface TokenErrorAlertProps {
  error: any
  className?: string
}

export const TokenErrorAlert: React.FC<TokenErrorAlertProps> = ({ error, className = '' }) => {
  if (!error || !isTokenError(error)) {
    return null
  }

  const tokenError = parseTokenError(error)
  if (!tokenError) {
    return null
  }

  const friendlyMessage = formatTokenErrorMessage(tokenError)

  return (
    <div
      className={`bg-yellow-50 border-l-4 border-yellow-400 p-4 ${className}`}
      role="alert"
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-yellow-800">
            Tokens Keepa temporairement épuisés
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>{friendlyMessage}</p>
            {tokenError.balance !== null && tokenError.required !== null && (
              <div className="mt-3 flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1">
                  <span className="font-semibold">Disponible:</span>
                  <span className="font-mono bg-yellow-100 px-2 py-1 rounded">
                    {tokenError.balance}
                  </span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="font-semibold">Requis:</span>
                  <span className="font-mono bg-yellow-100 px-2 py-1 rounded">
                    {tokenError.required}
                  </span>
                </span>
                {tokenError.deficit !== null && (
                  <span className="flex items-center gap-1">
                    <span className="font-semibold">Manquant:</span>
                    <span className="font-mono bg-red-100 text-red-700 px-2 py-1 rounded">
                      {tokenError.deficit}
                    </span>
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="mt-4">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="bg-yellow-100 px-3 py-1.5 rounded-md text-sm font-medium text-yellow-800 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
              >
                Réessayer
              </button>
              <p className="text-xs text-yellow-600 self-center">
                Les tokens se rechargent automatiquement
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Inline Token Error Badge - Version compacte
 */
export const TokenErrorBadge: React.FC<TokenErrorAlertProps> = ({ error, className = '' }) => {
  if (!error || !isTokenError(error)) {
    return null
  }

  const tokenError = parseTokenError(error)
  if (!tokenError) {
    return null
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-md text-sm ${className}`}>
      <svg
        className="h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <span className="font-medium">
        Tokens insuffisants ({tokenError.balance}/{tokenError.required})
      </span>
    </div>
  )
}
