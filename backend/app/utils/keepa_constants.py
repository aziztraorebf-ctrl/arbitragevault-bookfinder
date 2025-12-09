"""
Keepa API Constants - Official Specification
==============================================

Source: Keepa Support Email (October 15, 2025)
Last Updated: 2025-10-15

IMPORTANT: Do NOT modify these constants without official Keepa documentation.
"""

# ═══════════════════════════════════════════════════════════════════════════
# OFFICIAL KEEPA TIME CONVERSION
# ═══════════════════════════════════════════════════════════════════════════

# Official Keepa time offset (in minutes)
# Formula from Keepa Support: unix_seconds = (keepa_time + 21564000) * 60
#
# Example validation (from Keepa Support):
# keepa_time = 7777548
# → (7777548 + 21564000) * 60 = 1760454880 seconds
# → Oct 15 2025 01:48:00 UTC (03:48:00 GMT+0200)
KEEPA_TIME_OFFSET_MINUTES = 21564000

# Keepa null value indicator (used in arrays)
KEEPA_NULL_VALUE = -1

# Keepa price divisor (prices stored as integers, divide by 100 for dollars)
KEEPA_PRICE_DIVISOR = 100


