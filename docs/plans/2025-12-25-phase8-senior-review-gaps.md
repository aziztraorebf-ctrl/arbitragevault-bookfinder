# Phase 8 Senior Review - Gap Closure Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Combler les gaps identifies lors de l'audit senior de la Phase 8 Advanced Analytics.

**Architecture:** Tests de coherence inter-services, tests hook frontend, golden tests avec donnees reelles, documentation des seuils business.

**Tech Stack:** pytest, vitest, React Testing Library

---

## Task 1: Tests de coherence inter-services (4 tests)

**Fichiers:**
- Create: `backend/tests/integration/test_analytics_coherence.py`

**Objectif:** Verifier que les services ne produisent pas de recommandations absurdes quand combines.

**Tests a implementer:**

1. `test_high_risk_cannot_be_strong_buy` - Un produit avec risk_score > 70 ne doit JAMAIS etre STRONG_BUY
2. `test_low_velocity_low_roi_gives_skip` - Velocity < 30 ET ROI < 15% doit donner SKIP ou AVOID
3. `test_amazon_buybox_overrides_good_metrics` - Amazon avec BuyBox doit forcer AVOID meme si ROI=100%
4. `test_all_green_metrics_gives_positive_recommendation` - Tous bons indicateurs = BUY ou STRONG_BUY

**Code:**

```python
"""
Coherence tests for Phase 8 Analytics services.
Ensures services work together logically and don't produce absurd recommendations.
"""
import pytest
from decimal import Decimal

from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.risk_scoring_service import RiskScoringService
from app.services.recommendation_engine_service import RecommendationEngineService


class TestAnalyticsCoherence:
    """Test that analytics services produce coherent results when combined."""

    def test_high_risk_cannot_be_strong_buy(self):
        """A product with risk_score > 70 should NEVER be STRONG_BUY."""
        # Setup: Create a scenario with artificially high risk
        price_stability = {'stability_score': 20}  # Very unstable
        dead_inventory = {'is_dead_risk': True, 'risk_score': 80}

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=200000,  # High BSR
            category='books',
            seller_count=50,  # Many sellers
            amazon_on_listing=True,  # Amazon present
            price_stability_data=price_stability,
            dead_inventory_data=dead_inventory
        )

        # Now generate recommendation with this high risk
        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_1',
            title='High Risk Test',
            roi_net=50.0,  # Even good ROI
            velocity_score=80.0,  # Even good velocity
            risk_score=risk_data['total_risk_score'],
            price_stability_score=20.0,
            amazon_on_listing=True,
            amazon_has_buybox=False,
            estimated_sell_price=30.0,
            estimated_buy_price=10.0
        )

        # COHERENCE CHECK: High risk should prevent STRONG_BUY
        assert recommendation['recommendation'] != 'STRONG_BUY', \
            f"High risk ({risk_data['total_risk_score']}) should not result in STRONG_BUY"

    def test_low_velocity_low_roi_gives_skip(self):
        """Very poor metrics should result in SKIP or AVOID."""
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=500000,  # Very high BSR = slow sales
            bsr_history=[],
            category='books'
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('15.00'),
            estimated_sell_price=Decimal('16.00'),  # Tiny margin
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_2',
            title='Poor Metrics Test',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=60.0,
            price_stability_score=40.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=16.0,
            estimated_buy_price=15.0
        )

        # COHERENCE CHECK: Poor metrics should not recommend buying
        assert recommendation['recommendation'] in ['SKIP', 'AVOID', 'WATCH'], \
            f"Poor metrics should give SKIP/AVOID/WATCH, got {recommendation['recommendation']}"

    def test_amazon_buybox_overrides_good_metrics(self):
        """Amazon with BuyBox should force AVOID regardless of other metrics."""
        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_3',
            title='Amazon BuyBox Override Test',
            roi_net=150.0,  # Excellent ROI
            velocity_score=95.0,  # Excellent velocity
            risk_score=10.0,  # Low risk
            price_stability_score=95.0,  # Very stable
            amazon_on_listing=True,
            amazon_has_buybox=True,  # THE KILLER
            estimated_sell_price=50.0,
            estimated_buy_price=10.0
        )

        # COHERENCE CHECK: Amazon BuyBox is an absolute blocker
        assert recommendation['recommendation'] == 'AVOID', \
            f"Amazon BuyBox should force AVOID, got {recommendation['recommendation']}"

    def test_all_green_metrics_gives_positive_recommendation(self):
        """All positive indicators should result in BUY or STRONG_BUY."""
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=5000,  # Excellent BSR
            bsr_history=[],
            category='books'
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('5.00'),
            estimated_sell_price=Decimal('25.00'),  # Great margin
        )

        price_stability = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 25.0}, {'price': 24.5}, {'price': 25.5}]
        )

        dead_inventory = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=5000,
            category='books'
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=5000,
            category='books',
            seller_count=3,  # Low competition
            amazon_on_listing=False,
            price_stability_data=price_stability,
            dead_inventory_data=dead_inventory
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_4',
            title='All Green Test',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=risk_data['total_risk_score'],
            price_stability_score=price_stability['stability_score'],
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=25.0,
            estimated_buy_price=5.0,
            seller_count=3,
            breakeven_days=20
        )

        # COHERENCE CHECK: All green should recommend buying
        assert recommendation['recommendation'] in ['BUY', 'STRONG_BUY'], \
            f"All green metrics should give BUY/STRONG_BUY, got {recommendation['recommendation']}"
```

**Run:** `cd backend && pytest tests/integration/test_analytics_coherence.py -v`

**Expected:** 4 passed

---

## Task 2: Tests hook useProductDecision (4 tests)

**Fichiers:**
- Create: `frontend/src/hooks/__tests__/useProductDecision.test.tsx`

**Objectif:** Verifier que le hook React qui appelle l'API analytics fonctionne correctement.

**Tests a implementer:**

1. `test_hook_returns_loading_initially` - Le hook retourne isLoading=true au debut
2. `test_hook_returns_data_on_success` - Le hook retourne les data apres succes API
3. `test_hook_handles_error` - Le hook gere les erreurs API correctement
4. `test_hook_not_called_without_params` - Le hook ne fait pas d'appel si params manquants

**Code:**

```typescript
/**
 * Tests for useProductDecision hook
 * Phase 8 Senior Review
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the API module
vi.mock('../../api/analytics', () => ({
  fetchProductDecision: vi.fn()
}))

import { useProductDecision } from '../useProductDecision'
import { fetchProductDecision } from '../../api/analytics'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useProductDecision', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading state initially when params provided', async () => {
    ;(fetchProductDecision as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    const { result } = renderHook(
      () => useProductDecision({
        asin: 'TEST123',
        estimatedBuyPrice: 10,
        estimatedSellPrice: 25
      }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()
  })

  it('returns data on successful API call', async () => {
    const mockData = {
      asin: 'TEST123',
      recommendation: 'BUY',
      confidence_percent: 75,
      velocity: { velocity_score: 80 },
      risk: { risk_score: 30 }
    }

    ;(fetchProductDecision as any).mockResolvedValue(mockData)

    const { result } = renderHook(
      () => useProductDecision({
        asin: 'TEST123',
        estimatedBuyPrice: 10,
        estimatedSellPrice: 25
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.data?.recommendation).toBe('BUY')
  })

  it('handles API error correctly', async () => {
    ;(fetchProductDecision as any).mockRejectedValue(new Error('API Error'))

    const { result } = renderHook(
      () => useProductDecision({
        asin: 'TEST123',
        estimatedBuyPrice: 10,
        estimatedSellPrice: 25
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })

  it('does not fetch when params are missing', () => {
    const { result } = renderHook(
      () => useProductDecision({
        asin: '',  // Empty ASIN
        estimatedBuyPrice: 0,
        estimatedSellPrice: 0
      }),
      { wrapper: createWrapper() }
    )

    // Should not be loading because query is disabled
    expect(result.current.isLoading).toBe(false)
    expect(fetchProductDecision).not.toHaveBeenCalled()
  })
})
```

**Run:** `cd frontend && npm run test -- --run src/hooks/__tests__/useProductDecision.test.tsx`

**Expected:** 4 passed

---

## Task 3: Golden tests avec vrais ASINs (3 tests)

**Fichiers:**
- Create: `backend/tests/integration/test_analytics_golden.py`

**Objectif:** Valider que les calculs sont coherents pour des ASINs reels avec comportement connu.

**Tests a implementer:**

1. `test_low_bsr_book_high_velocity` - BSR < 10000 doit donner velocity_score >= 80
2. `test_high_bsr_book_low_velocity` - BSR > 100000 doit donner velocity_score < 50
3. `test_roi_calculation_accuracy` - ROI calcule doit matcher la formule attendue

**Code:**

```python
"""
Golden tests for Phase 8 Analytics.
These tests use realistic values to validate business logic correctness.
"""
import pytest
from decimal import Decimal

from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.recommendation_engine_service import RecommendationEngineService


class TestAnalyticsGolden:
    """Golden tests with realistic book arbitrage scenarios."""

    def test_low_bsr_book_high_velocity(self):
        """
        BUSINESS RULE: A book with BSR < 10,000 sells quickly.
        Expected: velocity_score >= 80 (good velocity)

        Real-world context: BSR 5000 in Books means roughly top 0.01% of sales,
        typically sells within days.
        """
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=5000,
            bsr_history=[],
            category='books'
        )

        assert result['velocity_score'] >= 80, \
            f"BSR 5000 should have velocity >= 80, got {result['velocity_score']}"
        assert result['risk_level'] == 'LOW', \
            f"BSR 5000 should be LOW risk, got {result['risk_level']}"

    def test_high_bsr_book_indicates_slow_sales(self):
        """
        BUSINESS RULE: A book with BSR > 100,000 sells slowly.
        Expected: This is detected as potential slow-moving inventory.

        Real-world context: BSR 150,000 in Books might take weeks/months to sell.
        """
        dead_inventory = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=150000,
            category='books'
        )

        # BSR 150k > threshold 50k for books = dead inventory risk
        assert dead_inventory['is_dead_risk'] == True, \
            f"BSR 150000 should be flagged as dead inventory risk"
        assert dead_inventory['threshold'] == 50000, \
            f"Books threshold should be 50000, got {dead_inventory['threshold']}"

    def test_roi_calculation_accuracy(self):
        """
        BUSINESS RULE: ROI must be calculated correctly with all fees.

        Scenario: Buy at $5, Sell at $20
        - Gross profit: $15
        - Referral fee (15%): $3.00
        - FBA fee: $2.50
        - Storage (1 month): $0.87
        - Returns (2%): $0.40
        - Total fees: ~$6.77
        - Net profit: ~$8.23
        - ROI: ~164.6%
        """
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('5.00'),
            estimated_sell_price=Decimal('20.00'),
            referral_fee_percent=Decimal('15'),
            fba_fee=Decimal('2.50'),
            return_rate_percent=Decimal('2'),
            storage_cost_monthly=Decimal('0.87'),
            sale_cycle_days=30
        )

        # Verify gross profit
        assert result['gross_profit'] == 15.0, \
            f"Gross profit should be 15.0, got {result['gross_profit']}"

        # Verify referral fee (15% of $20 = $3)
        assert result['referral_fee'] == 3.0, \
            f"Referral fee should be 3.0, got {result['referral_fee']}"

        # Verify FBA fee
        assert result['fba_fee'] == 2.5, \
            f"FBA fee should be 2.5, got {result['fba_fee']}"

        # Verify net profit is positive and reasonable
        assert result['net_profit'] > 7.0, \
            f"Net profit should be > 7.0, got {result['net_profit']}"
        assert result['net_profit'] < 10.0, \
            f"Net profit should be < 10.0, got {result['net_profit']}"

        # Verify ROI percentage (net_profit / buy_price * 100)
        expected_roi_min = 140  # Minimum expected
        expected_roi_max = 180  # Maximum expected
        assert expected_roi_min <= result['roi_percentage'] <= expected_roi_max, \
            f"ROI should be between {expected_roi_min}-{expected_roi_max}%, got {result['roi_percentage']}"
```

**Run:** `cd backend && pytest tests/integration/test_analytics_golden.py -v`

**Expected:** 3 passed

---

## Task 4: Documentation des seuils business (1 fichier)

**Fichiers:**
- Create: `docs/PHASE8_BUSINESS_THRESHOLDS.md`

**Objectif:** Documenter l'origine et la justification de chaque seuil utilise dans Phase 8.

**Contenu:**

```markdown
# Phase 8 - Business Thresholds Documentation

Ce document explique les seuils utilises dans les services Phase 8 Advanced Analytics.

## 1. Dead Inventory Thresholds (BSR)

| Categorie | Seuil BSR | Justification |
|-----------|-----------|---------------|
| books | 50,000 | Livres au-dela de ce BSR peuvent prendre > 30 jours a vendre |
| textbooks | 30,000 | Textbooks ont un marche plus restreint, seuil plus strict |
| general | 100,000 | Seuil par defaut pour categories non specifiees |

**Source:** Experience empirique du marche Amazon FBA Books. A valider avec donnees historiques de ventes reelles.

**Fichier:** `backend/app/services/advanced_analytics_service.py:18-22`

## 2. Recommendation Thresholds

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| MIN_ROI_THRESHOLD | 30% | ROI minimum pour couvrir les impr vus et garantir profit |
| GOOD_VELOCITY_THRESHOLD | 70 | Score velocity indiquant ventes rapides (< 2 semaines) |
| ACCEPTABLE_RISK_THRESHOLD | 50 | Score risque au-dela duquel prudence necessaire |
| MAX_SALE_CYCLE_DAYS | 45 | Delai max acceptable avant frais stockage long terme |

**Source:** Standards industrie FBA arbitrage. MIN_ROI 30% est un consensus communaute resellers.

**Fichier:** `backend/app/services/recommendation_engine_service.py:22-25`

## 3. Risk Scoring Weights

| Composant | Poids | Justification |
|-----------|-------|---------------|
| dead_inventory | 35% | Risque principal: produit qui ne se vend pas |
| competition | 25% | Beaucoup de vendeurs = guerre des prix |
| amazon_presence | 20% | Amazon sur listing = tres difficile de gagner BuyBox |
| price_stability | 10% | Prix volatils = marges imprevisibles |
| category | 10% | Certaines categories plus risquees |

**Source:** Ponderation basee sur impact relatif sur profitabilite. Dead inventory est le risque #1.

**Fichier:** `backend/app/services/risk_scoring_service.py:14-20`

## 4. Amazon Risk Values

| Scenario | Score | Justification |
|----------|-------|---------------|
| Amazon present | 95 | Quasi-impossible de concurrencer Amazon sur ses listings |
| Amazon absent | 5 | Risque residuel (Amazon peut revenir) |

**Fichier:** `backend/app/services/risk_scoring_service.py:162-164`

## 5. Recommendations pour validation future

1. **Collecter donnees reelles**: Tracker les ventes reelles vs predictions pour valider les seuils
2. **A/B testing**: Tester differents seuils sur un sous-ensemble de recommandations
3. **Feedback utilisateur**: Permettre aux utilisateurs de reporter si une recommandation etait correcte
4. **Revue trimestrielle**: Revoir les seuils tous les 3 mois avec nouvelles donnees

## Historique des modifications

| Date | Modification | Auteur |
|------|--------------|--------|
| 2025-12-25 | Documentation initiale | Claude Code Audit |
```

**Validation:** Fichier cree et lisible.

---

## Execution

**Commande globale de validation:**

```bash
# Backend
cd backend && pytest tests/integration/test_analytics_coherence.py tests/integration/test_analytics_golden.py -v

# Frontend
cd frontend && npm run test -- --run src/hooks/__tests__/useProductDecision.test.tsx
```

**Total nouveaux tests:** 11 tests (4 coherence + 4 hook + 3 golden)
