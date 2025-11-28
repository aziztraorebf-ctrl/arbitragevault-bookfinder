"""
Keepa BSR Extractors
====================
Specialized extractors for Amazon Best Seller Rank (BSR) data.
Implements multi-source fallback strategies and quality validation.

Extracted from keepa_extractors.py for Single Responsibility Principle compliance.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import logging

from app.services.keepa_constants import KeepaCSVType
from app.services.keepa_price_extractors import KeepaRawParser


logger = logging.getLogger(__name__)


class KeepaBSRExtractor:
    """
    Business logic layer for BSR extraction and validation.
    Implements fallback strategies and data quality checks.
    """

    @staticmethod
    def extract_current_bsr(raw_data: Dict[str, Any]) -> Tuple[Optional[int], str]:
        """
        Extract current BSR with multiple fallback strategies.

        Priority order (UPDATED based on real Keepa API structure):
        1. salesRanks[categoryId][1] (current BSR value) - source: 'salesRanks'
        2. stats.current[3] (legacy format support) - source: 'current'
        3. Last point from csv[3] history (if recent) - source: 'csv_recent'
        4. stats.avg30[3] (30-day average as fallback) - source: 'avg30'

        Args:
            raw_data: Raw Keepa API response

        Returns:
            Tuple of (BSR value or None, data source identifier)
        """
        asin = raw_data.get("asin", "unknown")

        # Extract stats early for use in fallback strategies
        stats = raw_data.get("stats", {})

        # Strategy 1: NEW - salesRanks format (current Keepa API structure)
        # Format: {"categoryId": [timestamp, bsr_value]}
        sales_ranks = raw_data.get("salesRanks", {})
        sales_rank_reference = raw_data.get("salesRankReference")

        # Try main category first (only if valid reference)
        if sales_rank_reference and sales_rank_reference != -1 and str(sales_rank_reference) in sales_ranks:
            rank_data = sales_ranks[str(sales_rank_reference)]
            if isinstance(rank_data, list) and len(rank_data) >= 2:
                # salesRanks format: [timestamp1, bsr1, timestamp2, bsr2, ...]
                # Last element is the most recent BSR
                bsr = rank_data[-1]  # FIX: Read LAST element (current BSR), not second
                if bsr and bsr != -1:
                    logger.info(f"ASIN {asin}: BSR {bsr} from salesRanks[{sales_rank_reference}]")
                    return int(bsr), "salesRanks"

        # Fallback to any available category
        if sales_ranks:
            for category_id, rank_data in sales_ranks.items():
                if isinstance(rank_data, list) and len(rank_data) >= 2:
                    bsr = rank_data[-1]  # FIX: Read LAST element (current BSR)
                    if bsr and bsr != -1:
                        logger.info(f"ASIN {asin}: BSR {bsr} from salesRanks[{category_id}]")
                        return int(bsr), "salesRanks"

        # Strategy 2: Legacy - current[3] (older Keepa API format)
        # Keep for backward compatibility
        current = raw_data.get("current")
        if not current:  # Fallback ancien format
            current = stats.get("current", [])

        if current and len(current) > KeepaCSVType.SALES:
            bsr = current[KeepaCSVType.SALES]
            if bsr and bsr != -1:
                logger.info(f"ASIN {asin}: BSR {bsr} from current[3] (legacy)")
                return int(bsr), "current"

        # Strategy 3: Fallback to last historical point if recent
        csv_data = raw_data.get("csv", [])
        if csv_data and len(csv_data) > KeepaCSVType.SALES:
            sales_data = csv_data[KeepaCSVType.SALES]
            if sales_data and len(sales_data) >= 2:
                # Check last data point (must be within 24 hours)
                last_timestamp = sales_data[-2] if len(sales_data) >= 2 else None
                last_value = sales_data[-1] if len(sales_data) >= 1 else None

                if last_timestamp and last_value and last_value != -1:
                    last_date = KeepaRawParser._keepa_to_datetime(last_timestamp)
                    age_hours = (datetime.now() - last_date).total_seconds() / 3600

                    # Only accept recent data (within last 24h)
                    if age_hours <= 24:
                        logger.info(f"ASIN {asin}: BSR {last_value} from csv[3] history ({age_hours:.1f}h old)")
                        return int(last_value), "csv_recent"
                    else:
                        logger.debug(f"ASIN {asin}: Historical BSR too old ({age_hours:.1f}h)")

        # Strategy 4: Use 30-day average if available (legacy support)
        avg30 = stats.get("avg30", [])
        if avg30 and len(avg30) > KeepaCSVType.SALES:
            avg_bsr = avg30[KeepaCSVType.SALES]
            if avg_bsr and avg_bsr != -1:
                logger.warning(f"ASIN {asin}: Using 30-day avg BSR {avg_bsr} as fallback")
                return int(avg_bsr), "avg30"

        logger.warning(f"ASIN {asin}: No BSR data available from any source")
        return None, "none"

    @staticmethod
    def validate_bsr_quality(bsr: Optional[int], category: str = "unknown", source: str = "current") -> Dict[str, Any]:
        """
        Validate BSR value and assess data quality.

        Args:
            bsr: BSR value to validate
            category: Product category for context
            source: Data source identifier (salesRanks, current, csv_recent, avg30, none)

        Returns:
            Quality assessment with confidence score (adjusted by source quality)
        """
        if bsr is None or source == "none":
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": "No BSR data available"
            }

        # BSR range validation by category
        category_ranges = {
            "books": (1, 5_000_000),
            "electronics": (1, 1_000_000),
            "toys": (1, 2_000_000),
            "default": (1, 10_000_000)
        }

        min_bsr, max_bsr = category_ranges.get(category.lower(), category_ranges["default"])

        if not (min_bsr <= bsr <= max_bsr):
            return {
                "valid": False,
                "confidence": 0.3,
                "reason": f"BSR {bsr} outside expected range for {category}"
            }

        # Calculate base confidence based on BSR value
        if bsr < 10_000:
            base_confidence = 1.0  # Top sellers have reliable BSR
        elif bsr < 100_000:
            base_confidence = 0.9
        elif bsr < 1_000_000:
            base_confidence = 0.7
        else:
            base_confidence = 0.5  # Lower confidence for high BSR

        # Apply penalty for fallback data sources
        source_multipliers = {
            "salesRanks": 1.0,  # Primary source, no penalty
            "current": 1.0,     # Also current data, no penalty
            "csv_recent": 0.9,  # Recent historical data, slight penalty
            "avg30": 0.8,       # 30-day average, significant penalty
        }

        source_multiplier = source_multipliers.get(source, 0.7)  # Default penalty for unknown sources
        final_confidence = base_confidence * source_multiplier

        return {
            "valid": True,
            "confidence": final_confidence,
            "reason": f"BSR within expected range (source: {source})"
        }


__all__ = ['KeepaBSRExtractor']
