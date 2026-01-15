"""Unit tests for Amazon URL helpers."""

import pytest


class TestAmazonURLHelpers:
    """Test Amazon URL generation functions."""

    def test_seller_central_url_us(self):
        """Generate correct Seller Central URL for US marketplace."""
        from app.utils.amazon_urls import get_seller_central_restriction_url

        url = get_seller_central_restriction_url('B08N5WRWNW', domain_id=1)

        assert url == 'https://sellercentral.amazon.com/product-search/search?q=B08N5WRWNW'

    def test_seller_central_url_ca(self):
        """Generate correct Seller Central URL for Canada marketplace."""
        from app.utils.amazon_urls import get_seller_central_restriction_url

        url = get_seller_central_restriction_url('B08N5WRWNW', domain_id=6)

        assert url == 'https://sellercentral.amazon.ca/product-search/search?q=B08N5WRWNW'

    def test_amazon_product_url_us(self):
        """Generate correct Amazon product page URL."""
        from app.utils.amazon_urls import get_amazon_product_url

        url = get_amazon_product_url('B08N5WRWNW', domain_id=1)

        assert url == 'https://www.amazon.com/dp/B08N5WRWNW'

    def test_default_domain_is_us(self):
        """Default domain should be US."""
        from app.utils.amazon_urls import get_seller_central_restriction_url

        url = get_seller_central_restriction_url('TEST123')

        assert 'sellercentral.amazon.com' in url
