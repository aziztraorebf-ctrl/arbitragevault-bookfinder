"""
Route Regression Tests - Verify all expected routes are registered.

TDD: These tests verify that router consolidation doesn't break any routes.
Run before and after migration to ensure no regression.

NOTE: These tests check route REGISTRATION in OpenAPI, not runtime behavior
(which would require DB connection).
"""

import pytest


class TestRouterRegistration:
    """Test that all routers are correctly registered by checking imports."""

    def test_main_imports_all_routers(self):
        """Verify main.py can import all routers without errors."""
        # This will fail if any router has import errors
        from app.main import app
        assert app is not None

    def test_all_expected_routers_imported(self):
        """Verify all expected router modules are importable."""
        # All routers now in v1/routers (migration complete)
        from app.api.v1.routers import (
            auth, health, analyses, batches, keepa, config,
            autosourcing, autoscheduler, views,
            bookmarks, strategic_views, stock_estimate, niche_discovery
        )

        # Legacy endpoints (still in v1/endpoints)
        from app.api.v1.endpoints import products, niches, analytics, asin_history

        # All imports successful
        assert all([
            auth, health, analyses, batches, keepa, config,
            autosourcing, autoscheduler, views,
            bookmarks, strategic_views, stock_estimate, niche_discovery,
            products, niches, analytics, asin_history
        ])

    def test_routers_have_router_attribute(self):
        """Verify each router module exposes a 'router' attribute."""
        from app.api.v1.routers import (
            health, config, views, autosourcing,
            bookmarks, strategic_views, stock_estimate, niche_discovery
        )

        assert hasattr(health, 'router'), "health module missing router"
        assert hasattr(config, 'router'), "config module missing router"
        assert hasattr(views, 'router'), "views module missing router"
        assert hasattr(autosourcing, 'router'), "autosourcing module missing router"
        assert hasattr(bookmarks, 'router'), "bookmarks module missing router"
        assert hasattr(strategic_views, 'router'), "strategic_views module missing router"
        assert hasattr(stock_estimate, 'router'), "stock_estimate module missing router"
        assert hasattr(niche_discovery, 'router'), "niche_discovery module missing router"


class TestRouteRegistration:
    """Test that routes are registered in OpenAPI schema."""

    def test_openapi_schema_has_expected_paths(self):
        """Verify OpenAPI schema includes expected route paths."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        # Expected routes that must exist
        expected_routes = [
            "/api/v1/health/live",
            "/api/v1/health/ready",
            "/api/v1/config/",
            "/api/v1/config/stats",
            "/api/v1/config/health",
            "/api/v1/views/",
            "/api/v1/autosourcing/jobs",
            "/api/v1/bookmarks/niches",
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

        # We expect at least 20 routes
        assert len(paths) >= 20, f"Too few routes registered: {len(paths)}"

        print(f"Total routes registered: {len(paths)}")


class TestRouterUnification:
    """Test router architecture after consolidation."""

    def test_no_duplicate_prefixes(self):
        """Verify no duplicate route prefixes exist."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = list(openapi_schema.get("paths", {}).keys())

        # Check for potential duplicates (same endpoint registered twice)
        # This would indicate router consolidation issues
        path_set = set(paths)
        assert len(paths) == len(path_set), "Duplicate routes detected!"

    def test_views_routes_exist(self):
        """Verify views routes exist with correct prefix."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        # Check views routes exist
        views_routes = [p for p in paths if "/views" in p.lower()]
        assert len(views_routes) > 0, "No views routes found"

        print(f"Views routes: {views_routes}")

    def test_bookmarks_has_api_v1_prefix(self):
        """Verify bookmarks route has /api/v1 prefix."""
        from app.main import app

        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        # Check bookmarks routes exist with /api/v1 prefix
        bookmark_routes = [p for p in paths if "bookmark" in p.lower()]
        for route in bookmark_routes:
            assert route.startswith("/api/v1"), f"Bookmark route {route} missing /api/v1 prefix"
