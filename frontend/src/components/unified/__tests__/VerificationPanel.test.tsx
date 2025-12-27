// frontend/src/components/unified/__tests__/VerificationPanel.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VerificationPanel } from '../VerificationPanel'
import type { VerificationResponse } from '../../../services/verificationService'

describe('VerificationPanel', () => {
  const mockVerificationResult: VerificationResponse = {
    asin: 'B08TEST123',
    status: 'ok',
    message: 'Product verified successfully',
    verified_at: '2025-12-27T10:00:00Z',
    sell_price: 24.99,
    used_sell_price: 18.99,
    current_bsr: 12500,
    current_fba_count: 8,
    amazon_selling: false,
    changes: [],
    buy_opportunities: [
      {
        seller_id: 'SELLER1',
        condition: 'Used - Good',
        condition_code: 3,
        is_new: false,
        price: 10.50,
        shipping: 3.99,
        total_cost: 14.49,
        sell_price: 18.99,
        profit: 4.50,
        roi_percent: 31.05,
        is_fba: true,
        is_prime: true,
      },
    ],
  }

  it('should render verification result with status badge', () => {
    render(<VerificationPanel result={mockVerificationResult} />)

    expect(screen.getByText('OK')).toBeInTheDocument()
    expect(screen.getByText('Product verified successfully')).toBeInTheDocument()
  })

  it('should display current prices', () => {
    render(<VerificationPanel result={mockVerificationResult} />)

    expect(screen.getByText('$24.99')).toBeInTheDocument() // sell_price
    // $18.99 appears twice: in used_sell_price AND in buy opportunities table
    expect(screen.getAllByText('$18.99').length).toBeGreaterThanOrEqual(1) // used_sell_price
    expect(screen.getByText('#12,500')).toBeInTheDocument() // BSR
  })

  it('should display buy opportunities table', () => {
    render(<VerificationPanel result={mockVerificationResult} />)

    expect(screen.getByText('Used - Good')).toBeInTheDocument()
    expect(screen.getByText('$10.50')).toBeInTheDocument()
    expect(screen.getByText('31%')).toBeInTheDocument()
  })

  it('should show Amazon warning when amazon_selling is true', () => {
    const withAmazon = { ...mockVerificationResult, amazon_selling: true }
    render(<VerificationPanel result={withAmazon} />)

    expect(screen.getByText(/Amazon vend ce produit/)).toBeInTheDocument()
  })

  it('should show changes with severity colors', () => {
    const withChanges: VerificationResponse = {
      ...mockVerificationResult,
      status: 'changed',
      changes: [
        { field: 'price', saved_value: 20, current_value: 25, severity: 'warning', message: 'Price increased by 25%' },
      ],
    }
    render(<VerificationPanel result={withChanges} />)

    expect(screen.getByText('Modifie')).toBeInTheDocument()
    expect(screen.getByText('Price increased by 25%')).toBeInTheDocument()
  })
})
