"""Unit tests for VerificationService.

Phase 8: Tests for product verification logic with mocked Keepa data.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.services.verification_service import (
    VerificationService,
    calculate_profit,
)
from app.schemas.verification import (
    VerificationStatus,
    VerificationRequest,
    VerificationThresholds,
)


class TestCalculateProfit:
    """Tests for profit calculation function."""

    def test_basic_profit_calculation(self):
        """Calculate profit for $50 book."""
        # $50 sell, $25 buy (50%), fees approx $13.80
        # Profit = 50 - 25 - 13.80 = ~$11.20
        profit = calculate_profit(50.0)
        assert 10 < profit < 13, f"Expected ~$11 profit, got ${profit:.2f}"

    def test_high_price_book(self):
        """Higher price = higher profit."""
        profit_50 = calculate_profit(50.0)
        profit_100 = calculate_profit(100.0)
        assert profit_100 > profit_50

    def test_low_price_book_marginal(self):
        """Low price books have thin margins."""
        profit = calculate_profit(20.0)
        assert profit < 5, "Low price books should have low profit"


class TestVerificationServiceExtractData:
    """Tests for _extract_current_data method."""

    @pytest.fixture
    def service(self):
        mock_keepa = MagicMock()
        return VerificationService(keepa_service=mock_keepa)

    def test_extract_price_from_current(self, service):
        """Extract price from stats.current array."""
        product = {
            "stats": {
                "current": [0, 4999, 0, 150000, 0, 0, 0, 0, 0, 0, 0, 3]
            },
            "availabilityAmazon": -1
        }
        result = service._extract_current_data(product)
        assert result["price"] == Decimal("49.99")

    def test_extract_bsr_from_current(self, service):
        """Extract BSR from stats.current array."""
        product = {
            "stats": {
                "current": [0, 4999, 0, 150000, 0, 0, 0, 0, 0, 0, 0, 3]
            },
            "availabilityAmazon": -1
        }
        result = service._extract_current_data(product)
        assert result["bsr"] == 150000

    def test_extract_fba_count_from_current(self, service):
        """Extract FBA count from stats.current array."""
        product = {
            "stats": {
                "current": [0, 4999, 0, 150000, 0, 0, 0, 0, 0, 0, 0, 3]
            },
            "availabilityAmazon": -1
        }
        result = service._extract_current_data(product)
        assert result["fba_count"] == 3

    def test_detect_amazon_selling_via_availability(self, service):
        """Detect Amazon selling via availabilityAmazon >= 0."""
        product = {
            "stats": {"current": [0, 4999, 0, 150000]},
            "availabilityAmazon": 0  # Amazon is selling
        }
        result = service._extract_current_data(product)
        assert result["amazon_selling"] is True

    def test_detect_amazon_selling_via_price(self, service):
        """Detect Amazon selling via amazon price > 0."""
        product = {
            "stats": {"current": [3999, 4999, 0, 150000]},  # Amazon price at index 0
            "availabilityAmazon": -1
        }
        result = service._extract_current_data(product)
        assert result["amazon_selling"] is True

    def test_no_amazon_when_not_selling(self, service):
        """amazon_selling is False when Amazon not present."""
        product = {
            "stats": {"current": [0, 4999, 0, 150000]},  # Amazon price = 0
            "availabilityAmazon": -1
        }
        result = service._extract_current_data(product)
        assert result["amazon_selling"] is False


class TestVerificationServiceDetectChanges:
    """Tests for _detect_changes method."""

    @pytest.fixture
    def service(self):
        mock_keepa = MagicMock()
        thresholds = VerificationThresholds(
            price_change_warning=10.0,
            price_change_critical=25.0,
            bsr_change_warning=50.0,
            bsr_change_critical=100.0,
            fba_count_warning=3,
            fba_count_critical=5
        )
        return VerificationService(keepa_service=mock_keepa, thresholds=thresholds)

    def test_no_changes_when_similar(self, service):
        """No changes detected when values are similar."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_price=Decimal("50.00"),
            saved_bsr=150000,
            saved_fba_count=3
        )
        current = {"price": Decimal("51.00"), "bsr": 148000, "fba_count": 3}
        changes = service._detect_changes(request, current)
        assert len(changes) == 0

    def test_price_warning_detected(self, service):
        """Price warning when change >= 10% but < 25%."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_price=Decimal("50.00")
        )
        current = {"price": Decimal("58.00")}  # 16% increase
        changes = service._detect_changes(request, current)
        assert len(changes) == 1
        assert changes[0].severity == "warning"
        assert changes[0].field == "price"

    def test_price_critical_detected(self, service):
        """Price critical when change >= 25%."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_price=Decimal("50.00")
        )
        current = {"price": Decimal("65.00")}  # 30% increase
        changes = service._detect_changes(request, current)
        assert len(changes) == 1
        assert changes[0].severity == "critical"

    def test_bsr_warning_detected(self, service):
        """BSR warning when change >= 50% but < 100%."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_bsr=100000
        )
        current = {"bsr": 160000}  # 60% worse
        changes = service._detect_changes(request, current)
        assert len(changes) == 1
        assert changes[0].severity == "warning"
        assert "worsened" in changes[0].message

    def test_fba_count_warning_detected(self, service):
        """FBA count warning when increase >= 3."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_fba_count=2
        )
        current = {"fba_count": 5}  # +3 sellers
        changes = service._detect_changes(request, current)
        assert len(changes) == 1
        assert changes[0].severity == "warning"

    def test_fba_count_critical_detected(self, service):
        """FBA count critical when increase >= 5."""
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_fba_count=2
        )
        current = {"fba_count": 8}  # +6 sellers
        changes = service._detect_changes(request, current)
        assert len(changes) == 1
        assert changes[0].severity == "critical"


class TestVerificationServiceDetermineStatus:
    """Tests for _determine_status method."""

    @pytest.fixture
    def service(self):
        mock_keepa = MagicMock()
        return VerificationService(keepa_service=mock_keepa)

    def test_ok_when_no_changes(self, service):
        """Status OK when no changes detected."""
        status, message = service._determine_status([], {})
        assert status == VerificationStatus.OK
        assert "unchanged" in message.lower()

    def test_changed_when_warnings(self, service):
        """Status CHANGED when only warnings."""
        from app.schemas.verification import VerificationChange
        changes = [
            VerificationChange(
                field="price",
                saved_value=50,
                current_value=58,
                severity="warning",
                message="Price increased"
            )
        ]
        status, message = service._determine_status(changes, {})
        assert status == VerificationStatus.CHANGED
        assert "price" in message.lower()

    def test_avoid_when_critical(self, service):
        """Status AVOID when any critical change."""
        from app.schemas.verification import VerificationChange
        changes = [
            VerificationChange(
                field="bsr",
                saved_value=100000,
                current_value=250000,
                severity="critical",
                message="BSR worsened"
            )
        ]
        status, message = service._determine_status(changes, {})
        assert status == VerificationStatus.AVOID


class TestVerificationServiceVerifyProduct:
    """Tests for verify_product method (integration with mocked Keepa)."""

    @pytest.fixture
    def mock_keepa(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_verify_ok_product(self, mock_keepa):
        """Verify returns OK for unchanged product."""
        mock_keepa.get_product_data.return_value = {
            "stats": {"current": [0, 5000, 0, 150000, 0, 0, 0, 0, 0, 0, 0, 3]},
            "availabilityAmazon": -1
        }

        service = VerificationService(keepa_service=mock_keepa)
        request = VerificationRequest(
            asin="B0DJQVYV99",
            saved_price=Decimal("50.00"),
            saved_bsr=150000,
            saved_fba_count=3
        )

        response = await service.verify_product(request)
        assert response.status == VerificationStatus.OK
        assert response.current_price == Decimal("50.00")
        assert response.amazon_selling is False

    @pytest.mark.asyncio
    async def test_verify_avoid_when_amazon_selling(self, mock_keepa):
        """Verify returns AVOID when Amazon is selling."""
        mock_keepa.get_product_data.return_value = {
            "stats": {"current": [3999, 5000, 0, 150000]},
            "availabilityAmazon": 0  # Amazon selling
        }

        service = VerificationService(keepa_service=mock_keepa)
        request = VerificationRequest(asin="B0DJQVYV99")

        response = await service.verify_product(request)
        assert response.status == VerificationStatus.AVOID
        assert response.amazon_selling is True
        assert "Amazon" in response.message

    @pytest.mark.asyncio
    async def test_verify_product_not_found(self, mock_keepa):
        """Verify returns AVOID when product not found."""
        mock_keepa.get_product_data.return_value = None

        service = VerificationService(keepa_service=mock_keepa)
        request = VerificationRequest(asin="B0DJQVYV99")

        response = await service.verify_product(request)
        assert response.status == VerificationStatus.AVOID
        assert "not found" in response.message.lower()

    @pytest.mark.asyncio
    async def test_verify_includes_profit_calculation(self, mock_keepa):
        """Verify includes estimated profit."""
        mock_keepa.get_product_data.return_value = {
            "stats": {"current": [0, 5000, 0, 150000, 0, 0, 0, 0, 0, 0, 0, 3]},
            "availabilityAmazon": -1
        }

        service = VerificationService(keepa_service=mock_keepa)
        request = VerificationRequest(asin="B0DJQVYV99")

        response = await service.verify_product(request)
        assert response.estimated_profit is not None
        assert response.estimated_profit > 0
