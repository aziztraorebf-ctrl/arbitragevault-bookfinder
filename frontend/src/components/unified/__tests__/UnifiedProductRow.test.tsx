// frontend/src/components/unified/__tests__/UnifiedProductRow.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { UnifiedProductRow } from '../UnifiedProductRow'
import type { DisplayableProduct } from '../../../types/unified'

describe('UnifiedProductRow', () => {
  const mockProductScore: DisplayableProduct = {
    asin: 'B08TEST123',
    title: 'Test Product Title',
    source: 'product_score',
    roi_percent: 45.2,
    velocity_score: 72,
    bsr: 12500,
    score: 85.5,
    rank: 1,
    amazon_on_listing: true,
    amazon_buybox: false,
    market_sell_price: 24.99,
    market_buy_price: 15.50,
  }

  const mockNicheProduct: DisplayableProduct = {
    asin: 'B08NICHE99',
    title: 'Niche Product',
    source: 'niche_product',
    roi_percent: 38.5,
    velocity_score: 55,
    bsr: 25000,
    recommendation: 'BUY',
    current_price: 19.99,
    category_name: 'Books',
  }

  it('should render ProductScore row with all columns', () => {
    render(
      <table>
        <tbody>
          <UnifiedProductRow
            product={mockProductScore}
            isExpanded={false}
            onToggle={vi.fn()}
            features={{ showScore: true, showRank: true }}
          />
        </tbody>
      </table>
    )

    expect(screen.getByText('B08TEST123')).toBeInTheDocument()
    expect(screen.getByText('Test Product Title')).toBeInTheDocument()
    expect(screen.getByText('85.5')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('45.2%')).toBeInTheDocument()
    expect(screen.getByText('72')).toBeInTheDocument()
    expect(screen.getByText('#12,500')).toBeInTheDocument()
  })

  it('should render NicheProduct row with recommendation badge', () => {
    render(
      <table>
        <tbody>
          <UnifiedProductRow
            product={mockNicheProduct}
            isExpanded={false}
            onToggle={vi.fn()}
            features={{ showRecommendation: true, showCategory: true }}
          />
        </tbody>
      </table>
    )

    expect(screen.getByText('B08NICHE99')).toBeInTheDocument()
    expect(screen.getByText('Acheter')).toBeInTheDocument() // BUY badge
    expect(screen.getByText('Books')).toBeInTheDocument()
  })

  it('should hide score column when showScore is false', () => {
    render(
      <table>
        <tbody>
          <UnifiedProductRow
            product={mockProductScore}
            isExpanded={false}
            onToggle={vi.fn()}
            features={{ showScore: false }}
          />
        </tbody>
      </table>
    )

    expect(screen.queryByText('85.5')).not.toBeInTheDocument()
  })

  it('should call onToggle when chevron is clicked', () => {
    const onToggle = vi.fn()
    render(
      <table>
        <tbody>
          <UnifiedProductRow
            product={mockProductScore}
            isExpanded={false}
            onToggle={onToggle}
            features={{ showAccordion: true }}
          />
        </tbody>
      </table>
    )

    const chevron = screen.getByRole('button', { name: /expand/i })
    fireEvent.click(chevron)

    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('should show Amazon link that opens in new tab', () => {
    render(
      <table>
        <tbody>
          <UnifiedProductRow
            product={mockProductScore}
            isExpanded={false}
            onToggle={vi.fn()}
            features={{}}
          />
        </tbody>
      </table>
    )

    const amazonLink = screen.getByRole('link', { name: /B08TEST123/i })
    expect(amazonLink).toHaveAttribute('href', 'https://www.amazon.com/dp/B08TEST123')
    expect(amazonLink).toHaveAttribute('target', '_blank')
  })
})
