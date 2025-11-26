"""
Unit Tests for Keepa Parser v2.0 - BSR Extraction Validation
==============================================================
Tests various scenarios for BSR extraction from Keepa API responses.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.keepa_parser_v2 import (
    parse_keepa_product,
    KeepaRawParser,
    KeepaBSRExtractor,
    KeepaCSVType
)


class TestBSRExtraction:
    """Test suite for BSR extraction from various Keepa response formats."""

    def test_bsr_from_stats_current(self):
        """Test BSR extraction from stats.current[3] (primary source)."""
        raw_data = {
            "asin": "B08N5WRWNW",
            "title": "Echo Dot (Echo Dot)",
            "domainId": 1,
            "stats": {
                "current": [
                    2499,   # 0: Amazon price ($24.99)
                    2999,   # 1: New price
                    1999,   # 2: Used price
                    1234,   # 3: BSR (rank 1234) ← TARGET
                    3999,   # 4: List price
                    -1,     # 5: Collectible
                    -1,     # 6: Refurbished
                    2999,   # 7: FBM shipping
                    -1,     # 8: Lightning deal
                    -1,     # 9: Warehouse
                    2899    # 10: FBA price
                ]
            }
        }

        result = parse_keepa_product(raw_data)

        assert result["current_bsr"] == 1234
        assert result["bsr_confidence"] == 1.0  # High confidence for low BSR
        assert result["current_amazon_price"] == Decimal("24.99")

    def test_bsr_missing_stats_current(self):
        """Test fallback when stats.current is missing."""
        # Use timestamps from 2020 (very old, should be rejected)
        # Formula: keepa_time = (unix_seconds / 60) - KEEPA_TIME_OFFSET_MINUTES
        old_timestamp_1 = int(datetime(2020, 1, 1).replace(tzinfo=timezone.utc).timestamp() / 60) - 21564000
        old_timestamp_2 = int(datetime(2020, 1, 2).replace(tzinfo=timezone.utc).timestamp() / 60) - 21564000

        raw_data = {
            "asin": "0134685997",
            "title": "Effective Java",
            "domainId": 1,
            "stats": {
                # No current array
                "avg30": [0, 0, 0, 5678, 0]  # 30-day avg BSR
            },
            "csv": [
                [],  # Amazon prices
                [],  # New prices
                [],  # Used prices
                [old_timestamp_1, 4321, old_timestamp_2, 5432]  # BSR history (old data from 2020)
            ]
        }

        result = parse_keepa_product(raw_data)

        # Should fallback to avg30
        assert result["current_bsr"] == 5678
        assert result["bsr_confidence"] < 1.0  # Lower confidence for fallback

    def test_bsr_from_recent_csv_history(self):
        """Test BSR extraction from recent CSV history as fallback."""
        # Current timestamp in Keepa format (recent)
        # Formula: keepa_time = (unix_seconds / 60) - KEEPA_TIME_OFFSET_MINUTES
        now_keepa = int(datetime.now().timestamp() / 60) - 21564000
        hour_ago_keepa = now_keepa - 60  # 1 hour ago

        raw_data = {
            "asin": "B07VGRJDFY",
            "title": "Test Product",
            "domainId": 1,
            "stats": {
                "current": []  # Empty current array
            },
            "csv": [
                [],  # Amazon prices
                [],  # New prices
                [],  # Used prices
                [hour_ago_keepa, 8765, now_keepa - 30, 9999]  # Recent BSR history
            ]
        }

        extractor = KeepaBSRExtractor()
        bsr, source = extractor.extract_current_bsr(raw_data)

        assert bsr == 9999  # Should get most recent value
        assert source == "csv_recent"  # From recent csv history

    def test_bsr_value_negative_one(self):
        """Test handling of -1 (no data) BSR values."""
        raw_data = {
            "asin": "B000000000",
            "title": "No BSR Product",
            "domainId": 1,
            "stats": {
                "current": [2999, 2999, -1, -1]  # BSR is -1 (no data)
            }
        }

        result = parse_keepa_product(raw_data)

        assert result["current_bsr"] is None
        assert result["bsr_confidence"] == 0.0

    def test_bsr_validation_by_category(self):
        """Test BSR validation for different categories."""
        # Books category - high BSR
        raw_data_books = {
            "asin": "1234567890",
            "title": "Test Book",
            "category": "Books",
            "domainId": 1,
            "stats": {
                "current": [0, 0, 0, 3500000]  # BSR 3.5M (valid for books)
            }
        }

        result_books = parse_keepa_product(raw_data_books)
        assert result_books["current_bsr"] == 3500000
        assert result_books["bsr_confidence"] == 0.5  # Low confidence for high BSR

        # Electronics - same BSR would be invalid
        raw_data_electronics = {
            "asin": "B000000001",
            "title": "Test Electronics",
            "category": "Electronics",
            "domainId": 1,
            "stats": {
                "current": [0, 0, 0, 3500000]  # BSR 3.5M (out of range for electronics)
            }
        }

        extractor = KeepaBSRExtractor()
        validation = extractor.validate_bsr_quality(3500000, "electronics", "current")
        assert validation["valid"] is False
        assert validation["confidence"] == 0.3

    def test_complete_product_parsing_with_bsr(self):
        """Test complete product parsing with all BSR-related fields."""
        raw_data = {
            "asin": "B08N5WRWNW",
            "title": "Echo Dot (4th Gen)",
            "brand": "Amazon",
            "category": "Electronics",
            "domainId": 1,
            "packageDimensions": {
                "height": 3.9,
                "length": 3.9,
                "width": 3.9,
                "weight": 0.7
            },
            "stats": {
                "current": [
                    4999,   # Amazon price
                    5499,   # New price
                    3999,   # Used price
                    527,    # BSR (rank 527)
                    5999,   # List price
                    -1, -1, -1, -1, -1,
                    4899,   # FBA price
                    15,     # New count
                    8,      # Used count
                    -1, -1,
                    45,     # Rating (4.5 stars)
                    125000, # Review count
                    -1,
                    5299    # Buy Box price
                ]
            },
            "csv": [
                # Price history (last 2 points)
                [21564000, 5999, 21565000, 4999],
                [],
                [],
                # BSR history (last 2 points)
                [21564000, 1200, 21565000, 527]
            ]
        }

        result = parse_keepa_product(raw_data)

        # Verify all extracted fields
        assert result["asin"] == "B08N5WRWNW"
        assert result["current_bsr"] == 527
        assert result["bsr_confidence"] == 1.0  # High confidence for top seller
        assert result["current_amazon_price"] == Decimal("49.99")
        assert result["current_price"] == Decimal("49.99")  # Best price selected
        assert result["offers_count"] == 15

        # Verify history extraction
        assert "bsr_history" in result
        assert len(result["bsr_history"]) == 2
        assert result["bsr_history"][-1][1] == 527  # Last BSR value

        assert "price_history" in result
        assert len(result["price_history"]) == 2
        assert result["price_history"][-1][1] == 49.99  # Last price value


class TestKeepaRawParser:
    """Test low-level parser functions."""

    def test_price_conversion(self):
        """Test Keepa price to decimal conversion."""
        parser = KeepaRawParser()

        # Test various price formats
        assert parser._convert_price(2999) == Decimal("29.99")
        assert parser._convert_price(100) == Decimal("1.00")
        assert parser._convert_price(0) == Decimal("0.00")
        assert parser._convert_price(999999) == Decimal("9999.99")

    def test_timestamp_conversion(self):
        """Test Keepa timestamp conversions."""
        parser = KeepaRawParser()

        # Test round-trip conversion (UTC required for Keepa timestamps)
        now = datetime.utcnow().replace(microsecond=0)
        keepa_time = parser._datetime_to_keepa(now)
        converted_back = parser._keepa_to_datetime(keepa_time)

        # Should be within 1 minute (Keepa precision)
        assert abs((converted_back - now).total_seconds()) < 60

    def test_time_series_parsing(self):
        """Test parsing of Keepa time series format."""
        parser = KeepaRawParser()

        # Create test data: [timestamp, value, timestamp, value]
        now_keepa = parser._datetime_to_keepa(datetime.now())
        test_data = [
            now_keepa - 100, 1000,  # 100 minutes ago, BSR 1000
            now_keepa - 50, 1500,   # 50 minutes ago, BSR 1500
            now_keepa - 10, 2000,   # 10 minutes ago, BSR 2000
            now_keepa - 5, -1,      # 5 minutes ago, no data
            now_keepa, 2500         # Now, BSR 2500
        ]

        cutoff = now_keepa - 200  # Include all data
        result = parser._parse_time_series(test_data, cutoff, convert_price=False)

        assert len(result) == 4  # Should exclude the -1 value
        assert result[0][1] == 1000
        assert result[-1][1] == 2500


class TestKeepaBSRExtractor:
    """Test business logic for BSR extraction."""

    def test_bsr_extraction_priority(self):
        """Test that extraction follows correct priority order."""
        extractor = KeepaBSRExtractor()

        # Scenario 1: All sources available - should use stats.current
        raw_data = {
            "asin": "TEST001",
            "stats": {
                "current": [0, 0, 0, 1000],  # Primary source
                "avg30": [0, 0, 0, 2000]     # Fallback
            },
            "csv": [[],[],[],[21564000, 3000]]  # Historical
        }

        bsr, source = extractor.extract_current_bsr(raw_data)
        assert bsr == 1000
        assert source == "current"

        # Scenario 2: No stats.current - should use recent csv
        # Formula: keepa_time = (unix_seconds / 60) - KEEPA_TIME_OFFSET_MINUTES
        now_keepa = int(datetime.now().timestamp() / 60) - 21564000
        raw_data = {
            "asin": "TEST002",
            "stats": {
                "current": [],  # Empty
                "avg30": [0, 0, 0, 2000]
            },
            "csv": [[],[],[],[now_keepa - 10, 1500]]  # Recent history
        }

        bsr, source = extractor.extract_current_bsr(raw_data)
        assert bsr == 1500
        assert source == "csv_recent"

        # Scenario 3: Only avg30 available
        raw_data = {
            "asin": "TEST003",
            "stats": {
                "current": [],
                "avg30": [0, 0, 0, 3000]
            },
            "csv": []
        }

        bsr, source = extractor.extract_current_bsr(raw_data)
        assert bsr == 3000
        assert source == "avg30"

    def test_bsr_quality_validation(self):
        """Test BSR quality assessment logic."""
        extractor = KeepaBSRExtractor()

        # Test various BSR values and categories (with "current" source = no penalty)
        test_cases = [
            (100, "books", "current", True, 1.0),        # Top seller books
            (50000, "electronics", "current", True, 0.9), # Good electronics BSR
            (5000000, "books", "current", True, 0.5),    # High but valid books BSR
            (5000000, "electronics", "current", False, 0.3), # Invalid electronics BSR
            (None, "any", "none", False, 0.0),        # No BSR data
        ]

        for bsr, category, source, expected_valid, expected_confidence in test_cases:
            result = extractor.validate_bsr_quality(bsr, category, source)
            assert result["valid"] == expected_valid
            assert abs(result["confidence"] - expected_confidence) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])