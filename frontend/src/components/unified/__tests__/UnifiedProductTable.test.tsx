// frontend/src/components/unified/__tests__/UnifiedProductTable.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { UnifiedProductTable } from '../UnifiedProductTable'
import type { DisplayableProduct } from '../../../types/unified'

describe('UnifiedProductTable', () => {
  const mockProducts: DisplayableProduct[] = [
    {
      asin: 'B08TEST001',
      title: 'Product 1',
      source: 'product_score',
      roi_percent: 45.2,
      velocity_score: 72,
      bsr: 12500,
      score: 85.5,
      rank: 1,
      amazon_on_listing: true,
      amazon_buybox: false,
    },
    {
      asin: 'B08TEST002',
      title: 'Product 2',
      source: 'product_score',
      roi_percent: 32.1,
      velocity_score: 55,
      bsr: 25000,
      score: 72.3,
      rank: 2,
      amazon_on_listing: false,
      amazon_buybox: false,
    },
  ]

  it('should render table with products', () => {
    render(
      <UnifiedProductTable
        products={mockProducts}
        title="Test Results"
        features={{ showScore: true, showRank: true }}
      />
    )

    expect(screen.getByText('Test Results')).toBeInTheDocument()
    expect(screen.getByText('B08TEST001')).toBeInTheDocument()
    expect(screen.getByText('B08TEST002')).toBeInTheDocument()
    expect(screen.getByText('(2 produits)')).toBeInTheDocument()
  })

  it('should show empty state when no products', () => {
    render(
      <UnifiedProductTable
        products={[]}
        title="Empty Results"
        features={{}}
      />
    )

    expect(screen.getByText('Aucun produit a afficher')).toBeInTheDocument()
  })

  it('should filter products by minimum ROI', () => {
    render(
      <UnifiedProductTable
        products={mockProducts}
        title="Test"
        features={{ showFilters: true }}
        defaultFilters={{ minRoi: 40 }}
      />
    )

    // Only Product 1 has ROI >= 40
    expect(screen.getByText('B08TEST001')).toBeInTheDocument()
    expect(screen.queryByText('B08TEST002')).not.toBeInTheDocument()
  })

  it('should sort products by score descending', () => {
    render(
      <UnifiedProductTable
        products={mockProducts}
        title="Test"
        features={{ showScore: true }}
        defaultSort={{ by: 'score', order: 'desc' }}
      />
    )

    const rows = screen.getAllByRole('row')
    // First data row (after header) should be Product 1 (score 85.5)
    expect(rows[1]).toHaveTextContent('B08TEST001')
  })

  it('should call onExportCSV when export button clicked', () => {
    const onExport = vi.fn()
    render(
      <UnifiedProductTable
        products={mockProducts}
        title="Test"
        features={{ showExportCSV: true }}
        onExportCSV={onExport}
      />
    )

    const exportBtn = screen.getByText('Export CSV')
    fireEvent.click(exportBtn)

    expect(onExport).toHaveBeenCalledWith(mockProducts)
  })

  it('should show footer summary with averages', () => {
    render(
      <UnifiedProductTable
        products={mockProducts}
        title="Test"
        features={{ showFooterSummary: true }}
      />
    )

    // Average ROI: (45.2 + 32.1) / 2 = 38.65%
    expect(screen.getByText(/ROI moyen/)).toBeInTheDocument()
    // Average Velocity: (72 + 55) / 2 = 63.5
    expect(screen.getByText(/Velocite moyenne/)).toBeInTheDocument()
  })
})
