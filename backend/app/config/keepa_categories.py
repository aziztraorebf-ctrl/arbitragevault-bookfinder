"""
Keepa Category Configuration - Single Source of Truth

All category IDs have been validated via Keepa /category API on 2025-12-07.
Each category must have:
- isBrowseNode = True (can be queried)
- productCount > min_products threshold

DO NOT modify IDs without re-validating via Keepa API first.
"""

from typing import TypedDict, Optional
from datetime import date


class CategoryConfig(TypedDict):
    """Configuration for a Keepa category."""
    id: int
    expected_name: str
    min_products: int
    validated_date: str
    description: Optional[str]


# =============================================================================
# VALIDATED KEEPA CATEGORY IDS
# =============================================================================
# All IDs verified via Keepa /category API on 2025-12-07
# isBrowseNode=True and productCount validated for each

KEEPA_CATEGORIES: dict[str, CategoryConfig] = {
    # Root category
    "books": {
        "id": 283155,
        "expected_name": "Books",
        "min_products": 90_000_000,
        "validated_date": "2025-12-07",
        "description": "Root Books category",
    },

    # Programming & Technology
    "programming": {
        "id": 3839,
        "expected_name": "Programming",
        "min_products": 100_000,
        "validated_date": "2025-12-07",
        "description": "Programming books - verified NOT Architecture (173508)",
    },
    "computer_technology": {
        "id": 5,
        "expected_name": "Computers & Technology",
        "min_products": 900_000,
        "validated_date": "2025-12-07",
        "description": "Computers & Technology parent category",
    },
    "computer_science": {
        "id": 3508,
        "expected_name": "Computer Science",
        "min_products": 200_000,
        "validated_date": "2025-12-07",
        "description": "Computer Science subcategory",
    },

    # Medical & Health
    "medical": {
        "id": 173514,
        "expected_name": "Medical Books",
        "min_products": 1_000_000,
        "validated_date": "2025-12-07",
        "description": "Medical Books - verified NOT PIC Microcontroller (3738)",
    },

    # Engineering
    "engineering": {
        "id": 173515,
        "expected_name": "Engineering",
        "min_products": 900_000,
        "validated_date": "2025-12-07",
        "description": "Engineering books under Engineering & Transportation",
    },

    # Business & Finance
    "accounting": {
        "id": 266117,
        "expected_name": "Accounting",
        "min_products": 200_000,
        "validated_date": "2025-12-07",
        "description": "Accounting - verified NOT Interviewing (2578)",
    },
    "business": {
        "id": 3,
        "expected_name": "Business & Money",
        "min_products": 5_000_000,
        "validated_date": "2025-12-07",
        "description": "Business & Money parent category",
    },

    # Education (replacement for non-browsable Textbooks 465600)
    "education": {
        "id": 8975347011,
        "expected_name": "Education & Teaching",
        "min_products": 1_500_000,
        "validated_date": "2025-12-07",
        "description": "Education & Teaching - replaces non-browsable Textbooks (465600)",
    },

    # Science
    "science": {
        "id": 75,
        "expected_name": "Science & Math",
        "min_products": 1_800_000,
        "validated_date": "2025-12-07",
        "description": "Science & Math parent category",
    },
}


# =============================================================================
# LEGACY MAPPING (for backward compatibility during migration)
# =============================================================================
# Maps old category names to new config keys

LEGACY_CATEGORY_MAPPING: dict[str, str] = {
    "Books": "books",
    "Medical": "medical",
    "Programming": "programming",
    "Engineering": "engineering",
    "Textbooks": "education",  # Mapped to Education (Textbooks is non-browsable)
    "Accounting": "accounting",
    "Computer & Technology": "computer_technology",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_category_id(category_name: str) -> int:
    """
    Get Keepa category ID by name.

    Args:
        category_name: Category name (supports both new and legacy names)

    Returns:
        Keepa category ID

    Raises:
        KeyError: If category not found
    """
    # Try direct lookup first
    key = category_name.lower().replace(" ", "_").replace("&", "")
    if key in KEEPA_CATEGORIES:
        return KEEPA_CATEGORIES[key]["id"]

    # Try legacy mapping
    if category_name in LEGACY_CATEGORY_MAPPING:
        legacy_key = LEGACY_CATEGORY_MAPPING[category_name]
        return KEEPA_CATEGORIES[legacy_key]["id"]

    raise KeyError(
        f"Unknown category: {category_name}. "
        f"Available: {list(KEEPA_CATEGORIES.keys())}"
    )


def get_category_config(category_name: str) -> CategoryConfig:
    """
    Get full category configuration by name.

    Args:
        category_name: Category name (supports both new and legacy names)

    Returns:
        CategoryConfig dict with id, expected_name, min_products, etc.
    """
    key = category_name.lower().replace(" ", "_").replace("&", "")
    if key in KEEPA_CATEGORIES:
        return KEEPA_CATEGORIES[key]

    if category_name in LEGACY_CATEGORY_MAPPING:
        legacy_key = LEGACY_CATEGORY_MAPPING[category_name]
        return KEEPA_CATEGORIES[legacy_key]

    raise KeyError(f"Unknown category: {category_name}")


def get_all_category_ids() -> dict[str, int]:
    """Get mapping of all category names to their IDs."""
    return {name: config["id"] for name, config in KEEPA_CATEGORIES.items()}


# =============================================================================
# VALIDATION (to be called at app startup)
# =============================================================================

class CategoryValidationError(Exception):
    """Raised when category validation fails."""
    pass


async def validate_categories_on_startup(keepa_service) -> dict[str, bool]:
    """
    Validate all category IDs against Keepa API at application startup.

    Args:
        keepa_service: KeepaService instance with get_category method

    Returns:
        Dict mapping category names to validation status

    Raises:
        CategoryValidationError: If any critical category is invalid
    """
    results = {}
    errors = []

    for name, config in KEEPA_CATEGORIES.items():
        try:
            response = await keepa_service.get_category(config["id"])

            # Check isBrowseNode
            if not response.get("isBrowseNode", False):
                errors.append(
                    f"{name} (ID={config['id']}): isBrowseNode=False, cannot query"
                )
                results[name] = False
                continue

            # Check productCount
            product_count = response.get("productCount", 0)
            if product_count < config["min_products"]:
                errors.append(
                    f"{name} (ID={config['id']}): productCount={product_count}, "
                    f"expected >= {config['min_products']}"
                )
                results[name] = False
                continue

            # Check name matches expectation
            actual_name = response.get("name", "")
            expected = config["expected_name"].lower()
            if expected not in actual_name.lower():
                errors.append(
                    f"{name} (ID={config['id']}): name='{actual_name}', "
                    f"expected to contain '{config['expected_name']}'"
                )
                results[name] = False
                continue

            results[name] = True

        except Exception as e:
            errors.append(f"{name} (ID={config['id']}): API error - {e}")
            results[name] = False

    if errors:
        error_msg = "Category validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise CategoryValidationError(error_msg)

    return results
