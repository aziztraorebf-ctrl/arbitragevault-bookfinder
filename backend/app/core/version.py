"""
ArbitrageVault Backend - Version and Build Information
=======================================================

Build metadata and version tracking for deployment verification.
"""

from datetime import datetime

# Build Tag for Strategy Refactor V2 (Phase 1: Core Implementation)
BUILD_TAG = "strategy_refactor_v2_phase1_shadowmode"

# Keepa SDK Version
KEEPA_SDK_VERSION = "1.3.0"

# Migration Details
MIGRATION_DATE = "2025-10-08"
MIGRATION_TIMESTAMP = datetime(2025, 10, 8, 14, 0, 0)

# Verification Sources
VERIFIED_SOURCES = [
    "Keepa SDK v1.3.0: https://github.com/akaszynski/keepa",
    "PyPI: https://pypi.org/project/keepa/",
    "Context7 Library ID: /akaszynski/keepa",
    "Production test: Render API 2025-10-08 13:34 UTC",
    "Documentation: docs/keepa_structure_verified.md"
]

# Refactor Summary
REFACTOR_SUMMARY = {
    "description": "NumPy-safe refactor of Keepa SDK integration",
    "scope": [
        "backend/app/utils/keepa_utils.py (NEW)",
        "backend/app/services/keepa_parser_v2.py",
        "backend/app/services/keepa_service.py"
    ],
    "changes": [
        "Added numpy-safe helpers: safe_array_check(), safe_array_to_list(), safe_value_check()",
        "Replaced unsafe numpy comparisons (== -1, != -1)",
        "Eliminated ambiguous truth value errors",
        "Added source verification comments"
    ],
    "validation": [
        "All tests passing",
        "Grep verification: 0 unsafe patterns",
        "Production API validated: current_price + current_bsr extracted"
    ]
}

def get_version_info() -> dict:
    """Return version information dictionary."""
    return {
        "build_tag": BUILD_TAG,
        "keepa_sdk_version": KEEPA_SDK_VERSION,
        "migration_date": MIGRATION_DATE,
        "verified_sources": VERIFIED_SOURCES,
        "refactor_summary": REFACTOR_SUMMARY
    }
