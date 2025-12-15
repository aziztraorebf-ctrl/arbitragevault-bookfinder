"""
Tests for router import integrity.
Verifies no circular imports in router architecture.
"""
import pytest
import sys
import importlib


class TestRouterImportIntegrity:
    """Tests for router module import integrity."""

    ROUTERS = [
        "app.api.v1.routers.auth",
        "app.api.v1.routers.health",
        "app.api.v1.routers.config",
        "app.api.v1.routers.views",
        "app.api.v1.routers.bookmarks",
        "app.api.v1.routers.strategic_views",
        "app.api.v1.routers.autosourcing",
        "app.api.v1.routers.niche_discovery",
    ]

    def test_all_routers_importable(self):
        """All router modules should import without errors."""
        for module_name in self.ROUTERS:
            try:
                module = importlib.import_module(module_name)
                assert hasattr(module, 'router'), f"{module_name} missing router attribute"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_no_circular_import_on_fresh_interpreter(self):
        """Fresh import should not cause circular import error."""
        # Clear cached imports
        for module_name in self.ROUTERS:
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Re-import all
        for module_name in self.ROUTERS:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                if "circular" in str(e).lower():
                    pytest.fail(f"Circular import detected in {module_name}")
                raise

    def test_main_app_imports_all_routers(self):
        """Main app should successfully register all routers."""
        from app.main import app
        assert app is not None

        # Check routes are registered
        routes = [r.path for r in app.routes]
        assert len(routes) > 20, f"Expected >20 routes, got {len(routes)}"
