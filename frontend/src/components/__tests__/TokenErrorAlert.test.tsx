/**
 * Tests for TokenErrorAlert and TokenErrorBadge components
 * Phase 8 Audit
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TokenErrorAlert, TokenErrorBadge } from '../TokenErrorAlert'

// Mock pour tokenErrorHandler
vi.mock('../../utils/tokenErrorHandler', () => ({
  isTokenError: vi.fn(),
  parseTokenError: vi.fn(),
  formatTokenErrorMessage: vi.fn()
}))

import { isTokenError, parseTokenError, formatTokenErrorMessage } from '../../utils/tokenErrorHandler'

const mock429Error = {
  response: {
    status: 429,
    headers: {
      'x-token-balance': '50',
      'x-token-required': '100',
      'retry-after': '3600'
    },
    data: {
      detail: 'Tokens insuffisants'
    }
  }
}

describe('TokenErrorAlert', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null when error is null', () => {
    ;(isTokenError as any).mockReturnValue(false)

    const { container } = render(<TokenErrorAlert error={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when error is not 429', () => {
    const error500 = { response: { status: 500 } }
    ;(isTokenError as any).mockReturnValue(false)

    const { container } = render(<TokenErrorAlert error={error500} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders alert for valid 429 error', () => {
    ;(isTokenError as any).mockReturnValue(true)
    ;(parseTokenError as any).mockReturnValue({
      balance: 50,
      required: 100,
      deficit: 50,
      retryAfter: 3600,
      message: 'Tokens insuffisants'
    })
    ;(formatTokenErrorMessage as any).mockReturnValue(
      'Vous avez 50 tokens disponibles, mais 100 sont necessaires.'
    )

    render(<TokenErrorAlert error={mock429Error} />)

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/Tokens Keepa temporairement/i)).toBeInTheDocument()
    expect(screen.getByText(/Disponible:/i)).toBeInTheDocument()
    expect(screen.getByText(/Requis:/i)).toBeInTheDocument()
  })

  it('renders retry button that reloads page', () => {
    ;(isTokenError as any).mockReturnValue(true)
    ;(parseTokenError as any).mockReturnValue({
      balance: 50,
      required: 100,
      deficit: 50,
      retryAfter: 3600,
      message: 'Tokens insuffisants'
    })
    ;(formatTokenErrorMessage as any).mockReturnValue('Message')

    // Mock window.location.reload
    const reloadMock = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true
    })

    render(<TokenErrorAlert error={mock429Error} />)

    const retryButton = screen.getByRole('button', { name: /essayer/i })
    expect(retryButton).toBeInTheDocument()

    fireEvent.click(retryButton)
    expect(reloadMock).toHaveBeenCalled()
  })
})

describe('TokenErrorBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null when not 429 error', () => {
    ;(isTokenError as any).mockReturnValue(false)

    const { container } = render(<TokenErrorBadge error={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders compact badge for 429 error', () => {
    ;(isTokenError as any).mockReturnValue(true)
    ;(parseTokenError as any).mockReturnValue({
      balance: 25,
      required: 75,
      deficit: 50,
      retryAfter: 1800,
      message: 'Tokens insuffisants'
    })

    render(<TokenErrorBadge error={mock429Error} />)

    expect(screen.getByText(/Tokens insuffisants/i)).toBeInTheDocument()
    expect(screen.getByText(/25\/75/)).toBeInTheDocument()
  })
})
