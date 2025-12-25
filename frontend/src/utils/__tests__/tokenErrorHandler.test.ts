/**
 * Tests for tokenErrorHandler utility functions
 * Phase 8 Audit
 */
import { describe, it, expect } from 'vitest'
import { parseTokenError, formatTokenErrorMessage, isTokenError } from '../tokenErrorHandler'

describe('isTokenError', () => {
  it('returns true for HTTP 429 error', () => {
    const error = { response: { status: 429 } }
    expect(isTokenError(error)).toBe(true)
  })

  it('returns false for HTTP 500 error', () => {
    const error = { response: { status: 500 } }
    expect(isTokenError(error)).toBe(false)
  })

  it('returns false for null error', () => {
    expect(isTokenError(null)).toBe(false)
  })

  it('returns false for undefined error', () => {
    expect(isTokenError(undefined)).toBe(false)
  })

  it('returns false for error without response', () => {
    const error = { message: 'Network Error' }
    expect(isTokenError(error)).toBe(false)
  })
})

describe('parseTokenError', () => {
  it('returns null for non-429 error', () => {
    const error = { response: { status: 500 } }
    expect(parseTokenError(error)).toBeNull()
  })

  it('parses 429 error with headers correctly', () => {
    const error = {
      response: {
        status: 429,
        headers: {
          'x-token-balance': '50',
          'x-token-required': '100',
          'retry-after': '3600'
        },
        data: { detail: 'Tokens insuffisants' }
      }
    }

    const result = parseTokenError(error)
    expect(result).not.toBeNull()
    expect(result?.balance).toBe(50)
    expect(result?.required).toBe(100)
    expect(result?.deficit).toBe(50)
    expect(result?.retryAfter).toBe(3600)
  })

  it('handles missing headers gracefully', () => {
    const error = {
      response: {
        status: 429,
        headers: {},
        data: { detail: 'Rate limited' }
      }
    }

    const result = parseTokenError(error)
    expect(result).not.toBeNull()
    expect(result?.balance).toBeNull()
    expect(result?.required).toBeNull()
    expect(result?.retryAfter).toBe(3600)
  })

  it('calculates deficit correctly', () => {
    const error = {
      response: {
        status: 429,
        headers: {
          'x-token-balance': '25',
          'x-token-required': '100'
        }
      }
    }

    const result = parseTokenError(error)
    expect(result?.deficit).toBe(75)
  })
})

describe('formatTokenErrorMessage', () => {
  it('formats message with balance and required', () => {
    const tokenError = {
      balance: 50,
      required: 100,
      deficit: 50,
      retryAfter: 3600,
      message: ''
    }

    const result = formatTokenErrorMessage(tokenError)
    expect(result).toContain('50 tokens disponibles')
    expect(result).toContain('100 sont nécessaires')
    expect(result).toContain('60 minutes')
  })

  it('formats fallback message when balance is null', () => {
    const tokenError = {
      balance: null,
      required: null,
      deficit: null,
      retryAfter: 1800,
      message: ''
    }

    const result = formatTokenErrorMessage(tokenError)
    expect(result).toContain('temporairement')
    expect(result).toContain('30 minutes')
  })
})
