"""
Tests for batch API partial failure handling.
Phase 7 Audit - Ensures graceful degradation.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.autosourcing_service import AutoSourcingService
from app.core.exceptions import InsufficientTokensError


class TestBatchAPIFailures:
    """Test batch API failure scenarios."""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        mock_keepa = MagicMock()
        mock_keepa._make_request = AsyncMock()
        mock_keepa._ensure_sufficient_balance = AsyncMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.mark.asyncio
    async def test_partial_batch_success(self, service):
        """30/50 ASINs succeed - should return 30 results."""
        # Mock API returning only 30 products from 50 requested
        service.keepa_service._make_request.return_value = {
            "products": [{"asin": f"ASIN{i}"} for i in range(30)]
        }

        asins = [f"ASIN{i}" for i in range(50)]
        result = await service._fetch_products_batch(asins)

        # Only successful ones returned
        assert len(result) == 30

    @pytest.mark.asyncio
    async def test_batch_api_timeout_continues(self, service):
        """First batch times out, second succeeds."""
        call_count = 0

        async def mock_request(endpoint, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Batch timeout")
            return {"products": [{"asin": f"ASIN{i}"} for i in range(50, 100)]}

        service.keepa_service._make_request = mock_request

        # 100 ASINs = 2 batches of 50
        asins = [f"ASIN{i}" for i in range(100)]
        result = await service._fetch_products_batch(asins, batch_size=50)

        # Should have results from second batch only (50-99)
        assert len(result) == 50
        assert "ASIN50" in result

    @pytest.mark.asyncio
    async def test_batch_insufficient_tokens_raises(self, service):
        """InsufficientTokensError should propagate up."""
        service.keepa_service._ensure_sufficient_balance.side_effect = InsufficientTokensError(
            current_balance=10,
            required_tokens=50,
            endpoint="batch"
        )

        asins = ["ASIN1", "ASIN2"]

        with pytest.raises(InsufficientTokensError):
            await service._fetch_products_batch(asins)

    @pytest.mark.asyncio
    async def test_empty_batch_returns_empty_dict(self, service):
        """Empty ASIN list should return empty dict."""
        result = await service._fetch_products_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_all_batches_fail_returns_empty(self, service):
        """All batches failing should return empty dict."""
        service.keepa_service._make_request.side_effect = Exception("API Error")

        asins = [f"ASIN{i}" for i in range(50)]
        result = await service._fetch_products_batch(asins)

        assert result == {}

    @pytest.mark.asyncio
    async def test_multiple_batches_partial_failure(self, service):
        """3 batches: 1st success, 2nd fails, 3rd success."""
        call_count = 0

        async def mock_request(endpoint, params):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second batch fails
                raise Exception("Batch 2 error")
            # Return products based on batch
            batch_start = (call_count - 1) * 50
            return {
                "products": [{"asin": f"ASIN{batch_start + i}"} for i in range(50)]
            }

        service.keepa_service._make_request = mock_request

        # 150 ASINs = 3 batches of 50
        asins = [f"ASIN{i}" for i in range(150)]
        result = await service._fetch_products_batch(asins, batch_size=50)

        # Should have results from batch 1 and 3 only (100 products)
        assert len(result) == 100
        assert "ASIN0" in result      # From batch 1
        assert "ASIN50" not in result  # Batch 2 failed
        assert "ASIN100" in result    # From batch 3
