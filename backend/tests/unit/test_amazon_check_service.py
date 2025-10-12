"""Unit tests for Amazon Check Service - Phase 2.5A Step 1.

Tests detection of Amazon presence on product listings using Keepa offers data.

BUILD_TAG: PHASE_2_5A_STEP_1
"""

import pytest
from app.services.amazon_check_service import check_amazon_presence


# ============================================================================
# Test Data - Real Keepa Field Structures
# ============================================================================

def create_keepa_product_with_amazon_offers(amazon_on_listing=True, amazon_has_buybox=False):
    """Create mock Keepa product dict with Amazon offers."""
    offers = []

    # Amazon offer (if present)
    if amazon_on_listing:
        offers.append({
            "sellerId": "ATVPDKIKX0DER",  # Real Amazon seller ID
            "isAmazon": True,
            "isFBA": False,
            "condition": 0,  # New
            "price": 1500,  # $15.00 in Keepa format (cents)
        })

    # 3rd party offer
    offers.append({
        "sellerId": "A1QUAC68EAM09F",  # Random 3rd party seller
        "isAmazon": False,
        "isFBA": True,
        "condition": 0,
        "price": 1299,  # $12.99
    })

    # Another 3rd party
    offers.append({
        "sellerId": "A18WXU4I7YR6UA",
        "isAmazon": False,
        "isFBA": False,
        "condition": 1,  # Used
        "price": 999,
    })

    # Buy Box history
    buybox_history = []
    if amazon_has_buybox:
        # Most recent Buy Box winner is Amazon
        buybox_history = [
            1672531200,  # Timestamp (Keepa time minutes)
            "A1QUAC68EAM09F",  # Previous winner
            1704067200,  # Newer timestamp
            "ATVPDKIKX0DER",  # Current Amazon winner
        ]
    else:
        # 3rd party has Buy Box
        buybox_history = [
            1672531200,
            "ATVPDKIKX0DER",  # Old Amazon
            1704067200,
            "A1QUAC68EAM09F",  # Current 3rd party winner
        ]

    # Live offers order (first = Buy Box winner typically)
    if amazon_has_buybox:
        live_offers_order = [0, 1, 2]  # Amazon is first (index 0)
    else:
        live_offers_order = [1, 0, 2]  # 3rd party is first (index 1)

    return {
        "asin": "B0088PUEPK",
        "title": "Test Product",
        "offers": offers,
        "buyBoxSellerIdHistory": buybox_history,
        "liveOffersOrder": live_offers_order,
    }


def create_keepa_product_no_offers():
    """Create Keepa product with no offers data (e.g., old product or no offers retrieved)."""
    return {
        "asin": "B0088PUEPK",
        "title": "Test Product No Offers",
        # No offers field
    }


def create_keepa_product_empty_offers():
    """Create Keepa product with empty offers array."""
    return {
        "asin": "B0088PUEPK",
        "title": "Test Product Empty Offers",
        "offers": [],
    }


# ============================================================================
# Tests - Amazon Detection
# ============================================================================

def test_amazon_on_listing_true():
    """Test: Amazon has an offer on the listing."""
    keepa_data = create_keepa_product_with_amazon_offers(
        amazon_on_listing=True,
        amazon_has_buybox=False
    )

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Should detect Amazon on listing"
    # Amazon present but doesn't have Buy Box
    assert result["amazon_buybox"] is False, "3rd party has Buy Box"


def test_amazon_on_listing_false():
    """Test: Amazon has NO offer on the listing."""
    keepa_data = create_keepa_product_with_amazon_offers(
        amazon_on_listing=False,  # Remove Amazon from offers
        amazon_has_buybox=False
    )

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is False, "No Amazon offer present"
    assert result["amazon_buybox"] is False, "No Buy Box for Amazon"


def test_amazon_owns_buybox():
    """Test: Amazon owns the Buy Box."""
    keepa_data = create_keepa_product_with_amazon_offers(
        amazon_on_listing=True,
        amazon_has_buybox=True  # Amazon is Buy Box winner
    )

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Amazon present on listing"
    assert result["amazon_buybox"] is True, "Amazon owns Buy Box"


def test_amazon_lost_buybox():
    """Test: Amazon has offer but lost Buy Box to 3rd party."""
    keepa_data = create_keepa_product_with_amazon_offers(
        amazon_on_listing=True,
        amazon_has_buybox=False  # 3rd party has Buy Box now
    )

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Amazon still on listing"
    assert result["amazon_buybox"] is False, "3rd party owns Buy Box"


# ============================================================================
# Tests - Edge Cases
# ============================================================================

def test_no_offers_data():
    """Test: No offers field in Keepa response (old product or offers not retrieved)."""
    keepa_data = create_keepa_product_no_offers()

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is False, "Default to False when no offers"
    assert result["amazon_buybox"] is False, "Default to False when no offers"


def test_empty_offers_array():
    """Test: Empty offers array (no active offers)."""
    keepa_data = create_keepa_product_empty_offers()

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is False, "No offers = no Amazon"
    assert result["amazon_buybox"] is False, "No offers = no Buy Box"


def test_malformed_keepa_data():
    """Test: Malformed/invalid Keepa data structure."""
    keepa_data = {
        "asin": "TEST123",
        "offers": "invalid_not_a_list",  # Wrong type
    }

    result = check_amazon_presence(keepa_data)

    # Should not crash, return safe defaults
    assert result["amazon_on_listing"] is False
    assert result["amazon_buybox"] is False


def test_missing_asin():
    """Test: Missing ASIN field (should still work)."""
    keepa_data = {
        # No asin field
        "offers": [
            {"sellerId": "ATVPDKIKX0DER", "isAmazon": True}
        ]
    }

    result = check_amazon_presence(keepa_data)

    # Should still detect Amazon
    assert result["amazon_on_listing"] is True


def test_offers_missing_is_amazon_field():
    """Test: Offers missing isAmazon boolean field."""
    keepa_data = {
        "asin": "TEST123",
        "offers": [
            {"sellerId": "ATVPDKIKX0DER"},  # Missing isAmazon
            {"sellerId": "A1QUAC68EAM09F", "isAmazon": False}
        ]
    }

    result = check_amazon_presence(keepa_data)

    # Without isAmazon=True, cannot detect Amazon
    assert result["amazon_on_listing"] is False


def test_buybox_history_fallback():
    """Test: Buy Box detection via liveOffersOrder when buyBoxSellerIdHistory unavailable."""
    keepa_data = {
        "asin": "B0088PUEPK",
        "offers": [
            {"sellerId": "ATVPDKIKX0DER", "isAmazon": True},  # Index 0
            {"sellerId": "A1QUAC68EAM09F", "isAmazon": False}  # Index 1
        ],
        # No buyBoxSellerIdHistory
        "liveOffersOrder": [0, 1]  # Amazon is first offer (Buy Box winner typically)
    }

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Amazon detected"
    assert result["amazon_buybox"] is True, "Amazon is first in liveOffersOrder = Buy Box"


def test_empty_buybox_history():
    """Test: Empty Buy Box history array."""
    keepa_data = {
        "asin": "B0088PUEPK",
        "offers": [
            {"sellerId": "ATVPDKIKX0DER", "isAmazon": True}
        ],
        "buyBoxSellerIdHistory": [],  # Empty
        "liveOffersOrder": [0]
    }

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True
    # Falls back to liveOffersOrder
    assert result["amazon_buybox"] is True


# ============================================================================
# Tests - Real-World Scenarios
# ============================================================================

def test_amazon_warehouse_deals():
    """Test: Amazon Warehouse Deals (isAmazon should be False per Keepa docs)."""
    keepa_data = {
        "asin": "B0088PUEPK",
        "offers": [
            {
                "sellerId": "A2L77EE7U53NWQ",  # Amazon Warehouse seller ID
                "isAmazon": False,  # Per Keepa: "Warehouse Deals not considered Amazon"
                "isWarehouseDeal": True,
                "isFBA": False
            }
        ]
    }

    result = check_amazon_presence(keepa_data)

    # Should NOT detect Amazon (Warehouse Deals excluded)
    assert result["amazon_on_listing"] is False, "Warehouse Deals != Amazon"
    assert result["amazon_buybox"] is False


def test_multiple_amazon_offers():
    """Test: Multiple Amazon offers (edge case, but possible)."""
    keepa_data = {
        "asin": "B0088PUEPK",
        "offers": [
            {"sellerId": "ATVPDKIKX0DER", "isAmazon": True, "condition": 0},  # New
            {"sellerId": "ATVPDKIKX0DER", "isAmazon": True, "condition": 1},  # Used
        ],
        "liveOffersOrder": [0, 1]
    }

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Amazon detected (multiple offers)"
    assert result["amazon_buybox"] is True, "Amazon has Buy Box"


# ============================================================================
# Performance / Edge Cases
# ============================================================================

def test_large_offers_array():
    """Test: Product with many offers (100+)."""
    offers = []
    for i in range(100):
        offers.append({
            "sellerId": f"A{i:013d}",
            "isAmazon": False,
            "isFBA": True
        })

    # Add Amazon as last offer
    offers.append({
        "sellerId": "ATVPDKIKX0DER",
        "isAmazon": True
    })

    keepa_data = {
        "asin": "B0088PUEPK",
        "offers": offers
    }

    result = check_amazon_presence(keepa_data)

    assert result["amazon_on_listing"] is True, "Should find Amazon in large list"


def test_none_keepa_data():
    """Test: None as input (extreme edge case)."""
    try:
        result = check_amazon_presence(None)
        # Should not crash
        assert result["amazon_on_listing"] is False
        assert result["amazon_buybox"] is False
    except Exception:
        pytest.fail("Should handle None input gracefully")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
