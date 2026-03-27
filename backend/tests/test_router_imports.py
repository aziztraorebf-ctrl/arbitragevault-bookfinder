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
        "app.api.v1.routers.keepa",
        "app.api.v1.routers.autosourcing",
        "app.api.v1.routers.autoscheduler",
        "app.api.v1.routers.stock_estimate",
        "app.api.v1.routers.textbook_analysis",
        "app.api.v1.routers.daily_review",
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
        """Fresh import should not cause circular import error.

        NOTE: We save and restore sys.modules state to avoid polluting
        other tests that rely on cached module references (e.g., Depends).
        """
        # Save current modules state
        saved_modules = {}
        for module_name in self.ROUTERS:
            if module_name in sys.modules:
                saved_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]

        try:
            # Re-import all
            for module_name in self.ROUTERS:
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    if "circular" in str(e).lower():
                        pytest.fail(f"Circular import detected in {module_name}")
                    raise
        finally:
            # Restore original modules to prevent cross-test pollution
            for module_name, module in saved_modules.items():
                sys.modules[module_name] = module

    def test_main_app_imports_all_routers(self):
        """Main app should successfully register all routers."""
        from app.main import app
        assert app is not None

        # Check routes are registered
        routes = [r.path for r in app.routes]
        assert len(routes) > 20, f"Expected >20 routes, got {len(routes)}"
