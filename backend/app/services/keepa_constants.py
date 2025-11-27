"""
Keepa API Constants and Enumerations
=====================================
Official CSV type indices from Keepa Java API.

Source: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
"""

from enum import IntEnum


class KeepaCSVType(IntEnum):
    """
    Official Keepa CSV Type indices from Java API.
    Source: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
    """
    AMAZON = 0              # Amazon price
    NEW = 1                 # Marketplace New price (includes Amazon)
    USED = 2                # Used price
    SALES = 3               # Sales Rank (BSR) - INTEGER not price!
    LISTPRICE = 4           # List price
    COLLECTIBLE = 5         # Collectible price
    REFURBISHED = 6         # Refurbished price
    NEW_FBM_SHIPPING = 7    # FBM with shipping
    LIGHTNING_DEAL = 8      # Lightning deal price
    WAREHOUSE = 9           # Amazon Warehouse
    NEW_FBA = 10            # FBA price (3rd party only)
    COUNT_NEW = 11          # New offer count
    COUNT_USED = 12         # Used offer count
    COUNT_REFURBISHED = 13  # Refurbished count
    COUNT_COLLECTIBLE = 14  # Collectible count
    RATING = 15             # Product rating (0-50, e.g., 45 = 4.5 stars)
    COUNT_REVIEWS = 16      # Review count
    BUY_BOX_SHIPPING = 18   # Buy Box price with shipping


# Keepa condition codes for offers
KEEPA_CONDITION_CODES = {
    1: ('new', 'New'),
    3: ('very_good', 'Used - Very Good'),
    4: ('good', 'Used - Good'),
    5: ('acceptable', 'Used - Acceptable')
}


__all__ = [
    'KeepaCSVType',
    'KEEPA_CONDITION_CODES'
]
