"""Tests for KeepaService token control methods."""
import pytest
from unittest.mock import AsyncMock
from app.services.keepa_service import KeepaService
from app.core.token_costs import TOKEN_COSTS


@pytest.fixture
def keepa_service():
    """Create KeepaService with mocked check_api_balance."""
    service = KeepaService(api_key="test_key")
    # Mock check_api_balance to return token count directly
    service.check_api_balance = AsyncMock(return_value=150)
    return service


@pytest.mark.asyncio
async def test_can_perform_action_sufficient_tokens(keepa_service):
    """Test can_perform_action returns True when balance is sufficient."""
    result = await keepa_service.can_perform_action("manual_search")

    assert result["can_proceed"] is True
    assert result["current_balance"] == 150
    assert result["required_tokens"] == 10
    assert result["action"] == "manual_search"


@pytest.mark.asyncio
async def test_can_perform_action_insufficient_tokens(keepa_service):
    """Test can_perform_action returns False when balance is insufficient."""
    # Mock low balance
    keepa_service.check_api_balance = AsyncMock(return_value=5)

    result = await keepa_service.can_perform_action("surprise_me")

    assert result["can_proceed"] is False
    assert result["current_balance"] == 5
    assert result["required_tokens"] == 50
    assert result["action"] == "surprise_me"


@pytest.mark.asyncio
async def test_can_perform_action_unknown_action(keepa_service):
    """Test can_perform_action raises error for unknown action."""
    with pytest.raises(ValueError, match="Unknown action"):
        await keepa_service.can_perform_action("unknown_action")


@pytest.mark.asyncio
async def test_can_perform_action_syncs_throttle(keepa_service):
    """Test can_perform_action syncs throttle with balance."""
    await keepa_service.can_perform_action("product_lookup")

    # Verify throttle was synced with balance
    assert keepa_service.throttle.available_tokens == 150
