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
        # stats.current[3] = 44000, different from salesRanks to verify priority
        assert result["current_bsr"] == 45100
        assert result["bsr_confidence"] >= 0.7

    def test_book_no_salesranks_uses_current_fallback(self, keepa_fixtures):
        """Should use stats.current when salesRanks missing."""
        data = keepa_fixtures["book_no_salesranks"]
        result = parse_keepa_product(data)

        # Limitation: Parser may not expose BSR source metadata
        # This test verifies the value matches stats.current[3] = 1234
        assert result["current_bsr"] == 1234

    def test_book_stale_data_uses_avg30_fallback(self, keepa_fixtures):
        """Should use avg30 when no current data available."""
        data = keepa_fixtures["book_stale_data"]
        result = parse_keepa_product(data)

        assert result["current_bsr"] == 5678
        # Lower confidence for avg30 source
        assert result["bsr_confidence"] <= 0.8

    def test_regression_salesranks_uses_last_index(self, keepa_fixtures):
        """Regression test: should use index [-1] not [1] for latest BSR."""
        data = keepa_fixtures["book_multiple_bsr_values"]
        result = parse_keepa_product(data)

        # salesRanks: [ts1, 10000, ts2, 20000, ts3, 30000, ts4, 40000, ts5, 50000]
        # Should pick 50000 (index [-1]), not 10000 (index [1])
        assert result["current_bsr"] == 50000
        assert result["current_bsr"] != 10000

    def test_full_parsing_pipeline_doesnt_crash(self, keepa_fixtures):
        """Full parsing pipeline should handle all fixture variations."""
        for name, data in keepa_fixtures.items():
            result = parse_keepa_product(data)
            assert "asin" in result
            assert "current_bsr" in result

            # Known-good fixtures should have valid BSR
            if name in ["book_with_salesranks", "book_no_salesranks", "book_stale_data", "book_multiple_bsr_values"]:
                assert result["current_bsr"] is not None
                assert result["current_bsr"] > 0
