"""
Unit Tests - View-Specific Scoring System

Tests for scoring_v2.py and views.py router.
Covers VIEW_WEIGHTS matrix, compute_view_score(), edge cases, and endpoint integration.

Phase 2 of Strategy Refactor (strategy_refactor_v2_phase2_views)
"""

import pytest
from typing import Dict, Any

from app.services.scoring_v2 import (
    VIEW_WEIGHTS,
    compute_view_score,
    validate_view_type,
    get_available_views,
    get_view_description,
    _extract_roi_percentage,
    _extract_velocity_score,
    _extract_stability_score,
    _normalize_metric
)


# ============================================================================
# Test 1: VIEW_WEIGHTS Matrix Structure
# ============================================================================

def test_view_weights_structure():
    """Verify VIEW_WEIGHTS matrix has required structure."""
    # All expected views present
    expected_views = [
        "dashboard",
        "mes_niches",
        "analyse_strategique",
        "auto_sourcing",
        "stock_estimates",
        "niche_discovery"
    ]
    for view in expected_views:
        assert view in VIEW_WEIGHTS, f"Missing view: {view}"

    # Each view has required keys
    required_keys = ["roi", "velocity", "stability", "description"]
    for view, weights in VIEW_WEIGHTS.items():
        for key in required_keys:
            assert key in weights, f"View '{view}' missing key: {key}"

        # Weights are numeric and in reasonable range [0-1]
        assert isinstance(weights["roi"], (int, float))
        assert isinstance(weights["velocity"], (int, float))
        assert isinstance(weights["stability"], (int, float))
        assert 0 <= weights["roi"] <= 1
        assert 0 <= weights["velocity"] <= 1
        assert 0 <= weights["stability"] <= 1


def test_view_weights_business_logic():
    """Verify VIEW_WEIGHTS reflect intended business priorities."""
    # Dashboard: balanced
    assert VIEW_WEIGHTS["dashboard"]["roi"] == VIEW_WEIGHTS["dashboard"]["velocity"]

    # MesNiches: ROI > velocity
    assert VIEW_WEIGHTS["mes_niches"]["roi"] > VIEW_WEIGHTS["mes_niches"]["velocity"]

    # AnalyseStrategique: velocity > ROI
    assert VIEW_WEIGHTS["analyse_strategique"]["velocity"] > VIEW_WEIGHTS["analyse_strategique"]["roi"]

    # AutoSourcing: velocity maximal
    assert VIEW_WEIGHTS["auto_sourcing"]["velocity"] >= 0.7

    # StockEstimates: stability highest
    assert VIEW_WEIGHTS["stock_estimates"]["stability"] >= VIEW_WEIGHTS["stock_estimates"]["roi"]
    assert VIEW_WEIGHTS["stock_estimates"]["stability"] >= VIEW_WEIGHTS["stock_estimates"]["velocity"]


# ============================================================================
# Test 2: compute_view_score() - Complete Data
# ============================================================================

def test_compute_view_score_complete_data():
    """Test scoring with complete valid metrics."""
    parsed = {
        "roi": {"roi_percentage": 50.0},
        "velocity_score": 70.0,
        "stability_score": 60.0
    }

    result = compute_view_score(parsed, "dashboard", "balanced")

    # Result structure
    assert "score" in result
    assert "view_type" in result
    assert "weights_applied" in result
    assert "components" in result
    assert "raw_metrics" in result

    # Score in valid range
    assert 0 <= result["score"] <= 100

    # View type correct
    assert result["view_type"] == "dashboard"

    # Components present
    assert "roi_contribution" in result["components"]
    assert "velocity_contribution" in result["components"]
    assert "stability_contribution" in result["components"]

    # Raw metrics preserved
    assert result["raw_metrics"]["roi_pct"] == 50.0
    assert result["raw_metrics"]["velocity_score"] == 70.0
    assert result["raw_metrics"]["stability_score"] == 60.0


def test_compute_view_score_different_views():
    """Test that different views produce different scores for same data."""
    parsed = {
        "roi": {"roi_percentage": 80.0},
        "velocity_score": 40.0,
        "stability_score": 60.0
    }

    # Score for ROI-heavy view (mes_niches)
    score_roi_heavy = compute_view_score(parsed, "mes_niches", None)

    # Score for velocity-heavy view (auto_sourcing)
    score_velocity_heavy = compute_view_score(parsed, "auto_sourcing", None)

    # ROI-heavy view should score higher (data has high ROI, low velocity)
    assert score_roi_heavy["score"] > score_velocity_heavy["score"]


# ============================================================================
# Test 3: compute_view_score() - Missing Data
# ============================================================================

def test_compute_view_score_missing_metrics():
    """Test scoring with missing metrics (should use defaults)."""
    parsed = {
        "roi": {"roi_percentage": 0}
        # Missing velocity_score and stability_score
    }

    result = compute_view_score(parsed, "mes_niches", "textbook")

    # Should not crash, should return valid score
    assert result["score"] >= 0
    assert result["view_type"] == "mes_niches"

    # Defaults applied
    assert result["raw_metrics"]["velocity_score"] == 0.0
    assert result["raw_metrics"]["stability_score"] == 50.0  # Default neutral


def test_compute_view_score_empty_parsed_data():
    """Test scoring with completely empty parsed_data."""
    parsed = {}

    result = compute_view_score(parsed, "dashboard", None)

    # Should not crash
    assert result["score"] >= 0
    # Defaults: roi=0, velocity=0, stability=50
    assert result["raw_metrics"]["roi_pct"] == 0.0
    assert result["raw_metrics"]["velocity_score"] == 0.0
    assert result["raw_metrics"]["stability_score"] == 50.0


# ============================================================================
# Test 4: Invalid View Type - Fallback
# ============================================================================

def test_invalid_view_type_fallback():
    """Test that invalid view_type falls back to dashboard."""
    parsed = {
        "roi": {"roi_percentage": 50},
        "velocity_score": 50
    }

    result = compute_view_score(parsed, "invalid_view", "balanced")

    # Should fallback to dashboard
    assert result["view_type"] == "dashboard"
    assert result["weights_applied"] == {
        "roi": VIEW_WEIGHTS["dashboard"]["roi"],
        "velocity": VIEW_WEIGHTS["dashboard"]["velocity"],
        "stability": VIEW_WEIGHTS["dashboard"]["stability"]
    }


# ============================================================================
# Test 5: Strategy Boost Application
# ============================================================================

def test_strategy_boost_textbook():
    """Test that textbook strategy boosts ROI contribution."""
    parsed = {
        "roi": {"roi_percentage": 80.0},
        "velocity_score": 30.0,
        "stability_score": 50.0
    }

    # Score with textbook boost (should boost ROI)
    result_textbook = compute_view_score(parsed, "mes_niches", "textbook")

    # Score without boost
    result_no_boost = compute_view_score(parsed, "mes_niches", None)

    # Textbook boost should increase score (high ROI product)
    assert result_textbook["score"] >= result_no_boost["score"]
    assert result_textbook["strategy_profile"] == "textbook"


def test_strategy_boost_velocity():
    """Test that velocity strategy boosts velocity contribution."""
    parsed = {
        "roi": {"roi_percentage": 30.0},
        "velocity_score": 80.0,
        "stability_score": 50.0
    }

    # Score with velocity boost
    result_velocity = compute_view_score(parsed, "analyse_strategique", "velocity")

    # Score without boost
    result_no_boost = compute_view_score(parsed, "analyse_strategique", None)

    # Velocity boost should increase score (high velocity product)
    assert result_velocity["score"] >= result_no_boost["score"]
    assert result_velocity["strategy_profile"] == "velocity"


def test_strategy_boost_balanced():
    """Test that balanced strategy applies neutral boost."""
    parsed = {
        "roi": {"roi_percentage": 50.0},
        "velocity_score": 50.0,
        "stability_score": 50.0
    }

    result_balanced = compute_view_score(parsed, "dashboard", "balanced")
    result_no_boost = compute_view_score(parsed, "dashboard", None)

    # Balanced should be very close to no boost
    assert abs(result_balanced["score"] - result_no_boost["score"]) < 5.0


# ============================================================================
# Test 6: Metric Normalization Boundaries
# ============================================================================

def test_score_normalization_upper_boundary():
    """Test that metrics > 100 are clamped to 100."""
    parsed = {
        "roi": {"roi_percentage": 250.0},  # Over 100%
        "velocity_score": 150.0,
        "stability_score": 120.0
    }

    result = compute_view_score(parsed, "dashboard", None)

    # Score should not exceed theoretical max
    assert result["score"] <= 100

    # Individual contributions should be clamped
    weights = VIEW_WEIGHTS["dashboard"]
    max_possible_roi = 100 * weights["roi"]
    assert result["components"]["roi_contribution"] <= max_possible_roi + 0.01  # float tolerance


def test_score_normalization_negative_values():
    """Test that negative metrics are clamped to 0."""
    parsed = {
        "roi": {"roi_percentage": -50.0},  # Negative ROI
        "velocity_score": -10.0,
        "stability_score": -5.0
    }

    result = compute_view_score(parsed, "mes_niches", None)

    # Score should be >= 0
    assert result["score"] >= 0

    # Raw metrics should show negatives were passed
    assert result["raw_metrics"]["roi_pct"] == 0.0  # Clamped


def test_normalize_metric_function():
    """Test _normalize_metric() helper directly."""
    # Within range
    assert _normalize_metric(50, 0, 100) == 50

    # Upper boundary
    assert _normalize_metric(150, 0, 100) == 100

    # Lower boundary
    assert _normalize_metric(-50, 0, 100) == 0

    # Edge cases
    assert _normalize_metric(0, 0, 100) == 0
    assert _normalize_metric(100, 0, 100) == 100


# ============================================================================
# Test 7: Helper Functions
# ============================================================================

def test_extract_roi_percentage():
    """Test _extract_roi_percentage() helper."""
    # Valid structure
    assert _extract_roi_percentage({"roi": {"roi_percentage": 75.5}}) == 75.5

    # Missing roi dict
    assert _extract_roi_percentage({}) == 0.0

    # Missing roi_percentage key
    assert _extract_roi_percentage({"roi": {}}) == 0.0

    # Invalid type
    assert _extract_roi_percentage({"roi": "not a dict"}) == 0.0


def test_extract_velocity_score():
    """Test _extract_velocity_score() helper."""
    # Valid
    assert _extract_velocity_score({"velocity_score": 85.0}) == 85.0

    # Missing
    assert _extract_velocity_score({}) == 0.0

    # Invalid type
    assert _extract_velocity_score({"velocity_score": "invalid"}) == 0.0


def test_extract_stability_score():
    """Test _extract_stability_score() helper."""
    # Valid
    assert _extract_stability_score({"stability_score": 70.0}) == 70.0

    # Missing (default to 50 neutral)
    assert _extract_stability_score({}) == 50.0

    # Invalid type
    assert _extract_stability_score({"stability_score": "invalid"}) == 50.0


# ============================================================================
# Test 8: Validation Helpers
# ============================================================================

def test_validate_view_type():
    """Test validate_view_type() function."""
    # Valid views
    assert validate_view_type("dashboard") is True
    assert validate_view_type("mes_niches") is True
    assert validate_view_type("auto_sourcing") is True

    # Invalid views
    assert validate_view_type("invalid") is False
    assert validate_view_type("") is False
    assert validate_view_type("DASHBOARD") is False  # Case-sensitive


def test_get_available_views():
    """Test get_available_views() returns all views."""
    views = get_available_views()

    assert isinstance(views, list)
    assert len(views) == 6  # Current number of views
    assert "dashboard" in views
    assert "mes_niches" in views


def test_get_view_description():
    """Test get_view_description() returns descriptions."""
    # Valid view
    desc = get_view_description("dashboard")
    assert desc is not None
    assert isinstance(desc, str)
    assert len(desc) > 0

    # Invalid view
    assert get_view_description("invalid_view") is None


# ============================================================================
# Test 9: Components Breakdown Accuracy
# ============================================================================

def test_components_sum_equals_score():
    """Test that component contributions sum to total score (approximately)."""
    parsed = {
        "roi": {"roi_percentage": 60.0},
        "velocity_score": 70.0},
        "stability_score": 50.0
    }

    result = compute_view_score(parsed, "dashboard", None)

    # Sum components
    components_sum = (
        result["components"]["roi_contribution"] +
        result["components"]["velocity_contribution"] +
        result["components"]["stability_contribution"]
    )

    # Should equal total score (within float precision)
    assert abs(components_sum - result["score"]) < 0.1


# ============================================================================
# Test 10: Edge Case - All Metrics Zero
# ============================================================================

def test_all_metrics_zero():
    """Test scoring when all metrics are 0."""
    parsed = {
        "roi": {"roi_percentage": 0.0},
        "velocity_score": 0.0,
        "stability_score": 0.0
    }

    result = compute_view_score(parsed, "dashboard", None)

    # Score should be 0
    assert result["score"] == 0.0

    # All components should be 0
    assert result["components"]["roi_contribution"] == 0.0
    assert result["components"]["velocity_contribution"] == 0.0
    assert result["components"]["stability_contribution"] == 0.0


# ============================================================================
# Test 11: Edge Case - All Metrics at Max
# ============================================================================

def test_all_metrics_max():
    """Test scoring when all metrics are at maximum (100)."""
    parsed = {
        "roi": {"roi_percentage": 100.0},
        "velocity_score": 100.0,
        "stability_score": 100.0
    }

    result = compute_view_score(parsed, "dashboard", None)

    # Score should be high (sum of all weights * 100)
    weights = VIEW_WEIGHTS["dashboard"]
    expected_max = (weights["roi"] + weights["velocity"] + weights["stability"]) * 100

    assert abs(result["score"] - expected_max) < 1.0  # Close to theoretical max


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
