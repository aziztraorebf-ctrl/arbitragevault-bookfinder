"""
Integration tests for BSR extraction with real Keepa API structures.
Uses fixtures captured from actual Keepa responses.
"""
import pytest
import json
from pathlib import Path

from app.services.keepa_parser_v2 import parse_keepa_product


@pytest.fixture
def keepa_fixtures():
    """Load real Keepa response fixtures."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "keepa_real_responses.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestBSRIntegrationRealStructure:
    """Integration tests with real Keepa API response structures."""

    def test_book_with_salesranks_extracts_latest_bsr(self, keepa_fixtures):
        """Should extract latest BSR from salesRanks array."""
        data = keepa_fixtures["book_with_salesranks"]
        result = parse_keepa_product(data)

        # salesRanks format: [ts1, bsr1, ts2, bsr2, ts3, bsr3]
        # Last element (45100) is current BSR
        assert result["current_bsr"] == 45100
        assert result["bsr_confidence"] >= 0.7

    def test_book_no_salesranks_uses_current_fallback(self, keepa_fixtures):
        """Should use stats.current when salesRanks missing."""
        data = keepa_fixtures["book_no_salesranks"]
        result = parse_keepa_product(data)

        assert result["current_bsr"] == 1234

    def test_book_stale_data_uses_avg30_fallback(self, keepa_fixtures):
        """Should use avg30 when no current data available."""
        data = keepa_fixtures["book_stale_data"]
        result = parse_keepa_product(data)

        assert result["current_bsr"] == 5678
        # Lower confidence for avg30 source
        assert result["bsr_confidence"] <= 0.8

    def test_full_parsing_pipeline_doesnt_crash(self, keepa_fixtures):
        """Full parsing pipeline should handle all fixture variations."""
        for name, data in keepa_fixtures.items():
            result = parse_keepa_product(data)
            assert "asin" in result
            assert "current_bsr" in result
            # Should not raise any exceptions
