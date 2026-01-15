"""Tests for URL generation in unified_analysis.

TDD: Tests for amazon_url and seller_central_url generation
in build_unified_product_v2 function.
"""

import pytest


def test_build_unified_product_v2_generates_amazon_url():
    """Test that build_unified_product_v2 generates amazon_url."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00TEST123',
        'title': 'Test Product',
        'domainId': 1,  # US
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    assert 'amazon_url' in result, "amazon_url field must be present in response"
    assert result['amazon_url'] == 'https://www.amazon.com/dp/B00TEST123'


def test_build_unified_product_v2_generates_seller_central_url():
    """Test that build_unified_product_v2 generates seller_central_url."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00TEST456',
        'title': 'Test Product 2',
        'domainId': 1,  # US
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    assert 'seller_central_url' in result, "seller_central_url field must be present in response"
    assert result['seller_central_url'] == 'https://sellercentral.amazon.com/product-search/search?q=B00TEST456'


def test_build_unified_product_v2_urls_for_canada():
    """Test URL generation for Canadian marketplace (domainId=6)."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00CANADA1',
        'title': 'Canadian Product',
        'domainId': 6,  # Canada
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    assert result['amazon_url'] == 'https://www.amazon.ca/dp/B00CANADA1'
    assert result['seller_central_url'] == 'https://sellercentral.amazon.ca/product-search/search?q=B00CANADA1'


def test_build_unified_product_v2_urls_for_uk():
    """Test URL generation for UK marketplace (domainId=2)."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00UKTEST1',
        'title': 'UK Product',
        'domainId': 2,  # UK
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    assert result['amazon_url'] == 'https://www.amazon.co.uk/dp/B00UKTEST1'
    assert result['seller_central_url'] == 'https://sellercentral.amazon.co.uk/product-search/search?q=B00UKTEST1'


def test_build_unified_product_v2_urls_default_to_us_for_unknown_domain():
    """Test URL generation defaults to US when domainId is unknown."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00UNKNOWN1',
        'title': 'Unknown Domain Product',
        'domainId': 999,  # Unknown domain
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    # Should default to US when domain is unknown
    assert result['amazon_url'] == 'https://www.amazon.com/dp/B00UNKNOWN1'
    assert result['seller_central_url'] == 'https://sellercentral.amazon.com/product-search/search?q=B00UNKNOWN1'


def test_build_unified_product_v2_urls_when_domain_missing():
    """Test URL generation defaults to US when domainId is missing."""
    import asyncio
    from app.services.unified_analysis import build_unified_product_v2

    mock_keepa = {
        'asin': 'B00NODOMAIN',
        'title': 'No Domain Product',
        # No domainId field
        'stats': {'current': [None] * 20},
        'offers': []
    }

    mock_config = {
        'roi': {'target_roi_percent': 35},
        'velocity': {'bsr_thresholds': {'excellent': 50000}},
        'default_source_price': 8.0
    }

    result = asyncio.run(build_unified_product_v2(
        raw_keepa=mock_keepa,
        keepa_service=None,
        config=mock_config,
        view_type='analyse_manuelle',
        compute_score=False
    ))

    # Should default to US (domainId=1) when missing
    assert result['amazon_url'] == 'https://www.amazon.com/dp/B00NODOMAIN'
    assert result['seller_central_url'] == 'https://sellercentral.amazon.com/product-search/search?q=B00NODOMAIN'
