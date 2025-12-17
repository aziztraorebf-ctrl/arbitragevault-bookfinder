"""
Unit tests for competition data extraction in AutoSourcing.
Phase 7 Audit Fix - Validates fba_seller_count and amazon_on_listing extraction.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.autosourcing_service import AutoSourcingService


class TestCompetitionDataExtraction:
    """Test competition data is correctly extracted from Keepa responses."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_keepa(self):
        keepa = MagicMock()
        keepa.can_perform_action = AsyncMock(return_value={
            "can_proceed": True, "current_balance": 1000, "required_tokens": 50
        })
        return keepa

    @pytest.fixture
    def service(self, mock_db, mock_keepa):
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    # ===== Test _extract_product_data_from_keepa =====

    def test_extracts_amazon_on_listing_true(self, service):
        """Amazon on listing when availabilityAmazon >= 0."""
        raw_keepa = {
            "title": "Test Product",
            "availabilityAmazon": 0,  # 0 = Amazon in stock now
            "stats": {
                "current": [2499, 1999, None, 45000],  # price in cents, BSR
                "offerCountFBA": 3
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["amazon_on_listing"] is True
        assert result["fba_seller_count"] == 3

    def test_extracts_amazon_on_listing_false(self, service):
        """Amazon NOT on listing when availabilityAmazon == -1."""
        raw_keepa = {
            "title": "No Amazon Product",
            "availabilityAmazon": -1,  # -1 = Amazon not selling
            "stats": {
                "current": [None, 2999, None, 30000],
                "offerCountFBA": 5
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["amazon_on_listing"] is False
        assert result["fba_seller_count"] == 5

    def test_extracts_fba_count_from_stats(self, service):
        """FBA seller count from stats.offerCountFBA."""
        raw_keepa = {
            "title": "FBA Product",
            "availabilityAmazon": -1,
            "stats": {
                "current": [None, 1999, None, 20000],
                "offerCountFBA": 7
            },
            "categoryTree": [{"name": "Electronics"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["fba_seller_count"] == 7

    def test_fba_count_none_when_negative(self, service):
        """FBA count is None when offerCountFBA is -2 (no data)."""
        raw_keepa = {
            "title": "No FBA Data Product",
            "availabilityAmazon": -1,
            "stats": {
                "current": [None, 2499, None, 50000],
                "offerCountFBA": -2  # -2 = no data available
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["fba_seller_count"] is None

    def test_fba_count_fallback_to_current_11(self, service):
        """FBA count falls back to current[11] when offerCountFBA missing."""
        raw_keepa = {
            "title": "Fallback FBA Product",
            "availabilityAmazon": -1,
            "stats": {
                # current[11] = COUNT_NEW (FBA offers count)
                "current": [None, 2499, None, 50000, None, None, None, None, None, None, None, 4]
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["fba_seller_count"] == 4

    def test_amazon_on_listing_with_delay(self, service):
        """Amazon on listing when availabilityAmazon > 0 (with delay)."""
        raw_keepa = {
            "title": "Amazon Delayed Product",
            "availabilityAmazon": 5,  # 5 = Amazon available with 5 days delay
            "stats": {
                "current": [2499, 1999, None, 45000],
                "offerCountFBA": 2
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["amazon_on_listing"] is True  # Amazon sells, just delayed

    def test_missing_availability_defaults_to_no_amazon(self, service):
        """Missing availabilityAmazon defaults to Amazon NOT on listing."""
        raw_keepa = {
            "title": "Missing Availability Product",
            # No availabilityAmazon field
            "stats": {
                "current": [None, 1999, None, 30000],
                "offerCountFBA": 1
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["amazon_on_listing"] is False  # Defaults to False

    def test_complete_extraction_with_all_fields(self, service):
        """Test complete extraction with all fields present."""
        raw_keepa = {
            "title": "Complete Product",
            "availabilityAmazon": -1,
            "stats": {
                "current": [None, 2499, None, 25000],  # NEW price = $24.99, BSR = 25000
                "offerCountFBA": 3
            },
            "categoryTree": [{"name": "Books"}]
        }

        result = service._extract_product_data_from_keepa(raw_keepa)

        assert result["title"] == "Complete Product"
        assert result["current_price"] == 24.99
        assert result["bsr"] == 25000
        assert result["category"] == "Books"
        assert result["amazon_on_listing"] is False
        assert result["fba_seller_count"] == 3


class TestDiscoveryConfigCompetitionParams:
    """Test that discovery_config competition params are properly extracted."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_keepa(self):
        keepa = MagicMock()
        return keepa

    @pytest.fixture
    def service(self, mock_db, mock_keepa):
        svc = AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)
        # Mock product_finder
        svc.product_finder = MagicMock()
        svc.product_finder.discover_products = AsyncMock(return_value=[])
        return svc

    @pytest.mark.asyncio
    async def test_default_max_fba_sellers(self, service):
        """Default max_fba_sellers is 5 when not specified."""
        discovery_config = {
            "categories": ["books"],
            "bsr_range": [10000, 80000],
            "price_range": [15, 60],
            "max_results": 10
        }

        await service._discover_products(discovery_config)

        # Verify discover_products was called with max_fba_sellers=5
        call_kwargs = service.product_finder.discover_products.call_args.kwargs
        assert call_kwargs.get("max_fba_sellers") == 5
        assert call_kwargs.get("exclude_amazon_seller") is True

    @pytest.mark.asyncio
    async def test_custom_max_fba_sellers(self, service):
        """Custom max_fba_sellers from discovery_config."""
        discovery_config = {
            "categories": ["books"],
            "bsr_range": [10000, 80000],
            "price_range": [15, 60],
            "max_fba_sellers": 3,
            "max_results": 10
        }

        await service._discover_products(discovery_config)

        call_kwargs = service.product_finder.discover_products.call_args.kwargs
        assert call_kwargs.get("max_fba_sellers") == 3

    @pytest.mark.asyncio
    async def test_exclude_amazon_seller_true(self, service):
        """exclude_amazon_seller defaults to True."""
        discovery_config = {
            "categories": ["books"],
            "bsr_range": [10000, 80000],
            "max_results": 10
        }

        await service._discover_products(discovery_config)

        call_kwargs = service.product_finder.discover_products.call_args.kwargs
        assert call_kwargs.get("exclude_amazon_seller") is True

    @pytest.mark.asyncio
    async def test_exclude_amazon_seller_false(self, service):
        """Can disable Amazon exclusion if needed."""
        discovery_config = {
            "categories": ["books"],
            "bsr_range": [10000, 80000],
            "exclude_amazon_seller": False,
            "max_results": 10
        }

        await service._discover_products(discovery_config)

        call_kwargs = service.product_finder.discover_products.call_args.kwargs
        assert call_kwargs.get("exclude_amazon_seller") is False
