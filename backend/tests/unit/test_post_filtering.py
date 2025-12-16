"""
Unit Tests: Post-Filtering Strategy (Phase 6.2)

Tests the Product Finder post-filtering implementation:
- Root category mapping
- Post-filter logic for Amazon/FBA
- Integration with discover_products
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict

from app.services.keepa_product_finder import (
    ROOT_CATEGORY_MAPPING,
    BOOKS_ROOT_CATEGORY,
    PRODUCT_FINDER_COST,
    KeepaProductFinderService
)


class TestRootCategoryMapping:
    """Test root category mapping for Product Finder."""

    def test_law_subcategory_maps_to_books(self):
        """Law (10777) should map to Books root (283155)."""
        assert ROOT_CATEGORY_MAPPING.get(10777) == BOOKS_ROOT_CATEGORY

    def test_python_programming_maps_to_books(self):
        """Python/Programming (3508) should map to Books root."""
        assert ROOT_CATEGORY_MAPPING.get(3508) == BOOKS_ROOT_CATEGORY

    def test_self_help_maps_to_books(self):
        """Self-Help (4736) should map to Books root."""
        assert ROOT_CATEGORY_MAPPING.get(4736) == BOOKS_ROOT_CATEGORY

    def test_medical_books_maps_to_books(self):
        """Medical Books (173514) should map to Books root."""
        assert ROOT_CATEGORY_MAPPING.get(173514) == BOOKS_ROOT_CATEGORY

    def test_root_category_returns_self(self):
        """Root category (283155) should return itself (not in mapping)."""
        # Root category is not in mapping, so get returns category itself
        result = ROOT_CATEGORY_MAPPING.get(283155, 283155)
        assert result == BOOKS_ROOT_CATEGORY

    def test_unknown_category_returns_self(self):
        """Unknown category returns itself as fallback."""
        unknown_cat = 999999
        result = ROOT_CATEGORY_MAPPING.get(unknown_cat, unknown_cat)
        assert result == unknown_cat


class TestPostFilterLogic:
    """Test post-filter logic for Amazon and FBA."""

    @pytest.fixture
    def mock_product_amazon_selling(self) -> Dict:
        """Product where Amazon is selling."""
        return {
            "asin": "B001234567",
            "title": "Test Product - Amazon Sells",
            "stats": {
                "current": [
                    2999,    # [0] AMAZON price = $29.99 (Amazon is selling!)
                    2499,    # [1] NEW price = $24.99
                    1999,    # [2] USED price
                    50000,   # [3] BSR
                    None, None, None, None, None, None, None,
                    3,       # [11] COUNT_NEW (FBA sellers)
                ]
            }
        }

    @pytest.fixture
    def mock_product_no_amazon(self) -> Dict:
        """Product where Amazon is NOT selling."""
        return {
            "asin": "B009876543",
            "title": "Test Product - No Amazon",
            "stats": {
                "current": [
                    -1,      # [0] AMAZON price = -1 (not selling)
                    3499,    # [1] NEW price = $34.99
                    2999,    # [2] USED price
                    45000,   # [3] BSR
                    None, None, None, None, None, None, None,
                    2,       # [11] COUNT_NEW (FBA sellers)
                ]
            }
        }

    @pytest.fixture
    def mock_product_high_fba(self) -> Dict:
        """Product with too many FBA sellers."""
        return {
            "asin": "B005555555",
            "title": "Test Product - High FBA",
            "stats": {
                "current": [
                    -1,      # [0] AMAZON price = -1 (not selling)
                    2999,    # [1] NEW price = $29.99
                    None,    # [2] USED price
                    35000,   # [3] BSR
                    None, None, None, None, None, None, None,
                    10,      # [11] COUNT_NEW = 10 FBA sellers (too many!)
                ]
            }
        }

    @pytest.fixture
    def mock_product_ideal(self) -> Dict:
        """Ideal product: no Amazon, low FBA."""
        return {
            "asin": "B007777777",
            "title": "Ideal Product - Low Competition",
            "stats": {
                "current": [
                    -1,      # [0] AMAZON price = -1 (not selling)
                    4999,    # [1] NEW price = $49.99
                    3999,    # [2] USED price
                    25000,   # [3] BSR
                    None, None, None, None, None, None, None,
                    1,       # [11] COUNT_NEW = 1 FBA seller (ideal!)
                ]
            }
        }

    def test_exclude_amazon_seller_filters_correctly(
        self,
        mock_product_amazon_selling,
        mock_product_no_amazon
    ):
        """Products with Amazon selling should be excluded."""
        products = [mock_product_amazon_selling, mock_product_no_amazon]
        filtered = []

        for p in products:
            current = p.get("stats", {}).get("current", [])
            amazon_price = current[0] if len(current) > 0 else None

            # Apply exclude_amazon filter
            if amazon_price is not None and amazon_price > 0:
                continue  # Excluded

            filtered.append(p["asin"])

        assert len(filtered) == 1
        assert "B009876543" in filtered  # No Amazon
        assert "B001234567" not in filtered  # Amazon selling

    def test_max_fba_sellers_filters_correctly(
        self,
        mock_product_high_fba,
        mock_product_ideal
    ):
        """Products with too many FBA sellers should be excluded."""
        products = [mock_product_high_fba, mock_product_ideal]
        max_fba = 5
        filtered = []

        for p in products:
            current = p.get("stats", {}).get("current", [])
            fba_count = current[11] if len(current) > 11 else 0

            # Apply max_fba filter
            if fba_count is not None and fba_count > max_fba:
                continue  # Excluded

            filtered.append(p["asin"])

        assert len(filtered) == 1
        assert "B007777777" in filtered  # Low FBA (1)
        assert "B005555555" not in filtered  # High FBA (10)

    def test_combined_filters_amazon_and_fba(
        self,
        mock_product_amazon_selling,
        mock_product_no_amazon,
        mock_product_high_fba,
        mock_product_ideal
    ):
        """Test combined Amazon + FBA filters."""
        products = [
            mock_product_amazon_selling,
            mock_product_no_amazon,
            mock_product_high_fba,
            mock_product_ideal
        ]
        max_fba = 3
        filtered = []

        for p in products:
            current = p.get("stats", {}).get("current", [])

            # Check Amazon
            amazon_price = current[0] if len(current) > 0 else None
            if amazon_price is not None and amazon_price > 0:
                continue

            # Check FBA
            fba_count = current[11] if len(current) > 11 else 0
            if fba_count is not None and fba_count > max_fba:
                continue

            filtered.append(p["asin"])

        # Only mock_product_no_amazon (2 FBA) and mock_product_ideal (1 FBA) should pass
        assert len(filtered) == 2
        assert "B009876543" in filtered  # No Amazon, 2 FBA
        assert "B007777777" in filtered  # No Amazon, 1 FBA
        assert "B001234567" not in filtered  # Amazon selling
        assert "B005555555" not in filtered  # High FBA (10)


class TestProductFinderServicePostFilter:
    """Test KeepaProductFinderService._post_filter_asins method."""

    @pytest.fixture
    def mock_keepa_service(self):
        """Create mock KeepaService."""
        service = MagicMock()
        service._make_request = AsyncMock()
        return service

    @pytest.fixture
    def mock_config_service(self):
        """Create mock ConfigService."""
        return MagicMock()

    @pytest.fixture
    def product_finder(self, mock_keepa_service, mock_config_service):
        """Create KeepaProductFinderService instance."""
        return KeepaProductFinderService(
            keepa_service=mock_keepa_service,
            config_service=mock_config_service,
            db=None
        )

    @pytest.mark.asyncio
    async def test_post_filter_excludes_amazon_sellers(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test that _post_filter_asins excludes Amazon sellers."""
        # Mock /product response
        mock_keepa_service._make_request.return_value = {
            "products": [
                {
                    "asin": "AMAZON_SELLS",
                    "stats": {"current": [2999, 2499, None, 50000, None, None, None, None, None, None, None, 2]}
                },
                {
                    "asin": "NO_AMAZON",
                    "stats": {"current": [-1, 3499, None, 45000, None, None, None, None, None, None, None, 2]}
                }
            ]
        }

        result = await product_finder._post_filter_asins(
            domain=1,
            asins=["AMAZON_SELLS", "NO_AMAZON"],
            max_fba_sellers=5,
            exclude_amazon_seller=True
        )

        assert len(result) == 1
        assert "NO_AMAZON" in result
        assert "AMAZON_SELLS" not in result

    @pytest.mark.asyncio
    async def test_post_filter_excludes_high_fba(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test that _post_filter_asins excludes high FBA count."""
        mock_keepa_service._make_request.return_value = {
            "products": [
                {
                    "asin": "HIGH_FBA",
                    "stats": {"current": [-1, 2999, None, 50000, None, None, None, None, None, None, None, 10]}
                },
                {
                    "asin": "LOW_FBA",
                    "stats": {"current": [-1, 3499, None, 45000, None, None, None, None, None, None, None, 2]}
                }
            ]
        }

        result = await product_finder._post_filter_asins(
            domain=1,
            asins=["HIGH_FBA", "LOW_FBA"],
            max_fba_sellers=5,
            exclude_amazon_seller=False  # Don't exclude Amazon for this test
        )

        assert len(result) == 1
        assert "LOW_FBA" in result
        assert "HIGH_FBA" not in result

    @pytest.mark.asyncio
    async def test_post_filter_empty_asins_returns_empty(
        self,
        product_finder
    ):
        """Test that empty input returns empty output."""
        result = await product_finder._post_filter_asins(
            domain=1,
            asins=[],
            max_fba_sellers=5,
            exclude_amazon_seller=True
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_post_filter_handles_api_error(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test graceful handling of API errors."""
        mock_keepa_service._make_request.side_effect = Exception("API Error")

        result = await product_finder._post_filter_asins(
            domain=1,
            asins=["TEST_ASIN"],
            max_fba_sellers=5,
            exclude_amazon_seller=True
        )

        assert result == []


class TestDiscoverProductsWithProductFinder:
    """Test discover_products uses Product Finder when appropriate."""

    @pytest.fixture
    def mock_keepa_service(self):
        service = MagicMock()
        service._make_request = AsyncMock()
        service._ensure_sufficient_balance = AsyncMock()
        return service

    @pytest.fixture
    def mock_config_service(self):
        return MagicMock()

    @pytest.fixture
    def product_finder(self, mock_keepa_service, mock_config_service):
        return KeepaProductFinderService(
            keepa_service=mock_keepa_service,
            config_service=mock_config_service,
            db=None
        )

    @pytest.mark.asyncio
    async def test_uses_product_finder_with_bsr_filters(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test that Product Finder is used when BSR filters are provided."""
        # Mock /query response
        mock_keepa_service._make_request.return_value = {
            "asinList": ["ASIN1", "ASIN2"],
            "totalResults": 100,
            "tokensConsumed": 11
        }

        with patch.object(
            product_finder,
            '_discover_via_product_finder',
            new_callable=AsyncMock
        ) as mock_pf:
            mock_pf.return_value = ["ASIN1"]

            result = await product_finder.discover_products(
                domain=1,
                category=10777,  # Law subcategory
                bsr_min=30000,
                bsr_max=250000,
                use_product_finder=True
            )

            # Should have called Product Finder
            mock_pf.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_bestsellers_without_bsr_filters(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test that Bestsellers is used when no BSR/price filters."""
        mock_keepa_service._make_request.return_value = {
            "bestSellersList": {"asinList": ["ASIN1", "ASIN2"]}
        }

        with patch.object(
            product_finder,
            '_discover_via_bestsellers',
            new_callable=AsyncMock
        ) as mock_bs:
            mock_bs.return_value = ["ASIN1"]

            result = await product_finder.discover_products(
                domain=1,
                category=10777,
                use_product_finder=True
                # No BSR/price filters
            )

            # Should have called Bestsellers (no BSR/price filters)
            mock_bs.assert_called_once()

    @pytest.mark.asyncio
    async def test_respects_use_product_finder_false(
        self,
        product_finder,
        mock_keepa_service
    ):
        """Test that use_product_finder=False uses Bestsellers."""
        mock_keepa_service._make_request.return_value = {
            "bestSellersList": {"asinList": ["ASIN1"]}
        }

        with patch.object(
            product_finder,
            '_discover_via_bestsellers',
            new_callable=AsyncMock
        ) as mock_bs:
            mock_bs.return_value = ["ASIN1"]

            result = await product_finder.discover_products(
                domain=1,
                category=10777,
                bsr_min=30000,
                bsr_max=250000,
                use_product_finder=False  # Explicitly disabled
            )

            # Should use Bestsellers even with BSR filters
            mock_bs.assert_called_once()
