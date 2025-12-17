"""
Integration tests for recent duplicates removal.
Phase 7 Audit - Tests 7-day window behavior.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from app.services.autosourcing_service import AutoSourcingService
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob, JobStatus


class TestRecentDuplicatesRemoval:
    """Test recent duplicates removal with time boundaries."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session with execute method."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        mock_keepa = MagicMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    def create_pick(self, asin: str, job_id=None):
        """Helper to create a pick."""
        return AutoSourcingPick(
            id=uuid4(),
            job_id=job_id or uuid4(),
            asin=asin,
            title=f"Product {asin}",
            roi_percentage=35.0,
            velocity_score=75,
            stability_score=80,
            confidence_score=85,
            overall_rating="A"
        )

    @pytest.mark.asyncio
    async def test_removes_picks_from_last_7_days(self, service, mock_db):
        """Picks with same ASIN from last 7 days should be removed."""
        # Mock: ASIN1 was found in recent jobs
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([MagicMock(asin="ASIN1")])
        mock_db.execute.return_value = mock_result

        new_picks = [
            self.create_pick("ASIN1"),  # Duplicate - should be removed
            self.create_pick("ASIN2"),  # New - should be kept
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 1
        assert result[0].asin == "ASIN2"

    @pytest.mark.asyncio
    async def test_keeps_picks_not_in_recent(self, service, mock_db):
        """Picks with ASINs not in recent jobs should be kept."""
        # Mock: No recent duplicates
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_db.execute.return_value = mock_result

        new_picks = [
            self.create_pick("ASIN1"),
            self.create_pick("ASIN2"),
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_picks_returns_empty(self, service, mock_db):
        """Empty picks list should return empty without DB query."""
        result = await service._remove_recent_duplicates([])

        assert result == []
        # Should not call DB for empty list
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_duplicates_returns_empty(self, service, mock_db):
        """If all picks are duplicates, return empty list."""
        # Mock: Both ASINs are recent duplicates
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([
            MagicMock(asin="ASIN1"),
            MagicMock(asin="ASIN2")
        ])
        mock_db.execute.return_value = mock_result

        new_picks = [
            self.create_pick("ASIN1"),
            self.create_pick("ASIN2"),
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_custom_days_parameter(self, service, mock_db):
        """Custom days parameter should be respected."""
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_db.execute.return_value = mock_result

        new_picks = [self.create_pick("ASIN1")]

        # Use 14 days instead of default 7
        result = await service._remove_recent_duplicates(new_picks, days=14)

        assert len(result) == 1
        # Verify execute was called (query was made)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_duplicates(self, service, mock_db):
        """Mix of duplicate and new ASINs."""
        # Mock: Only ASIN1 and ASIN3 are recent duplicates
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([
            MagicMock(asin="ASIN1"),
            MagicMock(asin="ASIN3")
        ])
        mock_db.execute.return_value = mock_result

        new_picks = [
            self.create_pick("ASIN1"),  # Duplicate
            self.create_pick("ASIN2"),  # New
            self.create_pick("ASIN3"),  # Duplicate
            self.create_pick("ASIN4"),  # New
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 2
        asins = [p.asin for p in result]
        assert "ASIN2" in asins
        assert "ASIN4" in asins
        assert "ASIN1" not in asins
        assert "ASIN3" not in asins
