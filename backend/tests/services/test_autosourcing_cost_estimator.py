"""
Tests for AutoSourcing cost estimation service.
"""
import pytest
from unittest.mock import Mock
from app.services.autosourcing_cost_estimator import AutoSourcingCostEstimator
from app.schemas.autosourcing_safeguards import MAX_TOKENS_PER_JOB

@pytest.fixture
def mock_settings():
    """Fixture for mock settings."""
    settings = Mock()
    settings.keepa_product_finder_cost = 10
    settings.keepa_product_details_cost = 1
    settings.keepa_results_per_page = 10
    return settings

@pytest.fixture
def estimator(mock_settings):
    """Fixture for cost estimator instance."""
    return AutoSourcingCostEstimator(mock_settings)

def test_estimate_discovery_cost_basic(estimator):
    """Test basic Product Finder cost calculation (10 tokens per page)."""
    discovery_config = {
        "categories": ["books"],
        "max_results": 50
    }

    cost = estimator.estimate_discovery_cost(discovery_config)

    # Product Finder = 10 tokens per page, expect 5 pages (50/10)
    assert cost == 50  # 5 pages * 10 tokens

def test_estimate_discovery_cost_with_multiple_categories(estimator):
    """Test cost calculation with multiple categories."""
    discovery_config = {
        "categories": ["books", "electronics"],
        "max_results": 30
    }

    cost = estimator.estimate_discovery_cost(discovery_config)

    # 2 categories * 3 pages * 10 tokens = 60 tokens
    assert cost == 60

def test_estimate_analysis_cost(estimator):
    """Test product analysis cost (1 token per ASIN)."""
    num_products = 25

    cost = estimator.estimate_analysis_cost(num_products)

    # 1 token per product
    assert cost == 25

def test_estimate_total_job_cost(estimator):
    """Test complete job cost estimation."""
    discovery_config = {
        "categories": ["books"],
        "max_results": 20
    }

    total_cost = estimator.estimate_total_job_cost(discovery_config)

    # Discovery: 2 pages * 10 = 20 tokens
    # Analysis: 20 products * 1 = 20 tokens
    # Total: 40 tokens
    assert total_cost == 40

def test_estimate_respects_max_results_limit(estimator):
    """Test that cost estimation calculates real cost without internal capping."""
    discovery_config = {
        "categories": ["books"],
        "max_results": 500  # Very high
    }

    total_cost = estimator.estimate_total_job_cost(discovery_config)

    # Discovery: 50 pages * 10 = 500 tokens (no cap in estimator)
    # Analysis: 500 products * 1 = 500 tokens (no cap in estimator)
    # Total: 1000 tokens
    # Note: The actual AutoSourcing service will apply MAX_PRODUCTS_PER_SEARCH limit
    assert total_cost == 1000
