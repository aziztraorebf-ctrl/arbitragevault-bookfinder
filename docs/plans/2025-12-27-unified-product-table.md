# Unified Product Table - Plan d'Implementation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Unifier les composants `ViewResultsTable` et `ProductsTable` en un seul `UnifiedProductTable` reutilisable par tous les modules (Analyse Manuelle, Niche Discovery, AutoSourcing).

**Architecture:** Creer un type union `DisplayableProduct` qui normalise les champs de `ProductScore` et `NicheProduct`. Le composant unifie accepte des feature flags pour activer/desactiver colonnes et fonctionnalites selon le module appelant. La feature Verification (Phase 8) est extraite en composant reutilisable.

**Tech Stack:** React, TypeScript, Tailwind CSS, React Query (hooks existants)

---

## Phase 1: Type Unifie et Composant de Base

### Task 1.1: Creer le type DisplayableProduct

**Files:**
- Create: `frontend/src/types/unified.ts`
- Test: `frontend/src/types/__tests__/unified.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend/src/types/__tests__/unified.test.ts
import { describe, it, expect } from 'vitest'
import {
  normalizeProductScore,
  normalizeNicheProduct,
  type DisplayableProduct
} from '../unified'
import type { ProductScore } from '../views'

describe('DisplayableProduct normalization', () => {
  it('should normalize ProductScore to DisplayableProduct', () => {
    const productScore: ProductScore = {
      asin: 'B08TEST123',
      title: 'Test Product',
      score: 85.5,
      rank: 1,
      strategy_profile: 'textbook',
      weights_applied: { roi: 0.6, velocity: 0.3, stability: 0.1 },
      components: { roi_contribution: 40, velocity_contribution: 30, stability_contribution: 15 },
      raw_metrics: { roi_pct: 45.2, velocity_score: 72, stability_score: 65 },
      amazon_on_listing: true,
      amazon_buybox: false,
      current_bsr: 12500,
      market_sell_price: 24.99,
      market_buy_price: 15.50,
    }

    const result = normalizeProductScore(productScore)

    expect(result.asin).toBe('B08TEST123')
    expect(result.title).toBe('Test Product')
    expect(result.score).toBe(85.5)
    expect(result.rank).toBe(1)
    expect(result.roi_percent).toBe(45.2)
    expect(result.velocity_score).toBe(72)
    expect(result.bsr).toBe(12500)
    expect(result.source).toBe('product_score')
  })

  it('should normalize NicheProduct to DisplayableProduct', () => {
    const nicheProduct = {
      asin: 'B08NICHE99',
      title: 'Niche Product',
      roi_percent: 38.5,
      velocity_score: 55,
      recommendation: 'BUY',
      current_price: 19.99,
      bsr: 25000,
      category_name: 'Books',
      fba_fees: 5.50,
      estimated_profit: 8.25,
      fba_seller_count: 12,
    }

    const result = normalizeNicheProduct(nicheProduct)

    expect(result.asin).toBe('B08NICHE99')
    expect(result.title).toBe('Niche Product')
    expect(result.roi_percent).toBe(38.5)
    expect(result.velocity_score).toBe(55)
    expect(result.recommendation).toBe('BUY')
    expect(result.bsr).toBe(25000)
    expect(result.source).toBe('niche_product')
    // score and rank should be undefined for niche products
    expect(result.score).toBeUndefined()
    expect(result.rank).toBeUndefined()
  })

  it('should handle null/undefined values gracefully', () => {
    const minimalProduct: ProductScore = {
      asin: 'B08MIN0001',
      title: null,
      score: 0,
      rank: 1,
      strategy_profile: null,
      weights_applied: { roi: 0, velocity: 0, stability: 0 },
      components: { roi_contribution: 0, velocity_contribution: 0, stability_contribution: 0 },
      raw_metrics: { roi_pct: 0, velocity_score: 0, stability_score: 0 },
      amazon_on_listing: false,
      amazon_buybox: false,
    }

    const result = normalizeProductScore(minimalProduct)

    expect(result.asin).toBe('B08MIN0001')
    expect(result.title).toBeNull()
    expect(result.bsr).toBeUndefined()
    expect(result.market_sell_price).toBeUndefined()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/types/__tests__/unified.test.ts
```

Expected: FAIL with "Cannot find module '../unified'"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/types/unified.ts
/**
 * Unified Product Type
 * Normalizes ProductScore (Analyse Manuelle/AutoSourcing) and NicheProduct (Niche Discovery)
 * into a single displayable format for UnifiedProductTable
 */

import type { ProductScore, StrategyProfile, VelocityBreakdown } from './views'

// Source type discriminator
export type ProductSource = 'product_score' | 'niche_product'

// Recommendation values from Niche Discovery
export type Recommendation = 'STRONG_BUY' | 'BUY' | 'CONSIDER' | 'SKIP'

/**
 * NicheProduct - Type for products from Niche Discovery
 * Matches ProductsTable interface in niche-discovery/ProductsTable.tsx
 */
export interface NicheProduct {
  asin: string
  title?: string
  roi_percent: number
  velocity_score: number
  recommendation: string
  current_price?: number
  bsr?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
  fba_seller_count?: number
}

/**
 * DisplayableProduct - Unified type for all product displays
 * Contains all possible fields from both sources with optional flags
 */
export interface DisplayableProduct {
  // Core identity (required)
  asin: string
  title: string | null
  source: ProductSource

  // Metrics (common to both, normalized)
  roi_percent: number
  velocity_score: number
  bsr?: number

  // ProductScore-specific fields (optional)
  score?: number
  rank?: number
  strategy_profile?: StrategyProfile
  weights_applied?: {
    roi: number
    velocity: number
    stability: number
  }
  components?: {
    roi_contribution: number
    velocity_contribution: number
    stability_contribution: number
  }
  stability_score?: number
  amazon_on_listing?: boolean
  amazon_buybox?: boolean
  market_sell_price?: number
  market_buy_price?: number
  current_roi_pct?: number
  max_buy_price_35pct?: number
  velocity_breakdown?: VelocityBreakdown
  last_updated_at?: string | null
  pricing?: ProductScore['pricing']

  // NicheProduct-specific fields (optional)
  recommendation?: Recommendation | string
  current_price?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
  fba_seller_count?: number
}

/**
 * Normalize a ProductScore to DisplayableProduct
 */
export function normalizeProductScore(product: ProductScore): DisplayableProduct {
  return {
    // Core
    asin: product.asin,
    title: product.title,
    source: 'product_score',

    // Metrics (normalized field names)
    roi_percent: product.raw_metrics?.roi_pct ?? 0,
    velocity_score: product.raw_metrics?.velocity_score ?? 0,
    bsr: product.current_bsr ?? undefined,

    // ProductScore-specific
    score: product.score,
    rank: product.rank,
    strategy_profile: product.strategy_profile,
    weights_applied: product.weights_applied,
    components: product.components,
    stability_score: product.raw_metrics?.stability_score,
    amazon_on_listing: product.amazon_on_listing,
    amazon_buybox: product.amazon_buybox,
    market_sell_price: product.market_sell_price,
    market_buy_price: product.market_buy_price,
    current_roi_pct: product.current_roi_pct,
    max_buy_price_35pct: product.max_buy_price_35pct,
    velocity_breakdown: product.velocity_breakdown,
    last_updated_at: product.last_updated_at,
    pricing: product.pricing,
  }
}

/**
 * Normalize a NicheProduct to DisplayableProduct
 */
export function normalizeNicheProduct(product: NicheProduct): DisplayableProduct {
  return {
    // Core
    asin: product.asin,
    title: product.title ?? null,
    source: 'niche_product',

    // Metrics (already normalized in NicheProduct)
    roi_percent: product.roi_percent,
    velocity_score: product.velocity_score,
    bsr: product.bsr,

    // NicheProduct-specific
    recommendation: product.recommendation as Recommendation,
    current_price: product.current_price,
    category_name: product.category_name,
    fba_fees: product.fba_fees,
    estimated_profit: product.estimated_profit,
    fba_seller_count: product.fba_seller_count,
  }
}

/**
 * Type guard to check if product has ProductScore-specific fields
 */
export function hasScoreData(product: DisplayableProduct): boolean {
  return product.source === 'product_score' && product.score !== undefined
}

/**
 * Type guard to check if product has NicheProduct-specific fields
 */
export function hasRecommendation(product: DisplayableProduct): boolean {
  return product.recommendation !== undefined
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/types/__tests__/unified.test.ts
```

Expected: PASS - 3 tests

**Step 5: Commit**

```bash
git add frontend/src/types/unified.ts frontend/src/types/__tests__/unified.test.ts
git commit -m "feat(unified): add DisplayableProduct type with normalization functions

- Create unified.ts with DisplayableProduct interface
- Add normalizeProductScore and normalizeNicheProduct functions
- Include type guards hasScoreData and hasRecommendation
- Add comprehensive unit tests for normalization"
```

---

### Task 1.2: Creer le composant UnifiedProductRow

**Files:**
- Create: `frontend/src/components/unified/UnifiedProductRow.tsx`
- Create: `frontend/src/components/unified/index.ts`
- Test: `frontend/src/components/unified/__tests__/UnifiedProductRow.test.tsx`

**Step 1: Write the failing test**

```typescript
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
            features={{ showRecommendation: true }}
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
            features={{}}
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
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/UnifiedProductRow.test.tsx
```

Expected: FAIL with "Cannot find module '../UnifiedProductRow'"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/components/unified/UnifiedProductRow.tsx
/**
 * UnifiedProductRow - Single row component for unified product display
 * Supports both ProductScore and NicheProduct sources
 * Feature flags control which columns are displayed
 */

import { Fragment } from 'react'
import type { DisplayableProduct, Recommendation } from '../../types/unified'

export interface UnifiedRowFeatures {
  showScore?: boolean
  showRank?: boolean
  showRecommendation?: boolean
  showCategory?: boolean
  showAmazonBadges?: boolean
  showVerifyButton?: boolean
  showAccordion?: boolean
}

interface UnifiedProductRowProps {
  product: DisplayableProduct
  isExpanded: boolean
  onToggle: () => void
  features: UnifiedRowFeatures
  onVerify?: (product: DisplayableProduct) => void
  verificationLoading?: boolean
  AccordionComponent?: React.ComponentType<{ product: DisplayableProduct; isExpanded: boolean }>
}

// Recommendation badge colors and labels
const RECOMMENDATION_BADGES: Record<string, { label: string; color: string }> = {
  STRONG_BUY: { label: 'Achat Fort', color: 'bg-green-600 text-white' },
  BUY: { label: 'Acheter', color: 'bg-green-500 text-white' },
  CONSIDER: { label: 'Considerer', color: 'bg-yellow-500 text-white' },
  SKIP: { label: 'Passer', color: 'bg-red-500 text-white' },
}

export function UnifiedProductRow({
  product,
  isExpanded,
  onToggle,
  features,
  onVerify,
  verificationLoading,
  AccordionComponent,
}: UnifiedProductRowProps) {
  const {
    showScore = false,
    showRank = false,
    showRecommendation = false,
    showCategory = false,
    showAmazonBadges = false,
    showVerifyButton = false,
    showAccordion = true,
  } = features

  const recommendationBadge = product.recommendation
    ? RECOMMENDATION_BADGES[product.recommendation] || { label: product.recommendation, color: 'bg-gray-500 text-white' }
    : null

  // ROI color coding
  const roiColorClass =
    product.roi_percent >= 30
      ? 'text-green-600'
      : product.roi_percent >= 15
      ? 'text-yellow-600'
      : 'text-red-600'

  return (
    <Fragment>
      <tr className="hover:bg-gray-50 transition-colors">
        {/* Chevron for expansion */}
        {showAccordion && (
          <td className="px-4 py-3 text-center">
            <button
              onClick={onToggle}
              className="text-gray-500 hover:text-gray-700 transition-transform"
              aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
            >
              <span
                className={`inline-block transition-transform duration-300 ${
                  isExpanded ? 'rotate-90' : ''
                }`}
              >
                [chevron]
              </span>
            </button>
          </td>
        )}

        {/* Rank (optional) */}
        {showRank && (
          <td className="px-4 py-3 text-center text-sm font-medium text-gray-900">
            {product.rank ?? '-'}
          </td>
        )}

        {/* ASIN with Amazon link */}
        <td className="px-4 py-3 text-sm font-mono text-blue-600">
          <a
            href={`https://www.amazon.com/dp/${product.asin}`}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {product.asin}
          </a>
        </td>

        {/* Title */}
        <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
          <div>
            <p className="truncate">{product.title || 'N/A'}</p>
            {showCategory && product.category_name && (
              <p className="text-xs text-gray-400 mt-1">{product.category_name}</p>
            )}
          </div>
        </td>

        {/* Score (optional - ProductScore only) */}
        {showScore && (
          <td className="px-4 py-3 text-center text-sm font-bold text-purple-600">
            {product.score?.toFixed(1) ?? '-'}
          </td>
        )}

        {/* ROI */}
        <td className={`px-4 py-3 text-center text-sm font-semibold ${roiColorClass}`}>
          {product.roi_percent.toFixed(1)}%
        </td>

        {/* Velocity */}
        <td className="px-4 py-3 text-center">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-sm font-medium text-gray-900">
              {product.velocity_score.toFixed(0)}
            </span>
            <div className="w-16 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min(product.velocity_score, 100)}%` }}
              />
            </div>
          </div>
        </td>

        {/* BSR */}
        <td className="px-4 py-3 text-center text-sm font-medium text-gray-700">
          {product.bsr ? `#${product.bsr.toLocaleString()}` : 'N/A'}
        </td>

        {/* Recommendation badge (optional - NicheProduct) */}
        {showRecommendation && (
          <td className="px-4 py-3 text-center">
            {recommendationBadge ? (
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${recommendationBadge.color}`}
              >
                {recommendationBadge.label}
              </span>
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </td>
        )}

        {/* Amazon badges (optional) */}
        {showAmazonBadges && (
          <td className="px-4 py-3 text-center">
            <div className="flex gap-1 justify-center">
              {product.amazon_on_listing && (
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">
                  AMZ
                </span>
              )}
              {product.amazon_buybox && (
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                  BB
                </span>
              )}
            </div>
          </td>
        )}

        {/* Actions: Verify button (optional) */}
        {showVerifyButton && (
          <td className="px-4 py-3 text-center">
            <div className="flex gap-2 justify-center">
              <a
                href={`https://www.amazon.com/dp/${product.asin}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-xs font-medium rounded-md border bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100"
              >
                Amazon
              </a>
              {onVerify && (
                <button
                  onClick={() => onVerify(product)}
                  disabled={verificationLoading}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                    verificationLoading
                      ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                      : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                  }`}
                >
                  {verificationLoading ? 'Verification...' : 'Verifier'}
                </button>
              )}
            </div>
          </td>
        )}
      </tr>

      {/* Accordion row */}
      {showAccordion && AccordionComponent && (
        <tr>
          <td colSpan={20} className="p-0">
            <AccordionComponent product={product} isExpanded={isExpanded} />
          </td>
        </tr>
      )}
    </Fragment>
  )
}
```

```typescript
// frontend/src/components/unified/index.ts
export { UnifiedProductRow } from './UnifiedProductRow'
export type { UnifiedRowFeatures } from './UnifiedProductRow'
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/UnifiedProductRow.test.tsx
```

Expected: PASS - 5 tests

**Step 5: Commit**

```bash
git add frontend/src/components/unified/
git commit -m "feat(unified): add UnifiedProductRow component

- Create UnifiedProductRow with feature flags for column visibility
- Support both ProductScore and NicheProduct display modes
- Add recommendation badges, Amazon badges, verify button support
- Include comprehensive unit tests"
```

---

### Task 1.3: Creer le composant UnifiedProductTable

**Files:**
- Create: `frontend/src/components/unified/UnifiedProductTable.tsx`
- Update: `frontend/src/components/unified/index.ts`
- Test: `frontend/src/components/unified/__tests__/UnifiedProductTable.test.tsx`

**Step 1: Write the failing test**

```typescript
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
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/UnifiedProductTable.test.tsx
```

Expected: FAIL with "Cannot find module '../UnifiedProductTable'"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/components/unified/UnifiedProductTable.tsx
/**
 * UnifiedProductTable - Main table component for unified product display
 * Supports filtering, sorting, export, and feature flags
 */

import { useState, useMemo } from 'react'
import type { DisplayableProduct } from '../../types/unified'
import { UnifiedProductRow, type UnifiedRowFeatures } from './UnifiedProductRow'

export interface UnifiedTableFeatures extends UnifiedRowFeatures {
  showFilters?: boolean
  showExportCSV?: boolean
  showFooterSummary?: boolean
}

export interface UnifiedTableFilters {
  minRoi?: number
  minVelocity?: number
  minScore?: number
  amazonListed?: boolean
  amazonBuybox?: boolean
}

export interface UnifiedTableSort {
  by: 'score' | 'rank' | 'roi' | 'velocity' | 'bsr'
  order: 'asc' | 'desc'
}

interface UnifiedProductTableProps {
  products: DisplayableProduct[]
  title: string
  features: UnifiedTableFeatures
  defaultFilters?: UnifiedTableFilters
  defaultSort?: UnifiedTableSort
  onExportCSV?: (products: DisplayableProduct[]) => void
  onVerify?: (product: DisplayableProduct) => void
  AccordionComponent?: React.ComponentType<{ product: DisplayableProduct; isExpanded: boolean }>
}

export function UnifiedProductTable({
  products,
  title,
  features,
  defaultFilters = {},
  defaultSort = { by: 'score', order: 'desc' },
  onExportCSV,
  onVerify,
  AccordionComponent,
}: UnifiedProductTableProps) {
  const {
    showFilters = false,
    showExportCSV = false,
    showFooterSummary = false,
    showScore = false,
    showRank = false,
    showRecommendation = false,
    showCategory = false,
    showAmazonBadges = false,
    showVerifyButton = false,
    showAccordion = true,
  } = features

  // Filter state
  const [filters, setFilters] = useState<UnifiedTableFilters>(defaultFilters)
  const [sort, setSort] = useState<UnifiedTableSort>(defaultSort)
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  // Process products with filters and sorting
  const processedProducts = useMemo(() => {
    let result = [...products]

    // Apply filters
    if (filters.minRoi !== undefined && filters.minRoi > 0) {
      result = result.filter((p) => p.roi_percent >= filters.minRoi!)
    }
    if (filters.minVelocity !== undefined && filters.minVelocity > 0) {
      result = result.filter((p) => p.velocity_score >= filters.minVelocity!)
    }
    if (filters.minScore !== undefined && filters.minScore > 0) {
      result = result.filter((p) => (p.score ?? 0) >= filters.minScore!)
    }
    if (filters.amazonListed) {
      result = result.filter((p) => p.amazon_on_listing)
    }
    if (filters.amazonBuybox) {
      result = result.filter((p) => p.amazon_buybox)
    }

    // Apply sorting
    result.sort((a, b) => {
      let compareValue = 0
      switch (sort.by) {
        case 'score':
          compareValue = (a.score ?? 0) - (b.score ?? 0)
          break
        case 'rank':
          compareValue = (a.rank ?? 999) - (b.rank ?? 999)
          break
        case 'roi':
          compareValue = a.roi_percent - b.roi_percent
          break
        case 'velocity':
          compareValue = a.velocity_score - b.velocity_score
          break
        case 'bsr':
          compareValue = (a.bsr ?? 999999) - (b.bsr ?? 999999)
          break
      }
      return sort.order === 'desc' ? -compareValue : compareValue
    })

    return result
  }, [products, filters, sort])

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    if (processedProducts.length === 0) return null
    const avgRoi =
      processedProducts.reduce((sum, p) => sum + p.roi_percent, 0) / processedProducts.length
    const avgVelocity =
      processedProducts.reduce((sum, p) => sum + p.velocity_score, 0) / processedProducts.length
    return { avgRoi, avgVelocity }
  }, [processedProducts])

  // Empty state
  if (products.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 text-center">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Aucun produit a afficher</h3>
        <p className="text-sm text-gray-500">Lancez une analyse pour voir les resultats.</p>
      </div>
    )
  }

  // Row features to pass down
  const rowFeatures: UnifiedRowFeatures = {
    showScore,
    showRank,
    showRecommendation,
    showCategory,
    showAmazonBadges,
    showVerifyButton,
    showAccordion,
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <span>{title}</span>
            <span className="text-sm font-normal text-gray-600">
              ({processedProducts.length} produits)
            </span>
          </h3>
          {showExportCSV && onExportCSV && (
            <button
              onClick={() => onExportCSV(processedProducts)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              Export CSV
            </button>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="flex gap-4 flex-wrap items-end mt-4">
            {/* Min ROI */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">ROI min</label>
              <input
                type="number"
                value={filters.minRoi ?? ''}
                onChange={(e) =>
                  setFilters({ ...filters, minRoi: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                placeholder="0"
              />
            </div>

            {/* Min Velocity */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Velocity min</label>
              <input
                type="number"
                value={filters.minVelocity ?? ''}
                onChange={(e) =>
                  setFilters({ ...filters, minVelocity: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                placeholder="0"
              />
            </div>

            {/* Min Score (only if showScore) */}
            {showScore && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Score min</label>
                <input
                  type="number"
                  value={filters.minScore ?? ''}
                  onChange={(e) =>
                    setFilters({ ...filters, minScore: e.target.value ? Number(e.target.value) : undefined })
                  }
                  className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                  placeholder="0"
                />
              </div>
            )}

            {/* Sort By */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Trier par</label>
              <select
                value={sort.by}
                onChange={(e) => setSort({ ...sort, by: e.target.value as UnifiedTableSort['by'] })}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
              >
                {showScore && <option value="score">Score</option>}
                {showRank && <option value="rank">Rank</option>}
                <option value="roi">ROI</option>
                <option value="velocity">Velocity</option>
                <option value="bsr">BSR</option>
              </select>
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ordre</label>
              <select
                value={sort.order}
                onChange={(e) => setSort({ ...sort, order: e.target.value as 'asc' | 'desc' })}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
              >
                <option value="desc">Decroissant</option>
                <option value="asc">Croissant</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {showAccordion && <th className="px-4 py-3 w-12"></th>}
              {showRank && (
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Rank
                </th>
              )}
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                ASIN
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Titre
              </th>
              {showScore && (
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
              )}
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                ROI
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                Velocity
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                BSR
              </th>
              {showRecommendation && (
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Recommandation
                </th>
              )}
              {showAmazonBadges && (
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Amazon
                </th>
              )}
              {showVerifyButton && (
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {processedProducts.map((product) => (
              <UnifiedProductRow
                key={product.asin}
                product={product}
                isExpanded={expandedRow === product.asin}
                onToggle={() => setExpandedRow(expandedRow === product.asin ? null : product.asin)}
                features={rowFeatures}
                onVerify={onVerify}
                AccordionComponent={AccordionComponent}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      {showFooterSummary && summaryStats && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>Total: {processedProducts.length} produits</span>
            <div className="flex gap-6">
              <span>
                ROI moyen: <strong className="text-green-600">{summaryStats.avgRoi.toFixed(1)}%</strong>
              </span>
              <span>
                Velocite moyenne: <strong className="text-blue-600">{summaryStats.avgVelocity.toFixed(0)}</strong>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

**Step 4: Update index.ts**

```typescript
// frontend/src/components/unified/index.ts
export { UnifiedProductRow } from './UnifiedProductRow'
export { UnifiedProductTable } from './UnifiedProductTable'
export type { UnifiedRowFeatures } from './UnifiedProductRow'
export type { UnifiedTableFeatures, UnifiedTableFilters, UnifiedTableSort } from './UnifiedProductTable'
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/UnifiedProductTable.test.tsx
```

Expected: PASS - 6 tests

**Step 6: Commit**

```bash
git add frontend/src/components/unified/
git commit -m "feat(unified): add UnifiedProductTable component

- Create main table component with filtering and sorting
- Support feature flags for columns and functionality
- Add export CSV callback and footer summary
- Include comprehensive unit tests"
```

---

## Phase 2: Extraction du Composant Verification

### Task 2.1: Extraire VerificationPanel en composant reutilisable

**Files:**
- Create: `frontend/src/components/unified/VerificationPanel.tsx`
- Create: `frontend/src/components/unified/useVerification.ts`
- Test: `frontend/src/components/unified/__tests__/VerificationPanel.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/unified/__tests__/VerificationPanel.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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
    expect(screen.getByText('$18.99')).toBeInTheDocument() // used_sell_price
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
    const withChanges = {
      ...mockVerificationResult,
      status: 'changed' as const,
      changes: [
        { field: 'price', saved_value: 20, current_value: 25, severity: 'warning' as const, message: 'Price increased by 25%' },
      ],
    }
    render(<VerificationPanel result={withChanges} />)

    expect(screen.getByText('Modifie')).toBeInTheDocument()
    expect(screen.getByText('Price increased by 25%')).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/VerificationPanel.test.tsx
```

Expected: FAIL with "Cannot find module '../VerificationPanel'"

**Step 3: Write implementation**

```typescript
// frontend/src/components/unified/VerificationPanel.tsx
/**
 * VerificationPanel - Reusable component for product verification display
 * Extracted from ProductsTable for use across all modules
 */

import type { VerificationResponse, VerificationStatus } from '../../services/verificationService'

interface VerificationPanelProps {
  result: VerificationResponse
}

const STATUS_BADGES: Record<VerificationStatus, { label: string; color: string; borderColor: string }> = {
  ok: { label: 'OK', color: 'text-green-700 bg-green-100', borderColor: 'border-green-500' },
  changed: { label: 'Modifie', color: 'text-yellow-700 bg-yellow-100', borderColor: 'border-yellow-500' },
  avoid: { label: 'Eviter', color: 'text-red-700 bg-red-100', borderColor: 'border-red-500' },
}

export function VerificationPanel({ result }: VerificationPanelProps) {
  const statusBadge = STATUS_BADGES[result.status] || STATUS_BADGES.avoid
  const buyOpportunities = result.buy_opportunities || []

  return (
    <div className={`border-l-4 ${statusBadge.borderColor} pl-4 py-3`}>
      {/* Status Badge and Message */}
      <div className="flex items-center gap-3 mb-3">
        <span className={`px-2 py-1 rounded text-xs font-semibold ${statusBadge.color}`}>
          {statusBadge.label}
        </span>
        <p className="text-sm font-medium text-gray-700">{result.message}</p>
      </div>

      {/* Current Data Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-3">
        {result.sell_price != null && (
          <div>
            <p className="text-xs text-gray-500">Prix vente NEW</p>
            <p className="text-sm font-semibold text-blue-600">${result.sell_price.toFixed(2)}</p>
          </div>
        )}
        {result.used_sell_price != null && (
          <div>
            <p className="text-xs text-gray-500">Prix vente USED</p>
            <p className="text-sm font-semibold text-purple-600">${result.used_sell_price.toFixed(2)}</p>
          </div>
        )}
        {result.current_bsr != null && (
          <div>
            <p className="text-xs text-gray-500">BSR actuel</p>
            <p className="text-sm font-semibold">#{result.current_bsr.toLocaleString()}</p>
          </div>
        )}
        {result.current_fba_count != null && result.current_fba_count >= 0 && (
          <div>
            <p className="text-xs text-gray-500">Vendeurs FBA</p>
            <p className="text-sm font-semibold">{result.current_fba_count}</p>
          </div>
        )}
        {buyOpportunities.length > 0 && (
          <div>
            <p className="text-xs text-gray-500">Opportunites</p>
            <p className="text-sm font-semibold text-green-600">{buyOpportunities.length} offres</p>
          </div>
        )}
      </div>

      {/* Amazon Warning */}
      {result.amazon_selling && (
        <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 mb-3">
          <p className="text-sm text-red-700 font-medium">
            Attention: Amazon vend ce produit directement
          </p>
        </div>
      )}

      {/* Buy Opportunities Table */}
      {buyOpportunities.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-gray-500 uppercase mb-2 font-semibold">
            Opportunites d'achat (Top {Math.min(buyOpportunities.length, 5)}):
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-2 py-1 text-left">Condition</th>
                  <th className="px-2 py-1 text-right">Prix Achat</th>
                  <th className="px-2 py-1 text-right">Livraison</th>
                  <th className="px-2 py-1 text-right">Total</th>
                  <th className="px-2 py-1 text-right">Vente</th>
                  <th className="px-2 py-1 text-right">Profit</th>
                  <th className="px-2 py-1 text-right">ROI</th>
                  <th className="px-2 py-1 text-center">FBA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {buyOpportunities.slice(0, 5).map((opp, idx) => {
                  const isNew = opp.is_new ?? opp.condition_code === 1
                  return (
                    <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                      <td className="px-2 py-1.5">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-xs font-semibold ${
                            isNew ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                          }`}
                        >
                          {isNew ? 'NEW' : 'USED'}
                        </span>
                        <span className="ml-1 text-gray-500">{opp.condition}</span>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">${opp.price.toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right font-mono text-gray-500">
                        {opp.shipping > 0 ? `+$${opp.shipping.toFixed(2)}` : 'Gratuit'}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono font-semibold">
                        ${opp.total_cost.toFixed(2)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono font-semibold text-blue-600">
                        ${opp.sell_price.toFixed(2)}
                      </td>
                      <td
                        className={`px-2 py-1.5 text-right font-mono font-semibold ${
                          opp.profit > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        ${opp.profit.toFixed(2)}
                      </td>
                      <td
                        className={`px-2 py-1.5 text-right font-mono ${
                          opp.roi_percent > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {opp.roi_percent.toFixed(0)}%
                      </td>
                      <td className="px-2 py-1.5 text-center">
                        {opp.is_fba ? (
                          <span className="text-orange-600 font-semibold">FBA</span>
                        ) : (
                          <span className="text-gray-400">FBM</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {buyOpportunities.length > 0 && (
            <p className="text-xs text-gray-500 mt-2 italic">
              Meilleure offre: Acheter a ${buyOpportunities[0].total_cost.toFixed(2)} (
              {buyOpportunities[0].is_new ? 'NEW' : 'USED'}) {'->'} Vendre a $
              {buyOpportunities[0].sell_price.toFixed(2)} = ${buyOpportunities[0].profit.toFixed(2)} profit
            </p>
          )}
        </div>
      )}

      {/* No opportunities message */}
      {buyOpportunities.length === 0 && !result.amazon_selling && (
        <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-md px-3 py-2">
          <p className="text-xs text-yellow-700">
            Aucune opportunite d'achat profitable trouvee actuellement.
          </p>
        </div>
      )}

      {/* Changes List */}
      {result.changes.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 uppercase mb-1">Changements detectes:</p>
          <ul className="space-y-1">
            {result.changes.map((change, idx) => (
              <li
                key={idx}
                className={`text-xs px-2 py-1 rounded ${
                  change.severity === 'critical'
                    ? 'bg-red-50 text-red-700'
                    : change.severity === 'warning'
                    ? 'bg-yellow-50 text-yellow-700'
                    : 'bg-gray-50 text-gray-700'
                }`}
              >
                {change.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timestamp */}
      <p className="text-xs text-gray-400 mt-3">
        Verifie le: {new Date(result.verified_at).toLocaleString()}
      </p>
    </div>
  )
}
```

**Step 4: Create useVerification hook**

```typescript
// frontend/src/components/unified/useVerification.ts
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
```

**Step 5: Update index.ts**

```typescript
// frontend/src/components/unified/index.ts
export { UnifiedProductRow } from './UnifiedProductRow'
export { UnifiedProductTable } from './UnifiedProductTable'
export { VerificationPanel } from './VerificationPanel'
export { useVerification } from './useVerification'
export type { UnifiedRowFeatures } from './UnifiedProductRow'
export type { UnifiedTableFeatures, UnifiedTableFilters, UnifiedTableSort } from './UnifiedProductTable'
```

**Step 6: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/components/unified/__tests__/VerificationPanel.test.tsx
```

Expected: PASS - 5 tests

**Step 7: Commit**

```bash
git add frontend/src/components/unified/
git commit -m "feat(unified): extract VerificationPanel as reusable component

- Create VerificationPanel from ProductsTable verification logic
- Add useVerification hook for state management
- Support all verification features: buy opportunities, changes, amazon warning
- Include unit tests"
```

---

## Phase 3: Integration dans les Modules

### Task 3.1: Integrer UnifiedProductTable dans NicheDiscovery

**Files:**
- Modify: `frontend/src/pages/NicheDiscovery.tsx`
- Modify: `frontend/src/components/niche-discovery/ProductsTable.tsx` (deprecate)
- Test: Run existing Niche Discovery tests

**Step 1: Update NicheDiscovery to use UnifiedProductTable**

```typescript
// In frontend/src/pages/NicheDiscovery.tsx
// Add imports at top:
import { UnifiedProductTable, useVerification } from '../components/unified'
import { normalizeNicheProduct, type DisplayableProduct } from '../types/unified'

// Inside component, add normalization:
const normalizedProducts = useMemo(() => {
  return products.map(normalizeNicheProduct)
}, [products])

// Add verification hook:
const { verifyProduct, getVerificationState, isVerificationExpanded, toggleVerificationExpansion } = useVerification()

// Replace ProductsTable usage with:
<UnifiedProductTable
  products={normalizedProducts}
  title={
    fromNiche
      ? `Analyse relancee: ${fromNiche.niche_name}`
      : selectedNiche
      ? `${selectedNiche.icon} ${selectedNiche.name}`
      : 'Resultats de recherche'
  }
  features={{
    showRecommendation: true,
    showCategory: true,
    showVerifyButton: true,
    showFooterSummary: true,
    showFilters: true,
    showAccordion: false, // NicheProduct doesn't have accordion content yet
  }}
  onVerify={verifyProduct}
/>
```

**Step 2: Run build to verify no errors**

```bash
cd frontend && npm run build
```

Expected: SUCCESS

**Step 3: Commit**

```bash
git add frontend/src/pages/NicheDiscovery.tsx
git commit -m "feat(niche-discovery): integrate UnifiedProductTable

- Replace ProductsTable with UnifiedProductTable
- Add product normalization with normalizeNicheProduct
- Enable verification feature via useVerification hook
- Preserve all existing functionality"
```

---

### Task 3.2: Integrer UnifiedProductTable dans AnalyseManuelle

**Files:**
- Modify: `frontend/src/pages/AnalyseManuelle.tsx`
- Test: Run build

**Step 1: Update AnalyseManuelle to use UnifiedProductTable**

```typescript
// In frontend/src/pages/AnalyseManuelle.tsx
// Add imports:
import { UnifiedProductTable } from '../components/unified'
import { normalizeProductScore, type DisplayableProduct } from '../types/unified'
import { AccordionContent } from '../components/accordions/AccordionContent'

// Update productScores conversion:
const normalizedProducts = useMemo(() => {
  if (!results) return []
  const productScores = batchResultsToProductScores(results.results)
  return productScores.map(normalizeProductScore)
}, [results])

// Replace ViewResultsTable with:
<UnifiedProductTable
  products={normalizedProducts}
  title="Analyse Manuelle - Resultats"
  features={{
    showScore: true,
    showRank: true,
    showAmazonBadges: true,
    showFilters: true,
    showExportCSV: true,
    showFooterSummary: true,
    showAccordion: true,
    showVerifyButton: true, // Now available in manual analysis too!
  }}
  onExportCSV={handleExportCSV}
  AccordionComponent={AccordionContent}
/>
```

**Step 2: Run build**

```bash
cd frontend && npm run build
```

Expected: SUCCESS

**Step 3: Commit**

```bash
git add frontend/src/pages/AnalyseManuelle.tsx
git commit -m "feat(analyse-manuelle): integrate UnifiedProductTable

- Replace ViewResultsTable with UnifiedProductTable
- Add product normalization with normalizeProductScore
- Enable accordion content and verification features
- Preserve export CSV functionality"
```

---

### Task 3.3: Integrer UnifiedProductTable dans AutoSourcing

**Files:**
- Modify: `frontend/src/pages/AutoSourcing.tsx`
- Test: Run build

**Step 1: Update AutoSourcing (manual analysis tab)**

The AutoSourcing page has two tabs - Jobs and Manual Analysis. Update the Manual Analysis tab to use UnifiedProductTable.

```typescript
// Similar pattern as AnalyseManuelle
// Add imports and replace ViewResultsTable usage
```

**Step 2: Run build**

```bash
cd frontend && npm run build
```

**Step 3: Commit**

```bash
git add frontend/src/pages/AutoSourcing.tsx
git commit -m "feat(autosourcing): integrate UnifiedProductTable

- Replace ViewResultsTable in manual analysis tab
- Maintain Jobs tab unchanged
- Add verification support"
```

---

## Phase 4: Nettoyage et Suppression Pages Obsoletes

### Task 4.1: Supprimer pages AnalyseStrategique et StockEstimates

**Files:**
- Delete: `frontend/src/pages/AnalyseStrategique.tsx`
- Delete: `frontend/src/pages/StockEstimates.tsx`
- Delete: Associated test files
- Modify: `frontend/src/App.tsx` (remove routes)
- Modify: `frontend/src/components/Layout/Layout.tsx` (remove nav links)

**Step 1: Update App.tsx - remove routes**

```typescript
// Remove these route imports and <Route> elements:
// import AnalyseStrategique from './pages/AnalyseStrategique'
// import StockEstimates from './pages/StockEstimates'
// <Route path="/analyse-strategique" element={<AnalyseStrategique />} />
// <Route path="/stock-estimates" element={<StockEstimates />} />
```

**Step 2: Update Layout.tsx - remove nav links**

```typescript
// Remove menu items for AnalyseStrategique and StockEstimates
```

**Step 3: Delete page files**

```bash
rm frontend/src/pages/AnalyseStrategique.tsx
rm frontend/src/pages/StockEstimates.tsx
rm frontend/src/pages/__tests__/AnalyseStrategique.test.tsx
rm frontend/src/pages/__tests__/StockEstimates.test.tsx
```

**Step 4: Run build**

```bash
cd frontend && npm run build
```

**Step 5: Run tests**

```bash
cd frontend && npm run test
```

**Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove AnalyseStrategique and StockEstimates pages

- Remove redundant pages as per external validation feedback
- Strategic signals integrated into UnifiedProductTable
- Stock estimates available via verification feature
- Update routes and navigation

BREAKING CHANGE: /analyse-strategique and /stock-estimates routes removed"
```

---

### Task 4.2: Deprecate ancien ViewResultsTable et ProductsTable

**Files:**
- Modify: `frontend/src/components/ViewResultsTable.tsx` (add deprecation notice)
- Modify: `frontend/src/components/niche-discovery/ProductsTable.tsx` (add deprecation notice)

**Step 1: Add deprecation comments**

```typescript
// At top of both files:
/**
 * @deprecated Use UnifiedProductTable from components/unified instead.
 * This component is kept for backward compatibility and will be removed in Phase 11.
 */
```

**Step 2: Commit**

```bash
git add frontend/src/components/ViewResultsTable.tsx frontend/src/components/niche-discovery/ProductsTable.tsx
git commit -m "chore: deprecate ViewResultsTable and ProductsTable

- Add deprecation notices pointing to UnifiedProductTable
- Components kept for backward compatibility
- Will be removed in Phase 11 cleanup"
```

---

## Verification Finale

### Task 5.1: Run all tests

```bash
cd frontend && npm run test
```

Expected: All tests pass

### Task 5.2: Run build

```bash
cd frontend && npm run build
```

Expected: SUCCESS with no TypeScript errors

### Task 5.3: Manual E2E verification

Test the following flows manually:
1. Analyse Manuelle: Upload CSV, run analysis, verify table displays
2. Niche Discovery: Click strategy, explore niche, verify products table
3. AutoSourcing: Run manual analysis, verify table displays
4. Verification: Click "Verifier" button in any module, verify panel displays

---

## Summary

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Types + UnifiedProductRow + UnifiedProductTable | 2h |
| Phase 2 | VerificationPanel extraction | 1h |
| Phase 3 | Integration 3 modules | 2h |
| Phase 4 | Cleanup + remove pages | 1h |
| Phase 5 | Verification | 30min |
| **Total** | | **~6.5h** |
