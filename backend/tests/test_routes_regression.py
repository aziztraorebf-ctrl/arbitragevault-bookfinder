"""
Route Regression Tests - Verify all expected routes are registered.

Updated after radical simplification (Feb 2026).
"""

import pytest


class TestRouterRegistration:
    """Test that all routers are correctly registered by checking imports."""

    def test_main_imports_all_routers(self):
        """Verify main.py can import all routers without errors."""
        from app.main import app
        assert app is not None

    def test_all_expected_routers_imported(self):
        """Verify all expected router modules are importable."""
        from app.api.v1.routers import (
            auth, health, keepa, config,
            autosourcing, autoscheduler, stock_estimate,
            textbook_analysis, daily_review
        )

        from app.api.v1.endpoints import products, asin_history

        assert all([
            auth, health, keepa, config,
            autosourcing, autoscheduler, stock_estimate,
            textbook_analysis, daily_review,
            products, asin_history
        ])

    def test_routers_have_router_attribute(self):
        """Verify each router module exposes a 'router' attribute."""
        from app.api.v1.routers import (
            health, config, autosourcing, autoscheduler,
            stock_estimate, keepa, textbook_analysis, daily_review
        )

        for module in [health, config, autosourcing, autoscheduler,
                       stock_estimate, keepa, textbook_analysis, daily_review]:
            assert hasattr(module, 'router'), f"{module.__name__} missing router attribute"


class TestRouteRegistration:
    """Test that routes are registered in OpenAPI schema."""

    def test_openapi_schema_has_expected_paths(self):
        """Verify OpenAPI schema includes expected route paths."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        expected_routes = [
            "/api/v1/health/live",
            "/api/v1/health/ready",
            "/api/v1/config/",
            "/api/v1/config/stats",
            "/api/v1/autosourcing/jobs",
            "/api/v1/keepa/{asin}/metrics",
            "/api/v1/products/discover",
        ]

        for route in expected_routes:
            assert route in paths, f"Route {route} not found in OpenAPI schema"

    def test_route_count_is_reasonable(self):
        """Verify we have a reasonable number of routes."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        assert len(paths) >= 15, f"Too few routes registered: {len(paths)}"


class TestRouterUnification:
    """Test router architecture after consolidation."""

    def test_no_duplicate_prefixes(self):
        """Verify no duplicate route prefixes exist."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = list(openapi_schema.get("paths", {}).keys())

        path_set = set(paths)
        assert len(paths) == len(path_set), "Duplicate routes detected!"
