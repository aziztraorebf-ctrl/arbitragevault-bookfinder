"""
Tests for AutoSourcing ASIN deduplication logic.
"""
import pytest
from unittest.mock import MagicMock
from app.services.autosourcing_service import AutoSourcingService

@pytest.fixture
def mock_keepa_service():
    """Mock Keepa service (not used in deduplication but required by service)."""
    return MagicMock()

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return MagicMock()

@pytest.fixture
def service(mock_db_session, mock_keepa_service):
    """AutoSourcing service with mocked dependencies."""
    return AutoSourcingService(db_session=mock_db_session, keepa_service=mock_keepa_service)

@pytest.mark.asyncio
async def test_deduplication_prevents_duplicate_analysis(service):
    """Test that duplicate ASINs are removed."""
    # Input with duplicate ASINs
    asins = ["ASIN1", "ASIN2", "ASIN1", "ASIN3", "ASIN1"]  # ASIN1 appears 3 times

    # Process with deduplication
    unique_asins = await service.process_asins_with_deduplication(asins)

    # Should only return unique ASINs
    assert len(unique_asins) == 3  # Only ASIN1, ASIN2, ASIN3

    # Verify all unique ASINs are present
    assert "ASIN1" in unique_asins
    assert "ASIN2" in unique_asins
    assert "ASIN3" in unique_asins

@pytest.mark.asyncio
async def test_deduplication_preserves_order(service):
    """Test that deduplication preserves first occurrence order."""
    # Input with specific order
    asins = ["ASIN3", "ASIN1", "ASIN2", "ASIN1", "ASIN3"]

    # Process with deduplication
    unique_asins = await service.process_asins_with_deduplication(asins)

    # Should preserve order of first occurrences
    assert unique_asins[0] == "ASIN3"  # First occurrence
    assert unique_asins[1] == "ASIN1"  # Second occurrence
    assert unique_asins[2] == "ASIN2"  # Third occurrence
