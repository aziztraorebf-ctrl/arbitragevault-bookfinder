/**
 * Token Control Error Handler - Phase 5
 * Utilities pour gérer les erreurs HTTP 429 (tokens insuffisants)
 */

export interface TokenError {
  balance: number | null
  required: number | null
  deficit: number | null
  retryAfter: number
  message: string
}

/**
 * Parse HTTP 429 response headers et body pour extraire info tokens
 */
export function parseTokenError(error: any): TokenError | null {
  if (error.response?.status !== 429) {
    return null
  }

  const headers = error.response.headers
  const balance = headers['x-token-balance']
    ? parseInt(headers['x-token-balance'])
    : null
  const required = headers['x-token-required']
    ? parseInt(headers['x-token-required'])
    : null
  const retryAfter = headers['retry-after']
    ? parseInt(headers['retry-after'])
    : 3600

  const deficit = balance !== null && required !== null
    ? required - balance
    : null

  // Extraire détails du body
  const detail = error.response?.data?.detail
  const detailStr = typeof detail === 'string'
    ? detail
    : JSON.stringify(detail)

  const message = `Tokens Keepa insuffisants. Disponible: ${balance ?? '?'}, Requis: ${required ?? '?'}. ${detailStr || `Réessayez dans ${Math.round(retryAfter / 60)} minutes.`}`

  return {
    balance,
    required,
    deficit,
    retryAfter,
    message
  }
}

/**
 * Format user-friendly message pour UI
 */
export function formatTokenErrorMessage(tokenError: TokenError): string {
  const retryMinutes = Math.round(tokenError.retryAfter / 60)

  if (tokenError.balance !== null && tokenError.required !== null) {
    return `Vous avez ${tokenError.balance} tokens disponibles, mais ${tokenError.required} sont nécessaires pour cette action. Réessayez dans ${retryMinutes} minutes lorsque les tokens se seront rechargés.`
  }

  return `Tokens Keepa temporairement épuisés. Réessayez dans ${retryMinutes} minutes.`
}

/**
 * Check si erreur est HTTP 429
 */
export function isTokenError(error: any): boolean {
  return error?.response?.status === 429
}
