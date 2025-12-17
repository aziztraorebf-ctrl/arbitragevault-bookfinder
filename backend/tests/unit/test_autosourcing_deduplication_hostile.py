"""
Hostile tests for ASIN deduplication edge cases.
Phase 7 Audit - TDD approach.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.autosourcing_service import AutoSourcingService


class TestDeduplicationHostile:
    """Hostile edge case tests for deduplication."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_db = MagicMock()
        mock_keepa = MagicMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, service):
        """Empty input should return empty output."""
        result = await service.process_asins_with_deduplication([])
        assert result == []

    @pytest.mark.asyncio
    async def test_all_duplicates_returns_one(self, service):
        """All identical ASINs should return single item."""
        asins = ["ASIN1"] * 100
        result = await service.process_asins_with_deduplication(asins)
        assert len(result) == 1
        assert result[0] == "ASIN1"

    @pytest.mark.asyncio
    async def test_max_to_analyze_zero_returns_empty(self, service):
        """max_to_analyze=0 should return empty list."""
        asins = ["ASIN1", "ASIN2", "ASIN3"]
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_max_to_analyze_negative_returns_empty(self, service):
        """Negative max_to_analyze should return empty list (graceful handling)."""
        asins = ["ASIN1", "ASIN2"]
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=-1)
        assert result == []

    @pytest.mark.asyncio
    async def test_preserves_first_occurrence_order_large_list(self, service):
        """Order preservation with 1000+ items."""
        # Create list with specific pattern: 100 unique ASINs, each repeated 10x
        asins = [f"ASIN{i % 100}" for i in range(1000)]
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=100)

        # Should preserve order of first occurrences
        assert result[0] == "ASIN0"
        assert result[1] == "ASIN1"
        assert len(result) == 100

    @pytest.mark.asyncio
    async def test_none_asins_in_list_filtered(self, service):
        """None values in list should be filtered out."""
        asins = ["ASIN1", None, "ASIN2", None, "ASIN3"]
        result = await service.process_asins_with_deduplication(asins)
        assert None not in result
        assert len(result) == 3
        assert "ASIN1" in result
        assert "ASIN2" in result
        assert "ASIN3" in result

    @pytest.mark.asyncio
    async def test_empty_string_asin_filtered(self, service):
        """Empty string ASINs should be filtered out."""
        asins = ["ASIN1", "", "ASIN2", "", "ASIN3"]
        result = await service.process_asins_with_deduplication(asins)
        assert "" not in result
        assert len(result) == 3
