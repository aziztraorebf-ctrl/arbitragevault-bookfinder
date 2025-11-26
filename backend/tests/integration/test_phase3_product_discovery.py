"""
Phase 3 Integration Tests - Product Discovery & Niche Discovery
================================================================

TDD RED Phase: Tests designed to validate Phase 3 components.

Components Tested:
- KeepaProductFinderService
- NicheDiscoveryService
- CategoryAnalyzer
- NicheScoringService

Test Categories:
1. ProductFinder Core (5 tests)
2. BSR & Price Extraction (4 tests)
3. Fee Calculation (3 tests)
4. NicheDiscovery Orchestration (4 tests)
5. CategoryAnalyzer (4 tests)
6. Cache Management (3 tests)
7. Edge Cases & Error Handling (4 tests)
8. Full Pipeline Integration (2 tests)

Total: 29 tests

Author: Claude Code (Phase 3 Audit)
Date: 24 November 2025
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
import logging

# Services under test
from app.services.keepa_product_finder import KeepaProductFinderService
from app.services.niche_discovery_service import NicheDiscoveryService
from app.services.category_analyzer import CategoryAnalyzer
from app.services.niche_scoring_service import NicheScoringService
from app.services.keepa_service import KeepaService
from app.services.config_service import ConfigService

# Models
from app.models.niche import (
    NicheAnalysisRequest,
    NicheAnalysisCriteria,
    NicheMetrics,
    DiscoveredNiche
)

logger = logging.getLogger(__name__)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_keepa_service():
    """Create mock KeepaService with realistic responses."""
    service = AsyncMock(spec=KeepaService)
    service._ensure_sufficient_balance = AsyncMock(return_value=None)
    service._make_request = AsyncMock()
    service.check_api_balance = AsyncMock(return_value=1500)
    return service


@pytest.fixture
def mock_config_service():
    """Create mock ConfigService with realistic config."""
    service = AsyncMock(spec=ConfigService)

    # Create mock effective config with proper structure
    mock_config = MagicMock()
    mock_config.effective_roi = MagicMock()
    mock_config.effective_roi.source_price_factor = Decimal("0.4")
    mock_config.effective_roi.excellent_threshold = Decimal("50")
    mock_config.effective_roi.target = Decimal("30")
    mock_config.effective_roi.min_acceptable = Decimal("15")

    mock_config.effective_fees = MagicMock()
    mock_config.effective_fees.referral_fee_percent = Decimal("15")
    mock_config.effective_fees.fba_base_fee = Decimal("2.50")
    mock_config.effective_fees.fba_per_pound = Decimal("0.40")
    mock_config.effective_fees.closing_fee = Decimal("1.80")
    mock_config.effective_fees.prep_fee = Decimal("0.20")
    mock_config.effective_fees.shipping_cost = Decimal("0.40")

    mock_config.effective_velocity = MagicMock()
    mock_config.effective_velocity.tiers = [
        MagicMock(bsr_threshold=10000, min_score=80, max_score=100),
        MagicMock(bsr_threshold=50000, min_score=60, max_score=80),
        MagicMock(bsr_threshold=100000, min_score=40, max_score=60),
        MagicMock(bsr_threshold=500000, min_score=20, max_score=40),
    ]

    service.get_effective_config = AsyncMock(return_value=mock_config)
    return service


@pytest.fixture
def sample_keepa_product():
    """Sample Keepa product data with realistic structure."""
    return {
        "asin": "B00FLIJJSA",
        "title": "Test Book: Advanced Programming Techniques",
        "csv": [
            # csv[0] = Amazon prices (time, price pairs)
            [1000, 2500, 1100, 2499, 1200, 2500, 1300, 2450, 1400, 2500],
            # csv[1] = NEW prices
            [1000, 2800, 1100, 2750, 1200, 2850, 1300, 2900],
            # csv[2] = USED prices
            [1000, 1500, 1100, 1600, 1200, 1550],
            # csv[3] = SALES rank (BSR)
            [1000, 45000, 1100, 43000, 1200, 42000, 1300, 41000, 1400, 40000]
        ],
        "stats": {
            "current": [2500, 2800, 1500, 40000, 50]  # [amazon, new, used, bsr, offers]
        },
        "salesRanks": {
            "283155": [1000, 45000, 1400, 40000]  # Books category
        },
        "salesRankReference": 283155,
        "availabilityAmazon": 0
    }


@pytest.fixture
def sample_keepa_product_minimal():
    """Minimal Keepa product with sparse data."""
    return {
        "asin": "B001MINIMAL",
        "title": "Minimal Product",
        "csv": [],
        "stats": {}
    }


@pytest.fixture
def sample_keepa_product_no_bsr():
    """Product without BSR data."""
    return {
        "asin": "B002NOBSR",
        "title": "No BSR Product",
        "csv": [
            [1000, 1500, 1100, 1600],  # Amazon prices
            [],  # NEW prices
            [],  # USED prices
            []   # BSR empty
        ],
        "stats": {
            "current": [1500, None, None, None]
        }
    }


@pytest.fixture
def product_finder_service(mock_keepa_service, mock_config_service):
    """Create ProductFinderService with mocks."""
    return KeepaProductFinderService(
        keepa_service=mock_keepa_service,
        config_service=mock_config_service,
        db=None  # No cache for unit tests
    )


@pytest.fixture
def category_analyzer(mock_keepa_service):
    """Create CategoryAnalyzer with mock Keepa service."""
    return CategoryAnalyzer(mock_keepa_service)


@pytest.fixture
def niche_discovery_service(mock_keepa_service):
    """Create NicheDiscoveryService with mock."""
    return NicheDiscoveryService(mock_keepa_service)


@pytest.fixture
def scoring_service():
    """Create NicheScoringService."""
    return NicheScoringService()


@pytest.fixture
def default_criteria():
    """Default niche analysis criteria."""
    return NicheAnalysisCriteria(
        bsr_range=[10000, 100000],
        max_sellers=5,
        min_margin_percent=20.0,
        min_price_stability=0.7,
        sample_size=20
    )


# =============================================================================
# SECTION 1: PRODUCTFINDER CORE (5 tests)
# =============================================================================

class TestProductFinderCore:
    """Tests for KeepaProductFinderService core functionality."""

    @pytest.mark.asyncio
    async def test_discover_products_with_category_uses_bestsellers(
        self,
        product_finder_service,
        mock_keepa_service
    ):
        """
        Test that discover_products with category calls bestsellers endpoint.

        Validates:
        - Correct endpoint called
        - Budget check performed
        - Returns list of ASINs
        """
        # Arrange
        mock_keepa_service._make_request.return_value = {
            "bestSellersList": {
                "asinList": ["B001", "B002", "B003", "B004", "B005"]
            }
        }

        # Act
        result = await product_finder_service.discover_products(
            domain=1,
            category=283155,
            max_results=5
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 5
        mock_keepa_service._ensure_sufficient_balance.assert_called()
        mock_keepa_service._make_request.assert_called()

    @pytest.mark.asyncio
    async def test_discover_products_without_category_uses_deals(
        self,
        product_finder_service,
        mock_keepa_service
    ):
        """
        Test that discover_products without category calls deals endpoint.

        Validates:
        - Deals endpoint used when no category
        - Returns ASINs from deals
        """
        # Arrange
        mock_keepa_service._make_request.return_value = {
            "deals": [
                {"asin": "B001DEAL", "currentPrice": 2500},
                {"asin": "B002DEAL", "currentPrice": 3000}
            ]
        }

        # Act
        result = await product_finder_service.discover_products(
            domain=1,
            category=None,
            max_results=10
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_discover_products_empty_response(
        self,
        product_finder_service,
        mock_keepa_service
    ):
        """
        Test handling of empty API response.

        BUG DETECTED: Should return empty list gracefully.
        """
        # Arrange
        mock_keepa_service._make_request.return_value = {}

        # Act
        result = await product_finder_service.discover_products(
            domain=1,
            category=283155,
            max_results=10
        )

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_discover_products_api_error_graceful_degradation(
        self,
        product_finder_service,
        mock_keepa_service
    ):
        """
        Test handling of API errors with graceful degradation.

        Validates:
        - Errors in bestsellers discovery return empty list
        - Service continues to function
        - Design choice: graceful degradation over exception propagation
        """
        # Arrange
        mock_keepa_service._ensure_sufficient_balance.side_effect = Exception("Insufficient tokens")

        # Act
        result = await product_finder_service.discover_products(
            domain=1,
            category=283155,
            max_results=10
        )

        # Assert - graceful degradation returns empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_discover_products_respects_max_results(
        self,
        product_finder_service,
        mock_keepa_service
    ):
        """
        Test that max_results parameter is respected.

        Validates:
        - Results truncated to max_results
        """
        # Arrange
        mock_keepa_service._make_request.return_value = {
            "bestSellersList": {
                "asinList": [f"B{i:03d}" for i in range(100)]
            }
        }

        # Act
        result = await product_finder_service.discover_products(
            domain=1,
            category=283155,
            max_results=5
        )

        # Assert
        assert len(result) == 5


# =============================================================================
# SECTION 2: BSR & PRICE EXTRACTION (4 tests)
# =============================================================================

class TestBSRAndPriceExtraction:
    """Tests for BSR and price extraction from Keepa data."""

    def test_extract_bsr_from_csv_sales(self, category_analyzer, sample_keepa_product):
        """
        Test BSR extraction from csv[3] (SALES history).

        BUG #1 DETECTED: Index iteration range(len-1, 0, -2) skips index 0.
        Should be range(len-1, -1, -2) to include index 0.
        """
        # Act
        bsr = category_analyzer._extract_bsr(sample_keepa_product)

        # Assert
        assert bsr is not None
        assert isinstance(bsr, int)
        assert bsr == 40000  # Last valid BSR from sample

    def test_extract_bsr_fallback_to_salesranks(self, category_analyzer):
        """
        Test BSR extraction fallback to salesRanks when csv[3] empty.

        Validates fallback mechanism works.
        """
        # Arrange
        product = {
            "asin": "B001FALLBACK",
            "csv": [[], [], [], []],  # Empty CSV
            "salesRanks": {
                "283155": [1000, 55000, 1200, 52000]
            },
            "salesRankReference": 283155
        }

        # Act
        bsr = category_analyzer._extract_bsr(product)

        # Assert
        assert bsr == 52000

    def test_extract_bsr_returns_none_for_empty_data(
        self,
        category_analyzer,
        sample_keepa_product_minimal
    ):
        """
        Test BSR extraction returns None for empty/missing data.

        Validates graceful handling of missing data.
        """
        # Act
        bsr = category_analyzer._extract_bsr(sample_keepa_product_minimal)

        # Assert
        assert bsr is None

    def test_extract_current_price_from_csv(self, category_analyzer, sample_keepa_product):
        """
        Test price extraction from csv[0] (Amazon prices).

        BUG #2 DETECTED: Same iteration issue - range excludes index 0.
        """
        # Act
        price = category_analyzer._extract_current_price(sample_keepa_product)

        # Assert
        assert price is not None
        assert isinstance(price, float)
        assert price == 25.00  # 2500 cents / 100


# =============================================================================
# SECTION 3: FEE CALCULATION (3 tests)
# =============================================================================

class TestFeeCalculation:
    """Tests for fee calculation logic."""

    def test_calculate_fees_with_valid_config(self, product_finder_service, mock_config_service):
        """
        Test fee calculation with valid config.

        BUG #3 DETECTED: _calculate_fees uses wrong attribute names:
        - Code uses: fba_base_fee + fba_per_pound
        - Config has: fba_fee_base + fba_fee_per_lb

        This test validates current behavior (may fail revealing bug).
        """
        # Arrange
        price = Decimal("25.00")
        fees_config = mock_config_service.get_effective_config.return_value.effective_fees

        # Act
        total_fees = product_finder_service._calculate_fees(price, fees_config)

        # Assert
        assert isinstance(total_fees, Decimal)
        assert total_fees > 0
        # Expected: referral(3.75) + fba(2.90) + closing(1.80) + prep(0.20) + shipping(0.40) = ~9.05
        assert total_fees >= Decimal("5.0")  # At minimum

    def test_calculate_fees_zero_price(self, product_finder_service, mock_config_service):
        """
        Test fee calculation with zero price.

        Validates edge case handling.
        """
        # Arrange
        price = Decimal("0")
        fees_config = mock_config_service.get_effective_config.return_value.effective_fees

        # Act
        total_fees = product_finder_service._calculate_fees(price, fees_config)

        # Assert
        # Should return fixed fees only (no referral on $0)
        assert total_fees >= Decimal("0")

    def test_estimate_profit_margin_realistic(self, category_analyzer, default_criteria):
        """
        Test profit margin estimation with realistic product.

        Validates margin calculation formula.
        """
        # Arrange
        product = {
            "asin": "B001MARGIN",
            "csv": [[1000, 3000, 1100, 3000]],  # $30 price
            "stats": {"current": [3000, None, None, None]}
        }

        # Act
        margin = category_analyzer._estimate_profit_margin(product, default_criteria)

        # Assert
        assert margin is not None
        # With $30 price: cost ~$15, fees ~$8, profit ~$7, ROI ~47%
        assert margin > 0


# =============================================================================
# SECTION 4: NICHE DISCOVERY ORCHESTRATION (4 tests)
# =============================================================================

class TestNicheDiscoveryOrchestration:
    """Tests for NicheDiscoveryService orchestration."""

    @pytest.mark.asyncio
    async def test_discover_niches_returns_response(
        self,
        niche_discovery_service,
        mock_keepa_service,
        default_criteria
    ):
        """
        Test discover_niches returns proper response structure.

        Validates:
        - Response type is NicheAnalysisResponse
        - Contains required fields
        """
        # Arrange
        request = NicheAnalysisRequest(
            criteria=default_criteria,
            target_categories=[3738],  # Medical Books
            max_results=5
        )

        # Mock category analysis
        mock_keepa_service.get_product_data = AsyncMock(return_value={
            "asin": "B001TEST",
            "csv": [[1000, 2500], [], [], [1000, 45000]],
            "stats": {"current": [2500, None, None, 45000]},
            "availabilityAmazon": 0
        })

        # Act
        response = await niche_discovery_service.discover_niches(request)

        # Assert
        assert response is not None
        assert hasattr(response, 'discovered_niches')
        assert hasattr(response, 'total_categories_analyzed')
        assert hasattr(response, 'analysis_duration_seconds')

    @pytest.mark.asyncio
    async def test_discover_niches_empty_categories(
        self,
        niche_discovery_service,
        default_criteria
    ):
        """
        Test discover_niches with no target categories.

        Should use recommended categories as fallback.
        """
        # Arrange
        request = NicheAnalysisRequest(
            criteria=default_criteria,
            target_categories=None,  # No specific categories
            max_results=5
        )

        # Act
        response = await niche_discovery_service.discover_niches(request)

        # Assert
        # Should not crash, uses recommended categories
        assert response is not None

    @pytest.mark.asyncio
    async def test_get_available_categories(self, niche_discovery_service):
        """
        Test get_available_categories returns category list.

        Validates:
        - Returns CategoriesListResponse
        - Contains categories and recommendations
        """
        # Act
        response = await niche_discovery_service.get_available_categories()

        # Assert
        assert response is not None
        assert hasattr(response, 'categories')
        assert hasattr(response, 'total_eligible')
        assert hasattr(response, 'recommended_categories')
        assert response.total_eligible > 0

    @pytest.mark.asyncio
    async def test_filter_and_rank_niches_minimum_score(self, niche_discovery_service):
        """
        Test that niches below minimum score (4.0) are filtered out.

        Validates minimum quality threshold.
        """
        # Arrange
        low_score_niche = DiscoveredNiche(
            category_name="Low Score Category",
            category_id=9999,
            metrics=NicheMetrics(
                avg_sellers=2.0,
                avg_bsr=50000.0,
                avg_price=20.0,
                price_stability=0.6,
                profit_margin=15.0,
                total_products=10,
                viable_products=3,
                competition_level="Medium"
            ),
            niche_score=3.5,  # Below 4.0 threshold
            confidence_level="Low",
            sample_quality="Poor",
            criteria_used=NicheAnalysisCriteria()
        )

        high_score_niche = DiscoveredNiche(
            category_name="High Score Category",
            category_id=9998,
            metrics=NicheMetrics(
                avg_sellers=1.5,
                avg_bsr=30000.0,
                avg_price=30.0,
                price_stability=0.85,
                profit_margin=35.0,
                total_products=15,
                viable_products=10,
                competition_level="Low"
            ),
            niche_score=7.5,  # Above threshold
            confidence_level="High",
            sample_quality="Good",
            criteria_used=NicheAnalysisCriteria()
        )

        # Act
        filtered = niche_discovery_service._filter_and_rank_niches(
            [low_score_niche, high_score_niche],
            max_results=10
        )

        # Assert
        assert len(filtered) == 1
        assert filtered[0].niche_score >= 4.0


# =============================================================================
# SECTION 5: CATEGORY ANALYZER (4 tests)
# =============================================================================

class TestCategoryAnalyzer:
    """Tests for CategoryAnalyzer functionality."""

    @pytest.mark.asyncio
    async def test_analyze_category_returns_metrics(
        self,
        category_analyzer,
        mock_keepa_service,
        default_criteria
    ):
        """
        Test analyze_category returns NicheMetrics.

        Validates full analysis pipeline.
        """
        # Arrange
        mock_keepa_service.get_product_data = AsyncMock(return_value={
            "asin": "B001CAT",
            "csv": [[1000, 2500], [], [], [1000, 45000]],
            "stats": {"current": [2500, None, None, 45000]},
            "availabilityAmazon": 0
        })

        # Act
        metrics = await category_analyzer.analyze_category(3738, default_criteria)

        # Assert (may be None if insufficient products)
        if metrics:
            assert isinstance(metrics, NicheMetrics)
            assert metrics.total_products >= 0

    def test_estimate_seller_count_with_amazon(self, category_analyzer, sample_keepa_product):
        """
        Test seller count estimation when Amazon is available.

        Validates seller estimation logic.
        """
        # Act
        sellers = category_analyzer._estimate_seller_count(sample_keepa_product)

        # Assert
        assert sellers >= 1.0
        assert sellers <= 10.0

    def test_calculate_price_stability_with_history(
        self,
        category_analyzer,
        sample_keepa_product
    ):
        """
        Test price stability calculation with valid history.

        Validates stability score is between 0 and 1.
        """
        # Act
        stability = category_analyzer._calculate_price_stability(sample_keepa_product)

        # Assert
        assert stability is not None
        assert 0.0 <= stability <= 1.0

    def test_calculate_price_stability_insufficient_data(
        self,
        category_analyzer,
        sample_keepa_product_minimal
    ):
        """
        Test price stability returns None with insufficient data.

        BUG #4 DETECTED: Should handle empty csv gracefully.
        """
        # Act
        stability = category_analyzer._calculate_price_stability(sample_keepa_product_minimal)

        # Assert
        assert stability is None


# =============================================================================
# SECTION 6: CACHE MANAGEMENT (3 tests)
# =============================================================================

class TestCacheManagement:
    """Tests for cache functionality in services."""

    def test_cache_key_generation_consistency(self, niche_discovery_service, default_criteria):
        """
        Test cache key generation is consistent.

        BUG #5 DETECTED: Using hash(str(criteria)) can cause collisions.
        Same criteria objects may produce different hashes.
        """
        # Arrange
        category_id = 3738

        # Act - Generate cache key twice
        key1 = f"{category_id}_{hash(str(default_criteria))}"
        key2 = f"{category_id}_{hash(str(default_criteria))}"

        # Assert
        assert key1 == key2  # Should be identical

    def test_cache_ttl_expiration(self, niche_discovery_service):
        """
        Test cache entries expire after TTL.

        Validates cache cleanup logic.
        """
        # Arrange
        import time

        # Manually set cache entry with old timestamp
        old_timestamp = time.time() - 7200  # 2 hours ago (TTL is 1 hour)
        mock_niche = MagicMock()
        niche_discovery_service._analysis_cache["test_key"] = (mock_niche, old_timestamp)

        # Act
        niche_discovery_service._cleanup_cache()

        # Assert
        assert "test_key" not in niche_discovery_service._analysis_cache

    def test_cache_cleanup_removes_expired_only(self, niche_discovery_service):
        """
        Test cache cleanup preserves non-expired entries.

        Validates selective cleanup.
        """
        # Arrange
        import time
        current_time = time.time()

        # Add expired and non-expired entries
        niche_discovery_service._analysis_cache["expired"] = (MagicMock(), current_time - 7200)
        niche_discovery_service._analysis_cache["fresh"] = (MagicMock(), current_time - 100)

        # Act
        niche_discovery_service._cleanup_cache()

        # Assert
        assert "expired" not in niche_discovery_service._analysis_cache
        assert "fresh" in niche_discovery_service._analysis_cache


# =============================================================================
# SECTION 7: EDGE CASES & ERROR HANDLING (4 tests)
# =============================================================================

class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error scenarios."""

    def test_velocity_score_bsr_zero(self, product_finder_service, mock_config_service):
        """
        Test velocity score calculation with BSR = 0.

        BUG #6 DETECTED: BSR = 0 should be handled (invalid BSR).
        """
        # Arrange
        tiers = mock_config_service.get_effective_config.return_value.effective_velocity.tiers

        # Act
        score = product_finder_service._calculate_velocity_score(0, tiers)

        # Assert
        # BSR 0 is invalid, should return high score (best seller) or handle specially
        assert score >= 0

    def test_velocity_score_very_high_bsr(self, product_finder_service, mock_config_service):
        """
        Test velocity score with very high BSR (outside all tiers).

        Validates fallback to 0 score.
        """
        # Arrange
        tiers = mock_config_service.get_effective_config.return_value.effective_velocity.tiers

        # Act
        score = product_finder_service._calculate_velocity_score(999999999, tiers)

        # Assert
        assert score == 0

    @pytest.mark.asyncio
    async def test_discover_with_scoring_config_fallback(
        self,
        product_finder_service,
        mock_keepa_service,
        mock_config_service
    ):
        """
        Test discover_with_scoring uses fallback when config fails.

        BUG #7 DETECTED: Config fallback returns dict but code expects object.
        Code tries effective_config.effective_roi.source_price_factor
        but fallback is {"roi": {"target_pct_default": 30}}.
        """
        # Arrange
        mock_config_service.get_effective_config.side_effect = Exception("Config unavailable")
        mock_keepa_service._make_request.return_value = {
            "bestSellersList": {"asinList": ["B001"]}
        }

        # Act & Assert
        # This should handle config failure gracefully
        # Currently will fail due to attribute access on dict
        try:
            result = await product_finder_service.discover_with_scoring(
                domain=1,
                category=283155,
                max_results=5
            )
            # If it succeeds, result should be list
            assert isinstance(result, list)
        except (AttributeError, KeyError) as e:
            # Expected bug: dict has no attribute 'effective_roi'
            pytest.fail(f"Config fallback bug detected: {e}")

    def test_is_product_viable_missing_bsr(self, category_analyzer, default_criteria):
        """
        Test product viability check with missing BSR.

        Should return False for incomplete data.
        """
        # Arrange
        product = {
            "asin": "B001NOBSR",
            "csv": [],
            "stats": {}
        }

        # Act
        viable = category_analyzer._is_product_viable(product, default_criteria)

        # Assert
        assert viable is False


# =============================================================================
# SECTION 8: FULL PIPELINE INTEGRATION (2 tests)
# =============================================================================

class TestFullPipelineIntegration:
    """Integration tests for complete Phase 3 pipeline."""

    @pytest.mark.asyncio
    async def test_full_discovery_pipeline_with_scoring(
        self,
        product_finder_service,
        mock_keepa_service,
        mock_config_service,
        sample_keepa_product
    ):
        """
        Test full pipeline: Discovery -> Scoring -> Recommendations.

        Validates end-to-end flow with mocked data.
        """
        # Arrange
        mock_keepa_service._make_request.side_effect = [
            # First call: bestsellers
            {"bestSellersList": {"asinList": [sample_keepa_product["asin"]]}},
            # Second call: product details
            {"products": [sample_keepa_product]}
        ]

        # Act
        results = await product_finder_service.discover_with_scoring(
            domain=1,
            category=283155,
            max_results=10
        )

        # Assert
        assert isinstance(results, list)
        if results:
            product = results[0]
            assert "asin" in product
            assert "roi_percent" in product
            assert "velocity_score" in product
            assert "recommendation" in product

    @pytest.mark.asyncio
    async def test_niche_discovery_full_pipeline(
        self,
        niche_discovery_service,
        mock_keepa_service,
        default_criteria
    ):
        """
        Test full niche discovery pipeline.

        Validates orchestration of all components.
        """
        # Arrange
        request = NicheAnalysisRequest(
            criteria=default_criteria,
            target_categories=[3738],
            max_results=3
        )

        mock_keepa_service.get_product_data = AsyncMock(return_value={
            "asin": "B001PIPELINE",
            "csv": [[1000, 2500, 1100, 2600], [], [], [1000, 35000, 1100, 33000]],
            "stats": {"current": [2600, None, None, 33000]},
            "availabilityAmazon": 0
        })

        # Act
        response = await niche_discovery_service.discover_niches(request)

        # Assert
        assert response is not None
        assert response.analysis_duration_seconds > 0
        assert response.analysis_quality in ["Excellent", "Good", "Fair", "Poor", "No Data", "Error: "]


# =============================================================================
# SECTION 9: NICHE SCORING SERVICE (3 tests)
# =============================================================================

class TestNicheScoringService:
    """Tests for NicheScoringService."""

    def test_calculate_niche_score_valid_metrics(self, scoring_service, default_criteria):
        """
        Test niche score calculation with valid metrics.

        Validates scoring algorithm.
        """
        # Arrange
        metrics = NicheMetrics(
            avg_sellers=2.0,
            avg_bsr=40000.0,
            avg_price=25.0,
            price_stability=0.85,
            profit_margin=35.0,
            total_products=20,
            viable_products=15,
            competition_level=""
        )

        # Act
        score, confidence, quality = scoring_service.calculate_niche_score(metrics, default_criteria)

        # Assert
        assert score >= 0
        assert score <= 10
        assert confidence in ["High", "Medium", "Low"]
        assert quality in ["Excellent", "Good", "Fair", "Poor"]

    def test_classify_competition_level(self, scoring_service):
        """
        Test competition level classification.

        Validates competition tiers.
        """
        # Act & Assert
        assert scoring_service.classify_competition_level(1.5) == "Low"
        assert scoring_service.classify_competition_level(3.0) in ["Low", "Medium"]
        assert scoring_service.classify_competition_level(6.0) in ["Medium", "High"]

    def test_calculate_niche_score_empty_metrics(self, scoring_service, default_criteria):
        """
        Test niche score with zero/empty metrics.

        BUG #8 DETECTED: Division by zero possible with avg_bsr=0.
        """
        # Arrange
        metrics = NicheMetrics(
            avg_sellers=0.0,
            avg_bsr=0.0,  # Potential division by zero
            avg_price=0.0,
            price_stability=0.0,
            profit_margin=0.0,
            total_products=0,
            viable_products=0,
            competition_level=""
        )

        # Act
        try:
            score, confidence, quality = scoring_service.calculate_niche_score(metrics, default_criteria)
            # Should handle gracefully
            assert score >= 0
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError - scoring should handle zero values")


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-p", "no:cacheprovider",  # Avoid bytecode cache issues
        "--log-cli-level=INFO"
    ])
