"""
Amazon URL Helpers
==================
Generates URLs for Amazon Seller Central and marketplace pages.
"""

from typing import Optional

SELLER_CENTRAL_DOMAINS = {
    1: "sellercentral.amazon.com",      # US
    2: "sellercentral.amazon.co.uk",    # UK
    3: "sellercentral.amazon.de",       # DE
    4: "sellercentral.amazon.fr",       # FR
    5: "sellercentral.amazon.co.jp",    # JP
    6: "sellercentral.amazon.ca",       # CA
    7: "sellercentral.amazon.cn",       # CN
    8: "sellercentral.amazon.it",       # IT
    9: "sellercentral.amazon.es",       # ES
    10: "sellercentral.amazon.in",      # IN
    11: "sellercentral.amazon.com.mx",  # MX
}

AMAZON_DOMAINS = {
    1: "amazon.com",
    2: "amazon.co.uk",
    3: "amazon.de",
    4: "amazon.fr",
    5: "amazon.co.jp",
    6: "amazon.ca",
    7: "amazon.cn",
    8: "amazon.it",
    9: "amazon.es",
    10: "amazon.in",
    11: "amazon.com.mx",
}


def get_seller_central_restriction_url(asin: str, domain_id: int = 1) -> str:
    """Generate Seller Central URL to check selling restrictions."""
    domain = SELLER_CENTRAL_DOMAINS.get(domain_id, "sellercentral.amazon.com")
    return f"https://{domain}/product-search/search?q={asin}"


def get_amazon_product_url(asin: str, domain_id: int = 1) -> str:
    """Generate Amazon product page URL."""
    domain = AMAZON_DOMAINS.get(domain_id, "amazon.com")
    return f"https://www.{domain}/dp/{asin}"


__all__ = [
    'get_seller_central_restriction_url',
    'get_amazon_product_url',
    'SELLER_CENTRAL_DOMAINS',
    'AMAZON_DOMAINS',
]
