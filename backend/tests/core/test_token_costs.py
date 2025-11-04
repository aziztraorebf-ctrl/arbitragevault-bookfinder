"""Tests for TOKEN_COSTS registry."""
import pytest
from app.core.token_costs import (
    TOKEN_COSTS,
    ActionCost,
    CRITICAL_THRESHOLD,
    WARNING_THRESHOLD,
    SAFE_THRESHOLD
)


def test_token_costs_structure():
    """Verify TOKEN_COSTS has correct structure."""
    assert isinstance(TOKEN_COSTS, dict)
    assert len(TOKEN_COSTS) > 0

    # Verify expected actions exist
    expected_actions = ["surprise_me", "niche_discovery", "manual_search", "product_lookup", "auto_sourcing_job"]
    for action in expected_actions:
        assert action in TOKEN_COSTS

        # Verify ActionCost structure
        cost_info = TOKEN_COSTS[action]
        assert "cost" in cost_info
        assert "description" in cost_info
        assert "endpoint_type" in cost_info

        # Verify types
        assert isinstance(cost_info["cost"], int)
        assert cost_info["cost"] > 0
        assert isinstance(cost_info["description"], str)
        assert len(cost_info["description"]) > 0
        assert cost_info["endpoint_type"] in ["single", "composite", "batch"]


def test_thresholds_are_ordered():
    """Verify thresholds are in correct order."""
    assert CRITICAL_THRESHOLD < WARNING_THRESHOLD < SAFE_THRESHOLD
    assert CRITICAL_THRESHOLD == 20
    assert WARNING_THRESHOLD == 100
    assert SAFE_THRESHOLD == 200


def test_action_costs_are_reasonable():
    """Verify action costs align with Keepa API costs."""
    # Single product lookup should be 1 token
    assert TOKEN_COSTS["product_lookup"]["cost"] == 1

    # Surprise me uses bestsellers (50 tokens)
    assert TOKEN_COSTS["surprise_me"]["cost"] == 50

    # Niche discovery uses 3x bestsellers
    assert TOKEN_COSTS["niche_discovery"]["cost"] == 150

    # Manual search uses product finder (10 tokens)
    assert TOKEN_COSTS["manual_search"]["cost"] == 10

    # AutoSourcing is most expensive (composite operation)
    assert TOKEN_COSTS["auto_sourcing_job"]["cost"] >= 200
