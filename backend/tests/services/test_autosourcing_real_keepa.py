"""
Test AutoSourcing with REAL Keepa Integration (RED-GREEN-REFACTOR)

These tests verify that AutoSourcing uses REAL Keepa data, not simulation.

Phase 4 RED: These tests MUST FAIL initially to prove the bug exists.
Phase 4 GREEN: After fix, tests should pass with real Keepa data.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.autosourcing_service import AutoSourcingService


class TestAutoSourcingRealKeepaIntegration:
    """Tests to verify AutoSourcing uses REAL Keepa data, not simulation."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_keepa_service(self):
        """Create a mock Keepa service that returns REAL-like data."""
        service = AsyncMock()

        # Mock can_perform_action
        service.can_perform_action = AsyncMock(return_value={
            "can_proceed": True,
            "current_balance": 500,
            "required_tokens": 50
        })

        # Mock get_product_data - returns data structure like real Keepa
        service.get_product_data = AsyncMock(return_value={
            "asin": "0134093410",
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "stats": {
                "current": [None, 4599, None, 3200, None, None, None, None, None, None,
                           None, None, None, None, None, None, None, None, 45, None],
                "avg30": [None, 4800, None, 3500, None, None, None, None, None, None,
                         None, None, None, None, None, None, None, None, 52, None]
            },
            "rootCategory": 283155,
            "categories": [283155],
            "salesRanks": {283155: [21654321, 45000, 21654400, 44500]},
            "lastUpdate": 21657000
        })

        # Mock find_products
        service.find_products = AsyncMock(return_value=["0134093410"])

        return service

    @pytest.mark.asyncio
    async def test_analyze_single_product_calls_keepa_service(
        self, mock_db_session, mock_keepa_service
    ):
        """
        RED TEST: Verify _analyze_single_product calls keepa_service.get_product_data()

        This test MUST FAIL initially because current code uses random.uniform()
        instead of calling keepa_service.get_product_data().
        """
        # Arrange
        autosourcing = AutoSourcingService(mock_db_session, mock_keepa_service)
        job_id = uuid4()
        asin = "0134093410"
        scoring_config = {
            "roi_min": 30,
            "velocity_weight": 0.4,
            "stability_weight": 0.3,
            "confidence_weight": 0.3
        }
        business_config = {
            "fba_fee_percentage": 0.15,
            "prep_cost": 2.50
        }

        # Act
        pick = await autosourcing._analyze_single_product(
            asin=asin,
            scoring_config=scoring_config,
            job_id=job_id,
            business_config=business_config
        )

        # Assert - THIS MUST FAIL initially because get_product_data is never called
        mock_keepa_service.get_product_data.assert_called_once_with(asin)

    @pytest.mark.asyncio
    async def test_analyze_single_product_uses_real_price_not_random(
        self, mock_db_session, mock_keepa_service
    ):
        """
        RED TEST: Verify _analyze_single_product uses REAL price from Keepa

        This test MUST FAIL initially because current code generates random price.
        Real price should be 45.99 (from mock stats.current[1] = 4599 cents)
        """
        # Arrange
        autosourcing = AutoSourcingService(mock_db_session, mock_keepa_service)
        job_id = uuid4()

        # Act
        pick = await autosourcing._analyze_single_product(
            asin="0134093410",
            scoring_config={"roi_min": 30},
            job_id=job_id,
            business_config={}
        )

        # Assert - THIS MUST FAIL because current code uses random.uniform(20, 300)
        # Real price from mock is 45.99 (4599 cents / 100)
        assert pick is not None

        # Price should be exactly 45.99 from mock, not random
        # Random would give a number between 20-300 that's almost never 45.99
        expected_price = 45.99
        tolerance = 0.01  # Allow 1 cent tolerance for float precision

        # This assertion WILL FAIL because random.uniform() almost never produces 45.99
        assert abs(pick.current_price - expected_price) < tolerance, (
            f"Price should be {expected_price} from Keepa, but got {pick.current_price}. "
            f"This likely means random.uniform() is being used instead of Keepa data."
        )

    @pytest.mark.asyncio
    async def test_analyze_single_product_uses_real_title_not_placeholder(
        self, mock_db_session, mock_keepa_service
    ):
        """
        RED TEST: Verify _analyze_single_product uses REAL title from Keepa

        This test MUST FAIL initially because current code generates "Product {asin}".
        Real title should be "Clean Code: A Handbook of Agile Software Craftsmanship"
        """
        # Arrange
        autosourcing = AutoSourcingService(mock_db_session, mock_keepa_service)
        job_id = uuid4()

        # Act
        pick = await autosourcing._analyze_single_product(
            asin="0134093410",
            scoring_config={"roi_min": 30},
            job_id=job_id,
            business_config={}
        )

        # Assert
        assert pick is not None

        # This MUST FAIL because current code sets title = f"Product {asin}"
        expected_title = "Clean Code: A Handbook of Agile Software Craftsmanship"
        assert pick.title == expected_title, (
            f"Title should be '{expected_title}' from Keepa, but got '{pick.title}'. "
            f"This likely means simulation data is being used instead of Keepa."
        )

    @pytest.mark.asyncio
    async def test_no_random_module_used_in_analyze(
        self, mock_db_session, mock_keepa_service
    ):
        """
        RED TEST: Verify _analyze_single_product doesn't use random module

        This test MUST FAIL initially because current code imports random.
        After fix, no random values should be generated.
        """
        # Arrange
        autosourcing = AutoSourcingService(mock_db_session, mock_keepa_service)
        job_id = uuid4()
        results = []

        # Act - Run 5 times, prices should be IDENTICAL if using real data
        for _ in range(5):
            pick = await autosourcing._analyze_single_product(
                asin="0134093410",
                scoring_config={"roi_min": 30},
                job_id=job_id,
                business_config={}
            )
            if pick:
                results.append(pick.current_price)

        # Assert - THIS MUST FAIL because random produces different values each time
        # With real Keepa data, all 5 prices should be identical
        assert len(results) == 5, "Should have 5 results"
        assert len(set(results)) == 1, (
            f"All 5 prices should be identical (from Keepa), but got different values: {results}. "
            f"This proves random.uniform() is being used."
        )


class TestAutoSourcingDiscoveryFallback:
    """Tests to verify discovery doesn't silently fall back to simulation."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def mock_keepa_service_failing(self):
        """Mock Keepa service that fails to discover products."""
        service = AsyncMock()
        service.can_perform_action = AsyncMock(return_value={
            "can_proceed": True,
            "current_balance": 500,
            "required_tokens": 50
        })
        # Simulate Keepa failure
        service.find_products = AsyncMock(side_effect=Exception("Keepa API error"))
        return service

    @pytest.mark.asyncio
    async def test_discover_products_raises_on_keepa_failure(
        self, mock_db_session, mock_keepa_service_failing
    ):
        """
        RED TEST: Verify _discover_products raises exception on Keepa failure

        This test MUST FAIL initially because current code silently falls back
        to simulation instead of raising the error.
        """
        # Arrange
        autosourcing = AutoSourcingService(mock_db_session, mock_keepa_service_failing)
        discovery_config = {
            "categories": ["Books"],
            "max_results": 20
        }

        # Act & Assert - THIS MUST FAIL because current code catches and falls back
        with pytest.raises(Exception, match="Keepa"):
            await autosourcing._discover_products(discovery_config)
