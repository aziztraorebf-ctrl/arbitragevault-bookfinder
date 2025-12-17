# Phase 7 Audit - AutoSourcing Competition Filtering

**Date**: 2025-12-17
**Status**: PROBLEM IDENTIFIED - FIX REQUIRED
**Severity**: HIGH - Same issue as Phase 6

## Executive Summary

AutoSourcing has the **same competition filtering problem** that Phase 6 Niche Discovery had:
- Products returned have **unknown competition** (FBA=None, Amazon=None)
- The `max_fba_sellers` parameter is **not passed** to `discover_products()`
- Post-filtering works but **competition data is not extracted** to picks

## Root Cause Analysis

### 1. Missing Parameter in AutoSourcing Call

**File**: `backend/app/services/autosourcing_service.py:276-284`

```python
# CURRENT (BROKEN)
discovered_asins = await self.product_finder.discover_products(
    domain=1,
    category=category_id,
    bsr_min=bsr_min,
    bsr_max=bsr_max,
    price_min=price_min,
    price_max=price_max,
    max_results=max_results
    # MISSING: max_fba_sellers=X
    # MISSING: exclude_amazon_seller=True (uses default, OK)
)
```

**Method Signature** (`keepa_product_finder.py:143-154`):
```python
async def discover_products(
    ...
    max_fba_sellers: Optional[int] = None,  # <-- Defaults to None = NO LIMIT
    exclude_amazon_seller: bool = True,     # <-- Default OK
)
```

### 2. Competition Data Not Extracted to Picks

Even when products pass filtering, the picks don't include:
- `fba_seller_count`: Always None
- `amazon_on_listing`: Always None (even though checked internally)

The data exists in Keepa response but isn't persisted to `AutoSourcingPick`.

### 3. Production API Test Results

**Test 1 - Normal filters**: 0 ASINs discovered, 0 picks
**Test 2 - Wide filters**: 1 pick (B0DJQVYV99), FBA=None, Amazon=None

Logs showed:
```
Keepa API error: Client error '400 Bad Request' for /query endpoint
```
Fallback to bestsellers worked but without proper competition filtering.

## Fix Required

### Fix 1: Pass Competition Params in AutoSourcing

```python
# FIXED
discovered_asins = await self.product_finder.discover_products(
    domain=1,
    category=category_id,
    bsr_min=bsr_min,
    bsr_max=bsr_max,
    price_min=price_min,
    price_max=price_max,
    max_results=max_results,
    max_fba_sellers=5,  # ADD: Configurable default
    exclude_amazon_seller=True  # ADD: Explicit
)
```

### Fix 2: Add Competition Config to Discovery Config

```python
# In discovery_config schema
{
    "categories": ["books"],
    "bsr_range": [10000, 80000],
    "price_range": [15, 60],
    "max_results": 10,
    "max_fba_sellers": 5,        # NEW
    "exclude_amazon_seller": true # NEW
}
```

### Fix 3: Extract Competition Data to Picks

In `_analyze_products()` or `_score_product()`, add:
```python
pick.fba_seller_count = product.get("offerCountFBA", None)
pick.amazon_on_listing = product.get("availabilityAmazon", -1) >= 0
```

## Validation Plan

1. Add `max_fba_sellers` param to AutoSourcing call
2. Add `exclude_amazon_seller` param (explicit, not default)
3. Extract competition data from Keepa response to picks
4. Add tests for competition filtering in AutoSourcing
5. Deploy and validate with production API

## Files to Modify

1. `backend/app/services/autosourcing_service.py` - Add competition params
2. `backend/app/schemas/autosourcing.py` - Add competition config fields
3. `backend/tests/unit/test_autosourcing_competition.py` - Add tests

## Related Issues

- Phase 6 Niche Discovery had same problem (fixed with post-filter strategy)
- Phase 6.2 documented that API returns 0 when combining filters
- Current workaround: Pre-filter BSR/price, Post-filter Amazon/FBA
