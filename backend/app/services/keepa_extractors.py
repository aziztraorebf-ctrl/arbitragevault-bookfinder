"""
Keepa Data Extractors - Facade Module
======================================
Re-exports all Keepa extractors from specialized sub-modules.
Maintains backward compatibility while applying Single Responsibility Principle.

This module serves as a facade for:
- keepa_price_extractors.py: Price and historical data extraction
- keepa_bsr_extractors.py: BSR (Best Seller Rank) extraction and validation
- keepa_timestamp_extractors.py: Data freshness timestamp extraction

MIGRATION NOTE:
This file was refactored from a 606 LOC monolithic module into separate concerns.
All previous imports continue to work via re-exports below.
"""

# Re-export price and data extractors
from app.services.keepa_price_extractors import KeepaRawParser

# Re-export BSR extractors
from app.services.keepa_bsr_extractors import KeepaBSRExtractor

# Re-export timestamp extractors
from app.services.keepa_timestamp_extractors import KeepaTimestampExtractor


# Maintain backward compatibility - all classes available at package level
__all__ = [
    'KeepaRawParser',
    'KeepaBSRExtractor',
    'KeepaTimestampExtractor'
]
