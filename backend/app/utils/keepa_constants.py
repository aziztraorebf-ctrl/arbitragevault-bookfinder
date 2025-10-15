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


# ═══════════════════════════════════════════════════════════════════════════
# DEPRECATED - DO NOT USE
# ═══════════════════════════════════════════════════════════════════════════

# ❌ LEGACY EPOCH (INCORRECT)
# This was used in previous versions but gave wrong results (dates in 2015)
# Kept here for reference only - DO NOT USE
KEEPA_EPOCH_LEGACY = 971222400  # Oct 21, 2000 00:00:00 GMT - DEPRECATED ❌

# Note: If you see dates in 2015 instead of 2025, you're using the legacy epoch!
# Switch to KEEPA_TIME_OFFSET_MINUTES immediately.
