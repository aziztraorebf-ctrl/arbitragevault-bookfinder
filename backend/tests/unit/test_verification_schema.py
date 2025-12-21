"""Unit tests for verification schema.

Phase 8: Tests for VerificationRequest, VerificationResponse, and related schemas.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.verification import (
    VerificationStatus,
    VerificationChange,
    VerificationRequest,
    VerificationResponse,
    VerificationThresholds,
)


class TestVerificationStatus:
    """Tests for VerificationStatus enum."""

    def test_status_values(self):
        """Status enum has correct values."""
        assert VerificationStatus.OK == "ok"
        assert VerificationStatus.CHANGED == "changed"
        assert VerificationStatus.AVOID == "avoid"

    def test_status_from_string(self):
        """Can create status from string."""
        assert VerificationStatus("ok") == VerificationStatus.OK
        assert VerificationStatus("changed") == VerificationStatus.CHANGED
        assert VerificationStatus("avoid") == VerificationStatus.AVOID


class TestVerificationChange:
    """Tests for VerificationChange model."""

    def test_valid_change(self):
        """Can create valid change."""
        change = VerificationChange(
            field="price",
            saved_value=29.99,
            current_value=39.99,
            severity="warning",
            message="Price increased by 33%"
        )
        assert change.field == "price"
        assert change.severity == "warning"

    def test_severity_validation(self):
        """Severity must be info, warning, or critical."""
        with pytest.raises(ValidationError):
            VerificationChange(
                field="price",
                saved_value=10,
                current_value=20,
                severity="invalid",
                message="test"
            )


class TestVerificationRequest:
    """Tests for VerificationRequest model."""

    def test_valid_request_minimal(self):
        """Can create request with just ASIN."""
        req = VerificationRequest(asin="B0DJQVYV99")
        assert req.asin == "B0DJQVYV99"
        assert req.saved_price is None

    def test_valid_request_full(self):
        """Can create request with all fields."""
        req = VerificationRequest(
            asin="B0DJQVYV99",
            saved_price=Decimal("49.99"),
            saved_bsr=125000,
            saved_fba_count=3
        )
        assert req.saved_price == Decimal("49.99")
        assert req.saved_bsr == 125000

    def test_asin_length_validation(self):
        """ASIN must be exactly 10 characters."""
        with pytest.raises(ValidationError):
            VerificationRequest(asin="SHORT")

        with pytest.raises(ValidationError):
            VerificationRequest(asin="TOOLONGASIN123")

    def test_negative_price_rejected(self):
        """Negative saved_price not allowed."""
        with pytest.raises(ValidationError):
            VerificationRequest(asin="B0DJQVYV99", saved_price=Decimal("-10.00"))

    def test_zero_bsr_rejected(self):
        """BSR must be >= 1."""
        with pytest.raises(ValidationError):
            VerificationRequest(asin="B0DJQVYV99", saved_bsr=0)


class TestVerificationResponse:
    """Tests for VerificationResponse model."""

    def test_ok_response(self):
        """Can create OK response."""
        resp = VerificationResponse(
            asin="B0DJQVYV99",
            status=VerificationStatus.OK,
            message="Product conditions unchanged"
        )
        assert resp.status == VerificationStatus.OK
        assert resp.changes == []

    def test_changed_response_with_changes(self):
        """Can create CHANGED response with change list."""
        changes = [
            VerificationChange(
                field="price",
                saved_value=29.99,
                current_value=39.99,
                severity="warning",
                message="Price increased"
            )
        ]
        resp = VerificationResponse(
            asin="B0DJQVYV99",
            status=VerificationStatus.CHANGED,
            message="Price has changed",
            changes=changes
        )
        assert len(resp.changes) == 1
        assert resp.changes[0].field == "price"

    def test_avoid_response_with_amazon(self):
        """AVOID when Amazon is selling."""
        resp = VerificationResponse(
            asin="B0DJQVYV99",
            status=VerificationStatus.AVOID,
            message="Amazon is now selling this product",
            amazon_selling=True
        )
        assert resp.amazon_selling is True

    def test_response_with_current_data(self):
        """Response includes current Keepa data."""
        resp = VerificationResponse(
            asin="B0DJQVYV99",
            status=VerificationStatus.OK,
            message="OK",
            current_price=Decimal("49.99"),
            current_bsr=125000,
            current_fba_count=2
        )
        assert resp.current_price == Decimal("49.99")
        assert resp.current_bsr == 125000

    def test_verified_at_auto_generated(self):
        """verified_at is auto-generated."""
        resp = VerificationResponse(
            asin="B0DJQVYV99",
            status=VerificationStatus.OK,
            message="OK"
        )
        assert isinstance(resp.verified_at, datetime)


class TestVerificationThresholds:
    """Tests for VerificationThresholds model."""

    def test_default_thresholds(self):
        """Default thresholds are reasonable."""
        t = VerificationThresholds()
        assert t.price_change_warning == 10.0
        assert t.price_change_critical == 25.0
        assert t.bsr_change_warning == 50.0
        assert t.fba_count_critical == 5

    def test_custom_thresholds(self):
        """Can customize thresholds."""
        t = VerificationThresholds(
            price_change_warning=5.0,
            fba_count_warning=2
        )
        assert t.price_change_warning == 5.0
        assert t.fba_count_warning == 2
