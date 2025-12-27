# Phase 8 Advanced Analytics - Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Auditer et valider la Phase 8 Advanced Analytics deployee mais non testee, en ajoutant tests unitaires hostiles, tests integration, et tests E2E Playwright.

**Architecture:**
- Backend: 4 endpoints analytics (`/calculate-analytics`, `/calculate-risk-score`, `/generate-recommendation`, `/product-decision`)
- Backend: 3 endpoints ASIN history (`/trends/{asin}`, `/records/{asin}`, `/latest/{asin}`)
- Services: AdvancedAnalyticsService, RiskScoringService, RecommendationEngineService, ASINTrackingService
- Frontend: TokenErrorAlert component, useProductDecision hook, tokenErrorHandler utils
- Models: ASINHistory, RunHistory, DecisionOutcome

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic, React, TypeScript, Playwright, Pytest

**Prerequisites:** Phase 7 complete (121 tests passing), production API accessible

**Token Cost:** ~30 tokens pour tests E2E production (appels Keepa indirects)

---

## Inventaire Phase 8 Existant

### Backend Endpoints (Deployes)
| Endpoint | Methode | Fichier | Tests Existants |
|----------|---------|---------|-----------------|
| `/api/v1/analytics/calculate-analytics` | POST | `app/api/v1/endpoints/analytics.py:23` | AUCUN |
| `/api/v1/analytics/calculate-risk-score` | POST | `app/api/v1/endpoints/analytics.py:80` | AUCUN |
| `/api/v1/analytics/generate-recommendation` | POST | `app/api/v1/endpoints/analytics.py:138` | AUCUN |
| `/api/v1/analytics/product-decision` | POST | `app/api/v1/endpoints/analytics.py:214` | E2E only |
| `/api/v1/asin-history/trends/{asin}` | GET | `app/api/v1/endpoints/asin_history.py:19` | E2E only |
| `/api/v1/asin-history/records/{asin}` | GET | `app/api/v1/endpoints/asin_history.py:100` | AUCUN |
| `/api/v1/asin-history/latest/{asin}` | GET | `app/api/v1/endpoints/asin_history.py:149` | AUCUN |

### Backend Services (Deployes)
| Service | Fichier | Tests Existants |
|---------|---------|-----------------|
| AdvancedAnalyticsService | `app/services/advanced_analytics_service.py` | AUCUN |
| RiskScoringService | `app/services/risk_scoring_service.py` | AUCUN |
| RecommendationEngineService | `app/services/recommendation_engine_service.py` | AUCUN |
| ASINTrackingService | `app/services/asin_tracking_service.py` | AUCUN |

### Frontend Components (Deployes)
| Component | Fichier | Tests Existants |
|-----------|---------|-----------------|
| TokenErrorAlert | `frontend/src/components/TokenErrorAlert.tsx` | AUCUN |
| useProductDecision | `frontend/src/hooks/useProductDecision.ts` | AUCUN |
| tokenErrorHandler | `frontend/src/utils/tokenErrorHandler.ts` | AUCUN |

### E2E Tests Existants
- `backend/tests/e2e/tests/09-phase-8-decision-system.spec.js` (5 tests)

---

## Task 1: Tests Unitaires Hostiles - AdvancedAnalyticsService

**Goal:** Tester calculs velocity, price stability, ROI, competition avec edge cases

**Files:**
- Create: `backend/tests/unit/test_advanced_analytics_hostile.py`
- Read: `backend/app/services/advanced_analytics_service.py`

### Step 1.1: Lire le service pour comprendre les methodes

Run:
```bash
cd backend && cat app/services/advanced_analytics_service.py | head -100
```

### Step 1.2: Ecrire les tests hostiles velocity

Create: `backend/tests/unit/test_advanced_analytics_hostile.py`

```python
"""
Phase 8 Audit: Tests unitaires hostiles pour AdvancedAnalyticsService.
Teste edge cases, divisions par zero, valeurs nulles, extremes.
"""
import pytest
from decimal import Decimal
from app.services.advanced_analytics_service import AdvancedAnalyticsService


class TestVelocityIntelligenceHostile:
    """Tests hostiles pour calculate_velocity_intelligence."""

    def test_velocity_with_zero_bsr(self):
        """BSR=0 ne doit pas causer division par zero."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=0,
            bsr_history=[],
            category='books'
        )
        assert 'velocity_score' in result
        assert result['velocity_score'] >= 0

    def test_velocity_with_none_bsr(self):
        """BSR=None doit retourner score par defaut."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=None,
            bsr_history=[],
            category='books'
        )
        assert result['velocity_score'] == 0 or result['risk_level'] == 'UNKNOWN'

    def test_velocity_with_extreme_high_bsr(self):
        """BSR=10M doit retourner velocity tres bas."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=10_000_000,
            bsr_history=[],
            category='books'
        )
        assert result['velocity_score'] <= 20
        assert result['risk_level'] in ['HIGH', 'CRITICAL']

    def test_velocity_with_empty_history(self):
        """Histoire vide ne doit pas crasher."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=50000,
            bsr_history=[],
            category='books'
        )
        assert result is not None
        assert result['trend_7d'] is None or isinstance(result['trend_7d'], (int, float))

    def test_velocity_with_unknown_category(self):
        """Categorie inconnue doit utiliser defaults."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=50000,
            bsr_history=[],
            category='unknown_category_xyz'
        )
        assert 'velocity_score' in result


class TestPriceStabilityHostile:
    """Tests hostiles pour calculate_price_stability_score."""

    def test_stability_with_empty_history(self):
        """Histoire vide doit retourner score neutre."""
        result = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[]
        )
        assert 'stability_score' in result
        assert result['stability_score'] >= 0

    def test_stability_with_single_price(self):
        """Un seul prix = stabilite parfaite."""
        result = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 19.99}]
        )
        assert result['stability_score'] >= 80

    def test_stability_with_identical_prices(self):
        """Tous prix identiques = pas de volatilite."""
        result = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 19.99} for _ in range(10)]
        )
        assert result['coefficient_variation'] == 0 or result['coefficient_variation'] is None
        assert result['price_volatility'] == 'LOW'

    def test_stability_with_extreme_volatility(self):
        """Prix variant 1$ a 100$ = volatilite extreme."""
        result = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 1.0}, {'price': 100.0}, {'price': 1.0}]
        )
        assert result['stability_score'] < 50
        assert result['price_volatility'] in ['HIGH', 'EXTREME']

    def test_stability_with_zero_prices(self):
        """Prix a 0 ne doit pas causer division par zero."""
        result = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 0.0}, {'price': 19.99}]
        )
        assert result is not None


class TestROINetHostile:
    """Tests hostiles pour calculate_roi_net."""

    def test_roi_with_zero_buy_price(self):
        """Prix achat=0 ne doit pas crasher (division par zero)."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('0'),
            estimated_sell_price=Decimal('19.99')
        )
        # Soit infinite ROI, soit erreur gracieuse
        assert result is not None

    def test_roi_with_negative_margin(self):
        """Marge negative doit retourner ROI negatif."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('20.00'),
            estimated_sell_price=Decimal('10.00')
        )
        assert result['roi_percentage'] < 0
        assert result['net_profit'] < 0

    def test_roi_with_equal_prices(self):
        """Prix egaux = ROI tres negatif (frais seulement)."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('19.99'),
            estimated_sell_price=Decimal('19.99')
        )
        assert result['roi_percentage'] < 0

    def test_roi_with_very_high_fees(self):
        """Frais eleves mangent tout le profit."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('10.00'),
            estimated_sell_price=Decimal('15.00'),
            referral_fee_percent=Decimal('25'),
            fba_fee=Decimal('5.00'),
            prep_fee=Decimal('2.00')
        )
        assert result['total_fees'] > 0
        # Verifier que ROI reflete bien les frais

    def test_roi_calculation_accuracy(self):
        """Verifier exactitude calcul ROI."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('5.00'),
            estimated_sell_price=Decimal('20.00'),
            referral_fee_percent=Decimal('15'),
            fba_fee=Decimal('2.50'),
            prep_fee=Decimal('0'),
            return_rate_percent=Decimal('0'),
            storage_cost_monthly=Decimal('0'),
            sale_cycle_days=30
        )
        # Referral = 20 * 0.15 = 3.00
        # Gross = 20 - 5 = 15.00
        # Net = 15 - 3 - 2.50 = 9.50
        # ROI = 9.50 / 5 * 100 = 190%
        assert 180 <= result['roi_percentage'] <= 200


class TestCompetitionScoreHostile:
    """Tests hostiles pour calculate_competition_score."""

    def test_competition_with_zero_sellers(self):
        """Aucun vendeur = pas de competition."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=0,
            fba_seller_count=0,
            amazon_on_listing=False
        )
        assert result['competition_score'] <= 20
        assert result['competition_level'] == 'LOW'

    def test_competition_with_amazon_present(self):
        """Amazon present = risque eleve."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=5,
            fba_seller_count=3,
            amazon_on_listing=True
        )
        assert result['amazon_risk'] in ['HIGH', 'CRITICAL']

    def test_competition_with_many_fba_sellers(self):
        """50+ vendeurs FBA = competition extreme."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=50,
            fba_seller_count=40,
            amazon_on_listing=False
        )
        assert result['competition_level'] in ['HIGH', 'EXTREME']

    def test_competition_with_none_values(self):
        """Valeurs None doivent etre gerees."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=None,
            fba_seller_count=None,
            amazon_on_listing=None
        )
        assert result is not None


class TestDeadInventoryHostile:
    """Tests hostiles pour detect_dead_inventory."""

    def test_dead_inventory_books_high_bsr(self):
        """BSR > 3M pour books = dead inventory."""
        result = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=4_000_000,
            category='books',
            seller_count=5
        )
        assert result['is_dead_risk'] == True

    def test_dead_inventory_low_bsr(self):
        """BSR < 100k pour books = pas dead."""
        result = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=50000,
            category='books',
            seller_count=5
        )
        assert result['is_dead_risk'] == False

    def test_dead_inventory_none_bsr(self):
        """BSR None doit etre gere."""
        result = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=None,
            category='books',
            seller_count=5
        )
        assert result is not None
```

### Step 1.3: Executer tests pour verifier echecs attendus

Run:
```bash
cd backend && pytest tests/unit/test_advanced_analytics_hostile.py -v --tb=short
```

Expected: Certains tests peuvent echouer si edge cases non geres

### Step 1.4: Corriger les edge cases dans le service si necessaire

Si tests echouent, corriger dans `app/services/advanced_analytics_service.py`

### Step 1.5: Commit tests hostiles analytics

```bash
git add backend/tests/unit/test_advanced_analytics_hostile.py
git commit -m "test(phase8): add hostile tests for AdvancedAnalyticsService

- Test velocity with zero/none BSR, extreme values
- Test price stability edge cases (empty, single, zero)
- Test ROI with division by zero, negative margins
- Test competition with none values, Amazon presence
- Test dead inventory detection

Phase 8 Audit - Task 1 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Tests Unitaires Hostiles - RiskScoringService

**Goal:** Tester calcul risk score 5-composants avec edge cases

**Files:**
- Create: `backend/tests/unit/test_risk_scoring_hostile.py`
- Read: `backend/app/services/risk_scoring_service.py`

### Step 2.1: Ecrire les tests hostiles risk scoring

Create: `backend/tests/unit/test_risk_scoring_hostile.py`

```python
"""
Phase 8 Audit: Tests unitaires hostiles pour RiskScoringService.
Teste calcul risk score avec 5 composants ponderes.
"""
import pytest
from app.services.risk_scoring_service import RiskScoringService


class TestRiskScoreCalculationHostile:
    """Tests hostiles pour calculate_risk_score."""

    def test_risk_score_all_low_risk(self):
        """Tous indicateurs positifs = risk score bas."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=3,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 90, 'price_volatility': 'LOW'},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 10}
        )
        assert result['total_risk_score'] < 30
        assert result['risk_level'] == 'LOW'

    def test_risk_score_all_high_risk(self):
        """Tous indicateurs negatifs = risk score eleve."""
        result = RiskScoringService.calculate_risk_score(
            bsr=5_000_000,
            category='books',
            seller_count=50,
            amazon_on_listing=True,
            price_stability_data={'stability_score': 20, 'price_volatility': 'HIGH'},
            dead_inventory_data={'is_dead_risk': True, 'risk_score': 90}
        )
        assert result['total_risk_score'] > 70
        assert result['risk_level'] in ['HIGH', 'CRITICAL']

    def test_risk_score_with_none_data(self):
        """Donnees None doivent etre gerees gracieusement."""
        result = RiskScoringService.calculate_risk_score(
            bsr=None,
            category='books',
            seller_count=None,
            amazon_on_listing=None,
            price_stability_data=None,
            dead_inventory_data=None
        )
        assert result is not None
        assert 'total_risk_score' in result

    def test_risk_components_sum_to_100(self):
        """Verifier que poids des composants = 100%."""
        result = RiskScoringService.calculate_risk_score(
            bsr=50000,
            category='books',
            seller_count=5,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 70, 'price_volatility': 'MEDIUM'},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 30}
        )
        total_weight = sum(c['weight'] for c in result['components'].values())
        assert 99 <= total_weight <= 101  # Allow rounding

    def test_risk_level_thresholds(self):
        """Verifier seuils risk_level."""
        # LOW < 30
        low = RiskScoringService.calculate_risk_score(
            bsr=10000, category='books', seller_count=2,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 90, 'price_volatility': 'LOW'},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 10}
        )

        # HIGH >= 60
        high = RiskScoringService.calculate_risk_score(
            bsr=2_000_000, category='books', seller_count=30,
            amazon_on_listing=True,
            price_stability_data={'stability_score': 30, 'price_volatility': 'HIGH'},
            dead_inventory_data={'is_dead_risk': True, 'risk_score': 80}
        )

        assert low['risk_level'] == 'LOW'
        assert high['risk_level'] in ['HIGH', 'CRITICAL']


class TestRiskRecommendationsHostile:
    """Tests hostiles pour get_risk_recommendations."""

    def test_recommendations_for_low_risk(self):
        """Risk bas doit recommander achat."""
        result = RiskScoringService.get_risk_recommendations(
            risk_score=15,
            risk_level='LOW'
        )
        assert 'proceed' in result.lower() or 'buy' in result.lower()

    def test_recommendations_for_critical_risk(self):
        """Risk critique doit recommander eviter."""
        result = RiskScoringService.get_risk_recommendations(
            risk_score=90,
            risk_level='CRITICAL'
        )
        assert 'avoid' in result.lower() or 'skip' in result.lower()

    def test_recommendations_not_empty(self):
        """Recommendations ne doivent pas etre vides."""
        for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            result = RiskScoringService.get_risk_recommendations(
                risk_score=50,
                risk_level=level
            )
            assert len(result) > 10
```

### Step 2.2: Executer tests

Run:
```bash
cd backend && pytest tests/unit/test_risk_scoring_hostile.py -v --tb=short
```

### Step 2.3: Commit tests risk scoring

```bash
git add backend/tests/unit/test_risk_scoring_hostile.py
git commit -m "test(phase8): add hostile tests for RiskScoringService

- Test risk score calculation with all low/high risk
- Test None handling for all parameters
- Test component weights sum to 100%
- Test risk level thresholds
- Test recommendations output

Phase 8 Audit - Task 2 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Tests Unitaires Hostiles - RecommendationEngineService

**Goal:** Tester generation recommandations 5-tier

**Files:**
- Create: `backend/tests/unit/test_recommendation_engine_hostile.py`
- Read: `backend/app/services/recommendation_engine_service.py`

### Step 3.1: Ecrire les tests hostiles recommendation

Create: `backend/tests/unit/test_recommendation_engine_hostile.py`

```python
"""
Phase 8 Audit: Tests unitaires hostiles pour RecommendationEngineService.
Teste generation recommandations avec systeme 5-tier.
"""
import pytest
from app.services.recommendation_engine_service import RecommendationEngineService


class TestRecommendationGenerationHostile:
    """Tests hostiles pour generate_recommendation."""

    def test_strong_buy_all_criteria_met(self):
        """Tous criteres positifs = STRONG_BUY."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567',
            title='Test Book',
            roi_net=50.0,
            velocity_score=85.0,
            risk_score=15.0,
            price_stability_score=90.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=20.00,
            estimated_buy_price=5.00,
            seller_count=3,
            breakeven_days=20
        )
        assert result['recommendation'] == 'STRONG_BUY'
        assert result['confidence_percent'] >= 80

    def test_avoid_all_criteria_failed(self):
        """Tous criteres negatifs = AVOID."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567',
            title='Test Book',
            roi_net=-10.0,
            velocity_score=15.0,
            risk_score=85.0,
            price_stability_score=20.0,
            amazon_on_listing=True,
            amazon_has_buybox=True,
            estimated_sell_price=12.00,
            estimated_buy_price=10.00,
            seller_count=50,
            breakeven_days=120
        )
        assert result['recommendation'] in ['SKIP', 'AVOID']
        assert result['confidence_percent'] >= 70

    def test_recommendation_with_amazon_buybox(self):
        """Amazon avec buybox = penalite forte."""
        with_amazon = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title='Test',
            roi_net=40.0, velocity_score=70.0, risk_score=30.0,
            price_stability_score=80.0,
            amazon_on_listing=True, amazon_has_buybox=True,
            estimated_sell_price=20.00, estimated_buy_price=8.00,
            seller_count=5, breakeven_days=30
        )

        without_amazon = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title='Test',
            roi_net=40.0, velocity_score=70.0, risk_score=30.0,
            price_stability_score=80.0,
            amazon_on_listing=False, amazon_has_buybox=False,
            estimated_sell_price=20.00, estimated_buy_price=8.00,
            seller_count=5, breakeven_days=30
        )

        # Sans Amazon doit avoir meilleure recommendation
        tiers = ['AVOID', 'SKIP', 'WATCH', 'CONSIDER', 'BUY', 'STRONG_BUY']
        assert tiers.index(without_amazon['recommendation']) >= tiers.index(with_amazon['recommendation'])

    def test_recommendation_with_edge_roi(self):
        """ROI au seuil (30%) doit etre gere correctement."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title='Test',
            roi_net=30.0,  # Exactement au seuil
            velocity_score=70.0, risk_score=40.0,
            price_stability_score=70.0,
            amazon_on_listing=False, amazon_has_buybox=False,
            estimated_sell_price=15.00, estimated_buy_price=10.00,
            seller_count=5, breakeven_days=30
        )
        assert result['recommendation'] in ['CONSIDER', 'BUY', 'WATCH']

    def test_recommendation_output_structure(self):
        """Verifier structure complete du retour."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title='Test Book',
            roi_net=40.0, velocity_score=70.0, risk_score=30.0,
            price_stability_score=80.0,
            amazon_on_listing=False, amazon_has_buybox=False,
            estimated_sell_price=20.00, estimated_buy_price=8.00,
            seller_count=5, breakeven_days=30
        )

        required_fields = [
            'asin', 'title', 'recommendation', 'confidence_percent',
            'criteria_passed', 'criteria_total', 'reason',
            'roi_net', 'velocity_score', 'risk_score',
            'profit_per_unit', 'suggested_action', 'next_steps'
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_recommendation_with_none_values(self):
        """Valeurs None doivent etre gerees."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title=None,
            roi_net=40.0, velocity_score=70.0, risk_score=30.0,
            price_stability_score=80.0,
            amazon_on_listing=None, amazon_has_buybox=None,
            estimated_sell_price=20.00, estimated_buy_price=8.00,
            seller_count=None, breakeven_days=None
        )
        assert result is not None
        assert result['recommendation'] in ['STRONG_BUY', 'BUY', 'CONSIDER', 'WATCH', 'SKIP', 'AVOID']

    def test_profit_per_unit_calculation(self):
        """Verifier calcul profit par unite."""
        result = RecommendationEngineService.generate_recommendation(
            asin='B001234567', title='Test',
            roi_net=100.0,  # 100% ROI = profit = buy_price
            velocity_score=70.0, risk_score=30.0,
            price_stability_score=80.0,
            amazon_on_listing=False, amazon_has_buybox=False,
            estimated_sell_price=20.00, estimated_buy_price=10.00,
            seller_count=5, breakeven_days=30
        )
        # Profit ~= sell - buy - fees
        assert result['profit_per_unit'] > 0
```

### Step 3.2: Executer tests

Run:
```bash
cd backend && pytest tests/unit/test_recommendation_engine_hostile.py -v --tb=short
```

### Step 3.3: Commit tests recommendation

```bash
git add backend/tests/unit/test_recommendation_engine_hostile.py
git commit -m "test(phase8): add hostile tests for RecommendationEngineService

- Test STRONG_BUY with all criteria met
- Test AVOID with all criteria failed
- Test Amazon buybox penalty
- Test edge case ROI at threshold
- Test output structure validation
- Test None handling

Phase 8 Audit - Task 3 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Tests Integration - Analytics API Endpoints

**Goal:** Tester endpoints analytics avec DB et vrais calculs

**Files:**
- Create: `backend/tests/integration/test_analytics_api_endpoints.py`
- Read: `backend/app/api/v1/endpoints/analytics.py`

### Step 4.1: Ecrire tests integration analytics

Create: `backend/tests/integration/test_analytics_api_endpoints.py`

```python
"""
Phase 8 Audit: Tests integration pour Analytics API endpoints.
Teste endpoints avec vraie DB et calculs.
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal


@pytest.mark.asyncio
class TestAnalyticsEndpointsIntegration:
    """Tests integration pour /api/v1/analytics/*."""

    async def test_calculate_analytics_success(self, async_client: AsyncClient):
        """Test /calculate-analytics retourne structure complete."""
        response = await async_client.post(
            "/api/v1/analytics/calculate-analytics",
            json={
                "asin": "B001234567",
                "title": "Test Book",
                "bsr": 25000,
                "estimated_buy_price": "5.00",
                "estimated_sell_price": "19.99",
                "seller_count": 5,
                "amazon_on_listing": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['asin'] == 'B001234567'
        assert 'velocity' in data
        assert 'price_stability' in data
        assert 'roi' in data
        assert 'competition' in data

    async def test_calculate_analytics_missing_required(self, async_client: AsyncClient):
        """Test validation erreur si champs requis manquants."""
        response = await async_client.post(
            "/api/v1/analytics/calculate-analytics",
            json={"asin": "B001234567"}  # Missing buy/sell prices
        )

        assert response.status_code == 422  # Validation error

    async def test_calculate_risk_score_success(self, async_client: AsyncClient):
        """Test /calculate-risk-score retourne score valide."""
        response = await async_client.post(
            "/api/v1/analytics/calculate-risk-score",
            json={
                "asin": "B001234567",
                "bsr": 50000,
                "estimated_buy_price": "8.00",
                "estimated_sell_price": "25.00",
                "seller_count": 8,
                "amazon_on_listing": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['asin'] == 'B001234567'
        assert 0 <= data['risk_score'] <= 100
        assert data['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 'components' in data
        assert len(data['recommendations']) > 0

    async def test_generate_recommendation_success(self, async_client: AsyncClient):
        """Test /generate-recommendation retourne tier valide."""
        response = await async_client.post(
            "/api/v1/analytics/generate-recommendation",
            json={
                "asin": "B001234567",
                "title": "Great Book Title",
                "bsr": 15000,
                "estimated_buy_price": "5.00",
                "estimated_sell_price": "22.00",
                "seller_count": 3,
                "amazon_on_listing": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        valid_tiers = ['STRONG_BUY', 'BUY', 'CONSIDER', 'WATCH', 'SKIP', 'AVOID']
        assert data['recommendation'] in valid_tiers
        assert 0 <= data['confidence_percent'] <= 100
        assert len(data['next_steps']) > 0

    async def test_product_decision_complete(self, async_client: AsyncClient):
        """Test /product-decision retourne decision complete."""
        response = await async_client.post(
            "/api/v1/analytics/product-decision",
            json={
                "asin": "B001234567",
                "title": "Complete Test Book",
                "bsr": 20000,
                "estimated_buy_price": "6.00",
                "estimated_sell_price": "24.99",
                "seller_count": 4,
                "fba_seller_count": 3,
                "amazon_on_listing": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify complete decision structure
        assert data['asin'] == 'B001234567'
        assert 'velocity' in data
        assert 'price_stability' in data
        assert 'roi' in data
        assert 'competition' in data
        assert 'risk' in data
        assert 'recommendation' in data

        # Verify nested structures
        assert data['velocity']['velocity_score'] >= 0
        assert data['roi']['roi_percentage'] > 0
        assert data['risk']['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    async def test_product_decision_performance(self, async_client: AsyncClient):
        """Test /product-decision repond en < 500ms."""
        import time

        start = time.time()
        response = await async_client.post(
            "/api/v1/analytics/product-decision",
            json={
                "asin": "B001234567",
                "estimated_buy_price": "5.00",
                "estimated_sell_price": "20.00"
            }
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"Response took {elapsed:.0f}ms, expected < 500ms"
```

### Step 4.2: Executer tests integration

Run:
```bash
cd backend && pytest tests/integration/test_analytics_api_endpoints.py -v --tb=short
```

### Step 4.3: Commit tests integration analytics

```bash
git add backend/tests/integration/test_analytics_api_endpoints.py
git commit -m "test(phase8): add integration tests for Analytics API endpoints

- Test /calculate-analytics response structure
- Test /calculate-risk-score with risk levels
- Test /generate-recommendation with tiers
- Test /product-decision complete response
- Test performance < 500ms

Phase 8 Audit - Task 4 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Tests Integration - ASIN History Endpoints

**Goal:** Tester endpoints ASIN history avec DB

**Files:**
- Create: `backend/tests/integration/test_asin_history_endpoints.py`

### Step 5.1: Ecrire tests integration ASIN history

Create: `backend/tests/integration/test_asin_history_endpoints.py`

```python
"""
Phase 8 Audit: Tests integration pour ASIN History endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestASINHistoryEndpointsIntegration:
    """Tests integration pour /api/v1/asin-history/*."""

    async def test_get_trends_not_found(self, async_client: AsyncClient):
        """Test /trends/{asin} retourne 404 si pas de donnees."""
        response = await async_client.get(
            "/api/v1/asin-history/trends/NONEXISTENT"
        )

        # 404 est OK si pas de donnees
        assert response.status_code in [200, 404]

        if response.status_code == 404:
            data = response.json()
            assert 'detail' in data

    async def test_get_trends_valid_params(self, async_client: AsyncClient):
        """Test /trends/{asin} accepte params days."""
        response = await async_client.get(
            "/api/v1/asin-history/trends/B001234567?days=30"
        )

        assert response.status_code in [200, 404]

    async def test_get_trends_invalid_days(self, async_client: AsyncClient):
        """Test /trends/{asin} rejette days invalide."""
        response = await async_client.get(
            "/api/v1/asin-history/trends/B001234567?days=0"
        )

        assert response.status_code == 422  # Validation error (days >= 1)

    async def test_get_trends_max_days(self, async_client: AsyncClient):
        """Test /trends/{asin} rejette days > 365."""
        response = await async_client.get(
            "/api/v1/asin-history/trends/B001234567?days=500"
        )

        assert response.status_code == 422

    async def test_get_records_not_found(self, async_client: AsyncClient):
        """Test /records/{asin} retourne liste vide si pas de donnees."""
        response = await async_client.get(
            "/api/v1/asin-history/records/NONEXISTENT"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_records_with_limit(self, async_client: AsyncClient):
        """Test /records/{asin} respecte limit."""
        response = await async_client.get(
            "/api/v1/asin-history/records/B001234567?limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    async def test_get_latest_not_found(self, async_client: AsyncClient):
        """Test /latest/{asin} retourne 404 si pas de donnees."""
        response = await async_client.get(
            "/api/v1/asin-history/latest/NONEXISTENT123"
        )

        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
```

### Step 5.2: Executer tests integration ASIN history

Run:
```bash
cd backend && pytest tests/integration/test_asin_history_endpoints.py -v --tb=short
```

### Step 5.3: Commit tests ASIN history

```bash
git add backend/tests/integration/test_asin_history_endpoints.py
git commit -m "test(phase8): add integration tests for ASIN History endpoints

- Test /trends/{asin} with valid/invalid params
- Test /records/{asin} with limit
- Test /latest/{asin} 404 handling
- Test days validation (1-365)

Phase 8 Audit - Task 5 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Tests Frontend - TokenErrorAlert Component

**Goal:** Tester composant TokenErrorAlert avec divers scenarios

**Files:**
- Create: `frontend/src/components/__tests__/TokenErrorAlert.test.tsx`
- Read: `frontend/src/components/TokenErrorAlert.tsx`

### Step 6.1: Ecrire tests unitaires TokenErrorAlert

Create: `frontend/src/components/__tests__/TokenErrorAlert.test.tsx`

```typescript
/**
 * Phase 8 Audit: Tests unitaires pour TokenErrorAlert component.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TokenErrorAlert, TokenErrorBadge } from '../TokenErrorAlert'

describe('TokenErrorAlert', () => {
  const mockTokenError = {
    response: {
      status: 429,
      headers: {
        'x-token-balance': '10',
        'x-token-required': '50',
        'retry-after': '3600'
      },
      data: {
        detail: 'Insufficient tokens'
      }
    }
  }

  it('renders nothing when error is null', () => {
    const { container } = render(<TokenErrorAlert error={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when error is not 429', () => {
    const nonTokenError = { response: { status: 500 } }
    const { container } = render(<TokenErrorAlert error={nonTokenError} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders alert when error is 429', () => {
    render(<TokenErrorAlert error={mockTokenError} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('displays token balance and required', () => {
    render(<TokenErrorAlert error={mockTokenError} />)
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('displays deficit calculation', () => {
    render(<TokenErrorAlert error={mockTokenError} />)
    expect(screen.getByText('40')).toBeInTheDocument() // 50 - 10
  })

  it('has retry button that reloads page', () => {
    const reloadMock = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true
    })

    render(<TokenErrorAlert error={mockTokenError} />)
    const retryButton = screen.getByText('Reessayer')
    fireEvent.click(retryButton)

    expect(reloadMock).toHaveBeenCalled()
  })
})

describe('TokenErrorBadge', () => {
  const mockTokenError = {
    response: {
      status: 429,
      headers: {
        'x-token-balance': '5',
        'x-token-required': '20'
      }
    }
  }

  it('renders nothing when error is null', () => {
    const { container } = render(<TokenErrorBadge error={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders compact badge for 429 error', () => {
    render(<TokenErrorBadge error={mockTokenError} />)
    expect(screen.getByText(/5\/20/)).toBeInTheDocument()
  })
})
```

### Step 6.2: Executer tests frontend

Run:
```bash
cd frontend && npm test -- --run TokenErrorAlert
```

### Step 6.3: Commit tests TokenErrorAlert

```bash
git add frontend/src/components/__tests__/TokenErrorAlert.test.tsx
git commit -m "test(phase8): add unit tests for TokenErrorAlert component

- Test renders nothing for null/non-429 errors
- Test displays token balance/required/deficit
- Test retry button functionality
- Test TokenErrorBadge compact variant

Phase 8 Audit - Task 6 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Tests Frontend - tokenErrorHandler Utils

**Goal:** Tester utilitaires parsing erreur token

**Files:**
- Create: `frontend/src/utils/__tests__/tokenErrorHandler.test.ts`

### Step 7.1: Ecrire tests tokenErrorHandler

Create: `frontend/src/utils/__tests__/tokenErrorHandler.test.ts`

```typescript
/**
 * Phase 8 Audit: Tests unitaires pour tokenErrorHandler utils.
 */
import { describe, it, expect } from 'vitest'
import {
  parseTokenError,
  formatTokenErrorMessage,
  isTokenError
} from '../tokenErrorHandler'

describe('isTokenError', () => {
  it('returns true for 429 status', () => {
    const error = { response: { status: 429 } }
    expect(isTokenError(error)).toBe(true)
  })

  it('returns false for other status codes', () => {
    expect(isTokenError({ response: { status: 400 } })).toBe(false)
    expect(isTokenError({ response: { status: 500 } })).toBe(false)
    expect(isTokenError({ response: { status: 200 } })).toBe(false)
  })

  it('returns false for null/undefined', () => {
    expect(isTokenError(null)).toBe(false)
    expect(isTokenError(undefined)).toBe(false)
    expect(isTokenError({})).toBe(false)
  })
})

describe('parseTokenError', () => {
  it('returns null for non-429 errors', () => {
    const error = { response: { status: 500 } }
    expect(parseTokenError(error)).toBeNull()
  })

  it('extracts token balance from headers', () => {
    const error = {
      response: {
        status: 429,
        headers: { 'x-token-balance': '25' }
      }
    }
    const result = parseTokenError(error)
    expect(result?.balance).toBe(25)
  })

  it('extracts token required from headers', () => {
    const error = {
      response: {
        status: 429,
        headers: { 'x-token-required': '100' }
      }
    }
    const result = parseTokenError(error)
    expect(result?.required).toBe(100)
  })

  it('calculates deficit correctly', () => {
    const error = {
      response: {
        status: 429,
        headers: {
          'x-token-balance': '10',
          'x-token-required': '50'
        }
      }
    }
    const result = parseTokenError(error)
    expect(result?.deficit).toBe(40)
  })

  it('extracts retry-after header', () => {
    const error = {
      response: {
        status: 429,
        headers: { 'retry-after': '1800' }
      }
    }
    const result = parseTokenError(error)
    expect(result?.retryAfter).toBe(1800)
  })

  it('defaults retry-after to 3600', () => {
    const error = {
      response: {
        status: 429,
        headers: {}
      }
    }
    const result = parseTokenError(error)
    expect(result?.retryAfter).toBe(3600)
  })
})

describe('formatTokenErrorMessage', () => {
  it('formats message with balance and required', () => {
    const tokenError = {
      balance: 10,
      required: 50,
      deficit: 40,
      retryAfter: 3600,
      message: ''
    }
    const message = formatTokenErrorMessage(tokenError)
    expect(message).toContain('10')
    expect(message).toContain('50')
    expect(message).toContain('60 minutes')
  })

  it('handles missing balance/required', () => {
    const tokenError = {
      balance: null,
      required: null,
      deficit: null,
      retryAfter: 1800,
      message: ''
    }
    const message = formatTokenErrorMessage(tokenError)
    expect(message).toContain('30 minutes')
  })
})
```

### Step 7.2: Executer tests

Run:
```bash
cd frontend && npm test -- --run tokenErrorHandler
```

### Step 7.3: Commit tests tokenErrorHandler

```bash
git add frontend/src/utils/__tests__/tokenErrorHandler.test.ts
git commit -m "test(phase8): add unit tests for tokenErrorHandler utils

- Test isTokenError detection
- Test parseTokenError extraction
- Test deficit calculation
- Test retry-after handling
- Test formatTokenErrorMessage

Phase 8 Audit - Task 7 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Tests E2E Playwright - Phase 8 Analytics Flow

**Goal:** Creer suite E2E complete pour valider analytics en production

**Files:**
- Create: `backend/tests/e2e/tests/12-phase8-analytics-audit.spec.js`

### Step 8.1: Ecrire tests E2E Playwright

Create: `backend/tests/e2e/tests/12-phase8-analytics-audit.spec.js`

```javascript
/**
 * Phase 8 Audit: E2E Tests - Advanced Analytics System
 *
 * Valide en production:
 * - Tous endpoints analytics repondent correctement
 * - Calculs coherents (ROI, Risk, Velocity)
 * - Performance < 500ms
 * - Gestion erreurs (404, 422)
 *
 * Token Cost: ~30 tokens (pas d'appels Keepa directs)
 */
const { test, expect } = require('@playwright/test')

const API_BASE_URL = process.env.BACKEND_URL || 'https://arbitragevault-backend-v2.onrender.com'
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://arbitragevault.netlify.app'

// Test data
const GOOD_PRODUCT = {
  asin: 'B001TEST01',
  title: 'Phase 8 Audit Test Book',
  bsr: 15000,
  estimated_buy_price: '5.00',
  estimated_sell_price: '22.00',
  seller_count: 3,
  fba_seller_count: 2,
  amazon_on_listing: false
}

const BAD_PRODUCT = {
  asin: 'B001TEST02',
  title: 'High Risk Test Book',
  bsr: 3000000,
  estimated_buy_price: '15.00',
  estimated_sell_price: '18.00',
  seller_count: 45,
  amazon_on_listing: true,
  amazon_has_buybox: true
}

test.describe('Phase 8 Audit: Analytics Endpoints', () => {

  test('8.1 - /calculate-analytics returns complete structure', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/analytics/calculate-analytics`, {
      data: GOOD_PRODUCT
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()

    // Verify structure
    expect(data.asin).toBe(GOOD_PRODUCT.asin)
    expect(data).toHaveProperty('velocity')
    expect(data).toHaveProperty('price_stability')
    expect(data).toHaveProperty('roi')
    expect(data).toHaveProperty('competition')
    expect(data).toHaveProperty('dead_inventory_risk')

    // Verify velocity
    expect(data.velocity.velocity_score).toBeGreaterThanOrEqual(0)
    expect(data.velocity.velocity_score).toBeLessThanOrEqual(100)

    // Verify ROI calculation (good margin should be positive)
    expect(data.roi.roi_percentage).toBeGreaterThan(0)
    expect(data.roi.net_profit).toBeGreaterThan(0)

    console.log('[PASS] 8.1 calculate-analytics structure validated')
  })

  test('8.2 - /calculate-risk-score returns valid risk levels', async ({ request }) => {
    // Test low risk product
    const lowRiskResponse = await request.post(`${API_BASE_URL}/api/v1/analytics/calculate-risk-score`, {
      data: GOOD_PRODUCT
    })

    expect(lowRiskResponse.ok()).toBeTruthy()
    const lowRisk = await lowRiskResponse.json()

    expect(lowRisk.risk_level).toMatch(/LOW|MEDIUM/)
    expect(lowRisk.risk_score).toBeLessThan(50)

    // Test high risk product
    const highRiskResponse = await request.post(`${API_BASE_URL}/api/v1/analytics/calculate-risk-score`, {
      data: BAD_PRODUCT
    })

    expect(highRiskResponse.ok()).toBeTruthy()
    const highRisk = await highRiskResponse.json()

    expect(highRisk.risk_level).toMatch(/MEDIUM|HIGH|CRITICAL/)

    console.log('[PASS] 8.2 risk-score returns correct risk levels')
    console.log(`  Low risk product: ${lowRisk.risk_level} (${lowRisk.risk_score})`)
    console.log(`  High risk product: ${highRisk.risk_level} (${highRisk.risk_score})`)
  })

  test('8.3 - /generate-recommendation returns correct tiers', async ({ request }) => {
    // Good product should get BUY or better
    const goodResponse = await request.post(`${API_BASE_URL}/api/v1/analytics/generate-recommendation`, {
      data: GOOD_PRODUCT
    })

    expect(goodResponse.ok()).toBeTruthy()
    const goodRec = await goodResponse.json()

    expect(goodRec.recommendation).toMatch(/STRONG_BUY|BUY|CONSIDER/)
    expect(goodRec.confidence_percent).toBeGreaterThanOrEqual(0)
    expect(goodRec.next_steps.length).toBeGreaterThan(0)

    // Bad product should get WATCH or worse
    const badResponse = await request.post(`${API_BASE_URL}/api/v1/analytics/generate-recommendation`, {
      data: BAD_PRODUCT
    })

    expect(badResponse.ok()).toBeTruthy()
    const badRec = await badResponse.json()

    expect(badRec.recommendation).toMatch(/WATCH|SKIP|AVOID/)

    console.log('[PASS] 8.3 recommendations align with product quality')
    console.log(`  Good product: ${goodRec.recommendation}`)
    console.log(`  Bad product: ${badRec.recommendation}`)
  })

  test('8.4 - /product-decision returns complete decision card', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: GOOD_PRODUCT
    })

    expect(response.ok()).toBeTruthy()
    const decision = await response.json()

    // Verify all sections present
    expect(decision).toHaveProperty('velocity')
    expect(decision).toHaveProperty('price_stability')
    expect(decision).toHaveProperty('roi')
    expect(decision).toHaveProperty('competition')
    expect(decision).toHaveProperty('risk')
    expect(decision).toHaveProperty('recommendation')

    // Verify nested risk structure
    expect(decision.risk.risk_score).toBeGreaterThanOrEqual(0)
    expect(decision.risk.components).toBeDefined()

    // Verify nested recommendation structure
    expect(decision.recommendation.recommendation).toMatch(/STRONG_BUY|BUY|CONSIDER|WATCH|SKIP|AVOID/)
    expect(decision.recommendation.next_steps).toBeDefined()

    console.log('[PASS] 8.4 product-decision card complete')
  })

  test('8.5 - Analytics performance under 500ms', async ({ request }) => {
    const start = Date.now()

    const response = await request.post(`${API_BASE_URL}/api/v1/analytics/product-decision`, {
      data: GOOD_PRODUCT
    })

    const elapsed = Date.now() - start

    expect(response.ok()).toBeTruthy()
    expect(elapsed).toBeLessThan(500)

    console.log(`[PASS] 8.5 Analytics response: ${elapsed}ms (target: <500ms)`)
  })

  test('8.6 - Validation error for missing required fields', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/analytics/calculate-analytics`, {
      data: { asin: 'B001TEST' }  // Missing buy/sell prices
    })

    expect(response.status()).toBe(422)

    console.log('[PASS] 8.6 Validation error returned for missing fields')
  })

})

test.describe('Phase 8 Audit: ASIN History Endpoints', () => {

  test('8.7 - /trends/{asin} handles missing data gracefully', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/asin-history/trends/NONEXISTENT?days=30`)

    // Should return 404 or empty data structure
    expect([200, 404]).toContain(response.status())

    if (response.status() === 404) {
      const data = await response.json()
      expect(data.detail).toContain('No history')
    }

    console.log('[PASS] 8.7 trends endpoint handles missing data')
  })

  test('8.8 - /trends/{asin} validates days parameter', async ({ request }) => {
    // days=0 should fail
    const zeroResponse = await request.get(`${API_BASE_URL}/api/v1/asin-history/trends/B001TEST?days=0`)
    expect(zeroResponse.status()).toBe(422)

    // days=500 should fail (max 365)
    const maxResponse = await request.get(`${API_BASE_URL}/api/v1/asin-history/trends/B001TEST?days=500`)
    expect(maxResponse.status()).toBe(422)

    console.log('[PASS] 8.8 trends days parameter validation works')
  })

  test('8.9 - /records/{asin} returns array', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/asin-history/records/B001TEST?limit=10`)

    expect(response.ok()).toBeTruthy()
    const data = await response.json()

    expect(Array.isArray(data)).toBe(true)

    console.log(`[PASS] 8.9 records endpoint returns array (${data.length} items)`)
  })

  test('8.10 - /latest/{asin} returns 404 for unknown ASIN', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/asin-history/latest/UNKNOWNASIN999`)

    expect(response.status()).toBe(404)

    console.log('[PASS] 8.10 latest endpoint returns 404 for unknown ASIN')
  })

})

test.describe('Phase 8 Audit: Frontend Integration', () => {

  test('8.11 - Frontend loads without errors', async ({ page }) => {
    // Navigate to app
    await page.goto(FRONTEND_URL)
    await page.waitForLoadState('networkidle')

    // Check no console errors
    const errors = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    await page.waitForTimeout(2000)

    // Filter out known acceptable errors
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('net::ERR_')
    )

    expect(criticalErrors.length).toBe(0)

    console.log('[PASS] 8.11 Frontend loads without critical errors')
  })

  test('8.12 - Take screenshot of analytics page', async ({ page }) => {
    await page.goto(FRONTEND_URL)
    await page.waitForLoadState('networkidle')

    // Take screenshot
    await page.screenshot({
      path: 'test-results/phase8-frontend-screenshot.png',
      fullPage: true
    })

    console.log('[PASS] 8.12 Screenshot captured: test-results/phase8-frontend-screenshot.png')
  })

})
```

### Step 8.2: Executer tests E2E

Run:
```bash
cd backend/tests/e2e && npx playwright test tests/12-phase8-analytics-audit.spec.js --reporter=list
```

Expected: 12/12 PASS

### Step 8.3: Commit tests E2E

```bash
git add backend/tests/e2e/tests/12-phase8-analytics-audit.spec.js
git commit -m "test(phase8): add comprehensive E2E Playwright tests for analytics

- 8.1-8.6: Analytics endpoint tests
- 8.7-8.10: ASIN history endpoint tests
- 8.11-8.12: Frontend integration tests
- Performance validation (<500ms)
- Error handling validation (404, 422)

Phase 8 Audit - Task 8 complete

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Executer Tous Tests et Documentation

**Goal:** Valider suite complete et documenter resultats

### Step 9.1: Executer tous tests backend

Run:
```bash
cd backend && pytest tests/unit/test_advanced_analytics_hostile.py tests/unit/test_risk_scoring_hostile.py tests/unit/test_recommendation_engine_hostile.py tests/integration/test_analytics_api_endpoints.py tests/integration/test_asin_history_endpoints.py -v --tb=short
```

### Step 9.2: Executer tests E2E Phase 8

Run:
```bash
cd backend/tests/e2e && npx playwright test tests/12-phase8-analytics-audit.spec.js
```

### Step 9.3: Mettre a jour compact_current.md

Update: `.claude/compact_current.md`

Ajouter section:
```markdown
### Phase 8 Audit - COMPLETE (25 Dec 2025)

**Tests ajoutes:**
- `backend/tests/unit/test_advanced_analytics_hostile.py` (20 tests)
- `backend/tests/unit/test_risk_scoring_hostile.py` (8 tests)
- `backend/tests/unit/test_recommendation_engine_hostile.py` (7 tests)
- `backend/tests/integration/test_analytics_api_endpoints.py` (6 tests)
- `backend/tests/integration/test_asin_history_endpoints.py` (7 tests)
- `backend/tests/e2e/tests/12-phase8-analytics-audit.spec.js` (12 tests)
- `frontend/src/components/__tests__/TokenErrorAlert.test.tsx` (6 tests)
- `frontend/src/utils/__tests__/tokenErrorHandler.test.ts` (10 tests)

**Total nouveaux tests:** 76 tests

**Validation:**
- Backend unit tests: XX/XX PASS
- Backend integration tests: XX/XX PASS
- E2E Playwright tests: 12/12 PASS
- Frontend tests: XX/XX PASS

**Status:** Phase 8 AUDITE et VALIDE
```

### Step 9.4: Commit final

```bash
git add .claude/compact_current.md .claude/compact_master.md
git commit -m "docs(phase8): mark Phase 8 Advanced Analytics as AUDITED

- 76 new tests added across unit/integration/e2e
- All analytics services validated with hostile tests
- ASIN history endpoints validated
- Frontend TokenErrorAlert tested
- Performance validated (<500ms)

Phase 8 Audit COMPLETE

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria Validation

**Phase 8 Audit Checklist:**

- [ ] Tests unitaires hostiles AdvancedAnalyticsService (20 tests)
- [ ] Tests unitaires hostiles RiskScoringService (8 tests)
- [ ] Tests unitaires hostiles RecommendationEngineService (7 tests)
- [ ] Tests integration Analytics API (6 tests)
- [ ] Tests integration ASIN History API (7 tests)
- [ ] Tests frontend TokenErrorAlert (6 tests)
- [ ] Tests frontend tokenErrorHandler (10 tests)
- [ ] Tests E2E Playwright (12 tests)
- [ ] Performance < 500ms validee
- [ ] Documentation mise a jour

**Test Summary:**

| Category | Tests | Status |
|----------|-------|--------|
| Unit - Analytics Service | 20 | PENDING |
| Unit - Risk Scoring | 8 | PENDING |
| Unit - Recommendation | 7 | PENDING |
| Integration - Analytics API | 6 | PENDING |
| Integration - ASIN History | 7 | PENDING |
| Frontend - TokenErrorAlert | 6 | PENDING |
| Frontend - tokenErrorHandler | 10 | PENDING |
| E2E - Playwright | 12 | PENDING |
| **TOTAL** | **76** | **PENDING** |

---

## Plan Complete

**Total Tasks:** 9 tasks
**Estimated Time:** 2-3 heures
**Token Cost:** ~30 tokens pour tests E2E production
**Files Created:** 8 nouveaux fichiers de tests

Plan saved to: `docs/plans/2025-12-25-phase8-advanced-analytics-audit.md`

---

**Execution Options:**

1. **Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

2. **Parallel Session (separate)** - Open new session with superpowers:executing-plans, batch execution with checkpoints

**Which approach would you prefer?**
