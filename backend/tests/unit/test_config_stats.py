"""
Unit Tests for Config Stats Endpoint
Tests database queries for config statistics.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select, func

from app.api.v1.routers.config import get_config_stats
from app.models.business_config import BusinessConfig


class TestConfigStatsQueries:
    """Tests for config statistics queries."""

    @pytest.mark.asyncio
    async def test_stats_returns_total_configs_count(self, async_db_session):
        """Should return accurate count of total configs."""
        # Create test configs
        configs = [
            BusinessConfig(
                scope="global",
                data={"test": "config1"},
                version=1,
                is_active=True
            ),
            BusinessConfig(
                scope="domain:1",
                data={"test": "config2"},
                version=1,
                is_active=True
            ),
            BusinessConfig(
                scope="category:books",
                data={"test": "config3"},
                version=1,
                is_active=False
            )
        ]

        for config in configs:
            async_db_session.add(config)
        await async_db_session.commit()

        # Mock config service
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "active_entries": 2,
            "hit_rate": 0.75
        }

        # Call the endpoint
        result = await get_config_stats(mock_service, async_db_session)

        # Assert total configs count
        assert result.total_configs == 3

    @pytest.mark.asyncio
    async def test_stats_returns_active_configs_count(self, async_db_session):
        """Should return only active configs in active_configs count."""
        # Create mix of active and inactive configs
        configs = [
            BusinessConfig(
                scope="global",
                data={"test": "active1"},
                version=1,
                is_active=True
            ),
            BusinessConfig(
                scope="domain:1",
                data={"test": "active2"},
                version=1,
                is_active=True
            ),
            BusinessConfig(
                scope="category:books",
                data={"test": "inactive1"},
                version=1,
                is_active=False
            ),
            BusinessConfig(
                scope="domain:2",
                data={"test": "inactive2"},
                version=1,
                is_active=False
            )
        ]

        for config in configs:
            async_db_session.add(config)
        await async_db_session.commit()

        # Mock config service
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "active_entries": 2,
            "hit_rate": 0.80
        }

        # Call the endpoint
        result = await get_config_stats(mock_service, async_db_session)

        # Assert active configs count
        assert result.active_configs == 2
        assert result.total_configs == 4

    @pytest.mark.asyncio
    async def test_stats_recent_changes_24h_window(self, async_db_session):
        """recent_changes should only count updates in last 24h."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
        two_days_ago = now - timedelta(hours=48)

        # Create configs with different update times
        configs = [
            BusinessConfig(
                scope="global",
                data={"test": "recent1"},
                version=1,
                is_active=True,
                updated_at=now - timedelta(hours=1)  # Within 24h
            ),
            BusinessConfig(
                scope="domain:1",
                data={"test": "recent2"},
                version=1,
                is_active=True,
                updated_at=now - timedelta(hours=12)  # Within 24h
            ),
            BusinessConfig(
                scope="category:books",
                data={"test": "old1"},
                version=1,
                is_active=True,
                updated_at=two_days_ago  # Outside 24h window
            ),
            BusinessConfig(
                scope="domain:2",
                data={"test": "old2"},
                version=1,
                is_active=True,
                updated_at=now - timedelta(hours=30)  # Outside 24h window
            )
        ]

        for config in configs:
            async_db_session.add(config)
        await async_db_session.commit()

        # Mock config service
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "active_entries": 4,
            "hit_rate": 0.85
        }

        # Call the endpoint
        result = await get_config_stats(mock_service, async_db_session)

        # Assert only recent changes counted
        assert result.recent_changes == 2
        assert result.total_configs == 4

    @pytest.mark.asyncio
    async def test_stats_handles_empty_database(self, async_db_session):
        """Should return zeros when no configs exist."""
        # Mock config service to return empty cache
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "active_entries": 0,
            "hit_rate": 0.0
        }

        # Call the endpoint with empty database
        result = await get_config_stats(mock_service, async_db_session)

        # Assert all counts are zero
        assert result.total_configs == 0
        assert result.active_configs == 0
        assert result.recent_changes == 0
        assert result.service_health == "healthy"
        assert result.cache_stats["active_entries"] == 0
        assert result.cache_stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_stats_handles_null_updated_at(self, async_db_session):
        """Should handle configs with NULL updated_at (server_default applies)."""
        # Note: Base model has server_default=func.now() for updated_at,
        # so NULL values are automatically set to current time.
        # This test verifies the query doesn't crash with NULL comparison.
        now = datetime.now(timezone.utc)
        old_date = now - timedelta(hours=72)  # 3 days ago

        configs = [
            BusinessConfig(
                scope="global",
                data={"test": "recent"},
                version=1,
                is_active=True,
                updated_at=now - timedelta(hours=1)  # Recent
            ),
            BusinessConfig(
                scope="domain:1",
                data={"test": "old1"},
                version=1,
                is_active=True,
                updated_at=old_date  # Old
            ),
            BusinessConfig(
                scope="category:books",
                data={"test": "old2"},
                version=1,
                is_active=True,
                updated_at=old_date  # Old
            )
        ]

        for config in configs:
            async_db_session.add(config)
        await async_db_session.commit()

        # Mock config service
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "active_entries": 3,
            "hit_rate": 0.90
        }

        # Call the endpoint - should not crash
        result = await get_config_stats(mock_service, async_db_session)

        # Assert counts are correct
        assert result.total_configs == 3
        assert result.active_configs == 3
        # Only config with updated_at within 24h should be counted
        assert result.recent_changes == 1
        assert result.service_health == "healthy"
