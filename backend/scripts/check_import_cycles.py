#!/usr/bin/env python
"""
Check for circular imports in router modules.
Run: python scripts/check_import_cycles.py
"""
import sys
import importlib
import traceback
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

ROUTERS = [
    "app.api.v1.routers.auth",
    "app.api.v1.routers.health",
    "app.api.v1.routers.analyses",
    "app.api.v1.routers.batches",
    "app.api.v1.routers.keepa",
    "app.api.v1.routers.config",
    "app.api.v1.routers.autosourcing",
    "app.api.v1.routers.autoscheduler",
    "app.api.v1.routers.views",
    "app.api.v1.routers.bookmarks",
    "app.api.v1.routers.strategic_views",
    "app.api.v1.routers.stock_estimate",
    "app.api.v1.routers.niche_discovery",
]

def check_imports():
    """Try importing all routers and check for cycles."""
    errors = []

    for module_name in ROUTERS:
        try:
            # Force fresh import
            if module_name in sys.modules:
                del sys.modules[module_name]
            importlib.import_module(module_name)
            print(f"OK: {module_name}")
        except ImportError as e:
            errors.append((module_name, str(e), traceback.format_exc()))
            print(f"FAIL: {module_name} - {e}")

    return errors

if __name__ == "__main__":
    print("Checking router imports for circular dependencies...")
    errors = check_imports()

    if errors:
        print(f"\n{len(errors)} import errors found:")
        for module, error, tb in errors:
            print(f"\n{module}:\n{tb}")
        sys.exit(1)
    else:
        print("\nAll routers imported successfully!")
        sys.exit(0)
