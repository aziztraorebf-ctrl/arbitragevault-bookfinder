"""
Hostile Tests for BSR Extraction Edge Cases
Tests edge cases that could cause scoring errors.
"""
import pytest
from app.services.keepa_bsr_extractors import KeepaBSRExtractor


class TestBSRExtractionHostile:
    """Hostile edge case tests for BSR extraction."""

    def test_bsr_zero_returns_none(self):
        """BSR=0 should be treated as invalid (not a real rank)."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {"283155": [1000000, 0]},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr is None, "BSR=0 should return None (invalid)"
        assert source == "none"

    def test_bsr_negative_returns_none(self):
        """BSR=-1 should be treated as invalid (Keepa convention)."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {"283155": [1000000, -1]},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr is None, "BSR=-1 should return None"

    def test_bsr_empty_salesranks_dict(self):
        """Empty salesRanks dict should not crash."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr is None
        assert source == "none"

    def test_bsr_none_salesranks(self):
        """salesRanks=None should not crash."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": None,
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr is None

    def test_bsr_missing_reference_category(self):
        """salesRankReference pointing to non-existent category."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {"999999": [1000000, 5000]},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        # Should fallback to any available category
        assert bsr == 5000
        assert source == "salesRanks"

    def test_bsr_single_element_array(self):
        """Single element array (only timestamp, no BSR)."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {"283155": [1000000]},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr is None

    def test_bsr_very_large_value(self):
        """BSR > 10 million should still be valid (some categories have this)."""
        raw_data = {
            "asin": "B000TEST",
            "salesRanks": {"283155": [1000000, 15000000]},
            "salesRankReference": 283155
        }
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        assert bsr == 15000000

    def test_bsr_tuple_in_old_format(self):
        """BSR as tuple (timestamp, value) in old csv format."""
        raw_data = {
            "asin": "B000TEST",
            "stats": {
                "current": [0, 0, 0, (1700000000, 5678), 0]
            }
        }
        # This should handle tuple unpacking or fail gracefully
        bsr, source = KeepaBSRExtractor.extract_current_bsr(raw_data)
        # Expected: either extracts 5678 or returns None (not crash)
        assert bsr is None or bsr == 5678


class TestBSRValidationHostile:
    """Hostile tests for BSR quality validation."""

    def test_validate_bsr_none_returns_invalid(self):
        """None BSR should return invalid with 0 confidence."""
        result = KeepaBSRExtractor.validate_bsr_quality(None)
        assert result["valid"] is False
        assert result["confidence"] == 0.0

    def test_validate_bsr_zero_returns_invalid(self):
        """BSR=0 should be invalid."""
        result = KeepaBSRExtractor.validate_bsr_quality(0)
        # 0 is outside range (1, 10_000_000)
        assert result["valid"] is False

    def test_validate_bsr_negative_returns_invalid(self):
        """Negative BSR should be invalid."""
        result = KeepaBSRExtractor.validate_bsr_quality(-100)
        assert result["valid"] is False

    def test_validate_source_none_returns_invalid(self):
        """source='none' should always be invalid."""
        result = KeepaBSRExtractor.validate_bsr_quality(5000, source="none")
        assert result["valid"] is False
        assert result["confidence"] == 0.0
