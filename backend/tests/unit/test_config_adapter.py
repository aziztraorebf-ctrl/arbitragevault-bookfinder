"""Tests for ConfigService to BusinessConfigService adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.config_adapter import ConfigServiceAdapter


class TestConfigServiceAdapter:
    """Test the adapter provides ConfigService-compatible interface."""

    @pytest.mark.asyncio
    async def test_get_effective_config_with_category_id(self):
        """Test adapter converts category_id to BusinessConfigService format."""
        mock_config = {
            "roi": {"target_pct_default": 30.0},
            "fees": {"buffer_pct_default": 5.0},
            "velocity": {"fast_threshold": 80.0},
            "_meta": {"domain_id": 1, "category": "books"}
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get_service.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config(category_id=283155)

            assert result.effective_fees is not None
            assert result.effective_roi is not None
            assert result.effective_velocity is not None

    @pytest.mark.asyncio
    async def test_adapter_maps_category_id_to_name(self):
        """Test adapter maps Keepa category IDs to names."""
        adapter = ConfigServiceAdapter()

        assert adapter._category_id_to_name(283155) == "books"
        assert adapter._category_id_to_name(1000) == "default"

    @pytest.mark.asyncio
    async def test_get_effective_config_returns_correct_structure(self):
        """Test adapter returns EffectiveConfigCompat with all required fields."""
        mock_config = {
            "roi": {"target_pct_default": 25.0, "min_for_buy": 15.0},
            "fees": {"buffer_pct_default": 5.0, "fba_fee_pct": 15.0},
            "velocity": {"fast_threshold": 80.0, "slow_threshold": 30.0},
            "_meta": {
                "domain_id": 1,
                "category": "books",
                "sources": {"global": True, "domain": False, "category": True}
            }
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get_service.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config(category_id=283155)

            # Verify structure
            assert result.base_config == mock_config
            assert result.category_id == 283155
            assert result.effective_fees == {"buffer_pct_default": 5.0, "fba_fee_pct": 15.0}
            assert result.effective_roi == {"target_pct_default": 25.0, "min_for_buy": 15.0}
            assert result.effective_velocity == {"fast_threshold": 80.0, "slow_threshold": 30.0}
            # applied_overrides should contain "category" since it's True in sources
            assert "category" in result.applied_overrides

    @pytest.mark.asyncio
    async def test_get_effective_config_with_domain_id(self):
        """Test adapter passes domain_id to BusinessConfigService."""
        mock_config = {
            "roi": {"target_pct_default": 30.0},
            "fees": {"buffer_pct_default": 5.0},
            "velocity": {"fast_threshold": 80.0},
            "_meta": {"domain_id": 2, "category": "books", "sources": {}}
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get_service.return_value = mock_service

            adapter = ConfigServiceAdapter()
            await adapter.get_effective_config(category_id=283155, domain_id=2)

            # Verify domain_id was passed correctly
            mock_service.get_effective_config.assert_called_once_with(
                domain_id=2,
                category="books"
            )

    @pytest.mark.asyncio
    async def test_get_effective_config_without_category_id(self):
        """Test adapter defaults to 'books' category when no category_id provided."""
        mock_config = {
            "roi": {"target_pct_default": 30.0},
            "fees": {"buffer_pct_default": 5.0},
            "velocity": {"fast_threshold": 80.0},
            "_meta": {"domain_id": 1, "category": "books", "sources": {}}
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get_service.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config()

            # Should default to books category
            mock_service.get_effective_config.assert_called_once_with(
                domain_id=1,
                category="books"
            )
            assert result.category_id is None

    @pytest.mark.asyncio
    async def test_applied_overrides_excludes_global(self):
        """Test that applied_overrides does not include 'global' source."""
        mock_config = {
            "roi": {"target_pct_default": 30.0},
            "fees": {"buffer_pct_default": 5.0},
            "velocity": {"fast_threshold": 80.0},
            "_meta": {
                "domain_id": 1,
                "category": "books",
                "sources": {"global": True, "domain": True, "category": False}
            }
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get_service.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config(category_id=283155)

            # global should not be in applied_overrides
            assert "global" not in result.applied_overrides
            # domain should be included since it's True
            assert "domain" in result.applied_overrides
            # category should not be included since it's False
            assert "category" not in result.applied_overrides


class TestGetConfigAdapter:
    """Test the singleton getter function."""

    def test_get_config_adapter_returns_singleton(self):
        """Test that get_config_adapter returns the same instance."""
        # Reset the singleton for testing
        import app.services.config_adapter as adapter_module
        adapter_module._adapter_instance = None

        with patch('app.services.config_adapter.get_business_config_service'):
            from app.services.config_adapter import get_config_adapter

            adapter1 = get_config_adapter()
            adapter2 = get_config_adapter()

            assert adapter1 is adapter2
