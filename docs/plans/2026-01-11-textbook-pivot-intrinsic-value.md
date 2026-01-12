# ArbitrageVault Textbook Pivot - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform ArbitrageVault from snapshot-based pricing to intrinsic value calculation, with textbook-focused features for year-round stable income.

**Architecture:** Add an Intrinsic Value Service that calculates price corridors from historical Keepa data. Inject this into existing ROI calculations via a configurable `sell_price_source`. Add seasonal detection, evergreen identification, and a reserve calculator for income smoothing.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, NumPy (statistics), React 18, TypeScript, Tailwind CSS

---

## Phase 1: Intrinsic Value Foundation (Days 1-5)

### Task 1: Create Intrinsic Value Service - Core Calculation

**Files:**
- Create: `backend/app/services/intrinsic_value_service.py`
- Test: `backend/tests/services/test_intrinsic_value_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_intrinsic_value_service.py
import pytest
from datetime import datetime, timedelta
from app.services.intrinsic_value_service import calculate_intrinsic_value_corridor


class TestIntrinsicValueCorridor:
    """Tests for intrinsic value calculation."""

    def test_calculate_corridor_with_sufficient_data(self):
        """Test corridor calculation with 30+ data points."""
        # Arrange - simulate 90 days of price history
        base_time = datetime.now()
        price_history = [
            (base_time - timedelta(days=i), 45.0 + (i % 10) - 5)
            for i in range(90)
        ]
        # Prices range from ~40 to ~50, median around 45

        # Act
        result = calculate_intrinsic_value_corridor(price_history)

        # Assert
        assert result["confidence"] == "HIGH"
        assert 40.0 <= result["low"] <= 45.0
        assert 43.0 <= result["median"] <= 47.0
        assert 45.0 <= result["high"] <= 52.0
        assert "volatility" in result
        assert result["data_points"] == 90

    def test_calculate_corridor_insufficient_data(self):
        """Test fallback when less than 10 data points."""
        # Arrange
        price_history = [
            (datetime.now() - timedelta(days=i), 50.0)
            for i in range(5)
        ]

        # Act
        result = calculate_intrinsic_value_corridor(price_history)

        # Assert
        assert result["confidence"] == "INSUFFICIENT_DATA"
        assert result["median"] is None
        assert "reason" in result

    def test_calculate_corridor_filters_outliers(self):
        """Test that P5-P95 filtering removes outliers."""
        # Arrange - normal prices with extreme outliers
        base_time = datetime.now()
        price_history = [
            (base_time - timedelta(days=i), 50.0)
            for i in range(50)
        ]
        # Add outliers
        price_history.append((base_time - timedelta(days=51), 5.0))   # Low outlier
        price_history.append((base_time - timedelta(days=52), 200.0)) # High outlier

        # Act
        result = calculate_intrinsic_value_corridor(price_history)

        # Assert - median should still be around 50, not skewed by outliers
        assert 48.0 <= result["median"] <= 52.0
        assert result["confidence"] == "HIGH"

    def test_calculate_corridor_empty_history(self):
        """Test handling of empty price history."""
        # Act
        result = calculate_intrinsic_value_corridor([])

        # Assert
        assert result["confidence"] == "INSUFFICIENT_DATA"
        assert result["median"] is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.intrinsic_value_service'`

**Step 3: Write minimal implementation**

```python
# backend/app/services/intrinsic_value_service.py
"""
Intrinsic Value Service - Calculate true market value from historical data.

This service addresses the core problem: ArbitrageVault was using snapshot
prices (current buybox) instead of historical median values for ROI calculation.

The intrinsic value corridor represents what buyers ACTUALLY pay over time,
not what the current (potentially anomalous) price shows.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from statistics import median, stdev, mean

logger = logging.getLogger(__name__)


def calculate_intrinsic_value_corridor(
    price_history: List[Tuple[datetime, float]],
    window_days: int = 90,
    min_data_points: int = 10,
) -> Dict[str, Any]:
    """
    Calculate the intrinsic value corridor from price history.

    The corridor represents [P25, Median, P75] of historical prices,
    filtered to remove outliers (P5-P95).

    Args:
        price_history: List of (timestamp, price) tuples
        window_days: How far back to look (default 90 days)
        min_data_points: Minimum points required for HIGH confidence

    Returns:
        {
            "low": float,           # P25 - conservative estimate
            "median": float,        # P50 - best estimate
            "high": float,          # P75 - optimistic estimate
            "confidence": str,      # HIGH, MEDIUM, LOW, INSUFFICIENT_DATA
            "volatility": float,    # Coefficient of variation (std/mean)
            "data_points": int,     # Number of points used
            "window_days": int,     # Analysis window
            "reason": str,          # Explanation (if low confidence)
        }
    """
    if not price_history:
        return _insufficient_data_response("No price history available")

    # Filter to window
    cutoff = datetime.now() - timedelta(days=window_days)
    filtered = [(ts, price) for ts, price in price_history if ts >= cutoff and price > 0]

    if len(filtered) < min_data_points:
        return _insufficient_data_response(
            f"Only {len(filtered)} data points in {window_days}-day window (need {min_data_points})"
        )

    prices = [price for _, price in filtered]

    # Remove outliers (P5-P95)
    prices_sorted = sorted(prices)
    p5_idx = int(len(prices_sorted) * 0.05)
    p95_idx = int(len(prices_sorted) * 0.95)
    filtered_prices = prices_sorted[p5_idx:p95_idx] if p95_idx > p5_idx else prices_sorted

    if len(filtered_prices) < 5:
        filtered_prices = prices_sorted  # Fallback to all if too few after filtering

    # Calculate corridor
    prices_for_percentile = sorted(filtered_prices)
    n = len(prices_for_percentile)

    p25_idx = int(n * 0.25)
    p50_idx = int(n * 0.50)
    p75_idx = int(n * 0.75)

    low = prices_for_percentile[p25_idx]
    median_val = prices_for_percentile[p50_idx]
    high = prices_for_percentile[min(p75_idx, n - 1)]

    # Calculate volatility (coefficient of variation)
    avg = mean(filtered_prices)
    std = stdev(filtered_prices) if len(filtered_prices) > 1 else 0
    volatility = std / avg if avg > 0 else 0

    # Determine confidence
    confidence = _determine_confidence(len(filtered), volatility)

    return {
        "low": round(low, 2),
        "median": round(median_val, 2),
        "high": round(high, 2),
        "confidence": confidence,
        "volatility": round(volatility, 4),
        "data_points": len(filtered),
        "window_days": window_days,
        "reason": None,
    }


def _determine_confidence(data_points: int, volatility: float) -> str:
    """Determine confidence level based on data quality."""
    if data_points >= 30 and volatility < 0.20:
        return "HIGH"
    elif data_points >= 15 and volatility < 0.35:
        return "MEDIUM"
    elif data_points >= 10:
        return "LOW"
    else:
        return "INSUFFICIENT_DATA"


def _insufficient_data_response(reason: str) -> Dict[str, Any]:
    """Return a standardized response for insufficient data."""
    return {
        "low": None,
        "median": None,
        "high": None,
        "confidence": "INSUFFICIENT_DATA",
        "volatility": None,
        "data_points": 0,
        "window_days": None,
        "reason": reason,
    }


def get_sell_price_for_strategy(
    parsed_data: Dict[str, Any],
    strategy: str = "balanced",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get the appropriate sell price based on strategy.

    This is the KEY FUNCTION that replaces snapshot pricing with intrinsic value.

    Args:
        parsed_data: Output from parse_keepa_product_unified()
        strategy: "textbook", "velocity", or "balanced"
        config: Optional override config

    Returns:
        {
            "sell_price": float,
            "source": str,          # "intrinsic_median", "current_price_fallback"
            "confidence": str,
            "intrinsic_corridor": dict,  # Full corridor if available
            "warning": str,         # If using fallback
        }
    """
    # Get price history from parsed data
    price_history = parsed_data.get("price_history", [])
    current_price = parsed_data.get("current_price") or parsed_data.get("current_buybox_price")

    # Strategy-specific window
    window_days = 365 if strategy == "textbook" else 90

    # Calculate intrinsic value
    corridor = calculate_intrinsic_value_corridor(price_history, window_days=window_days)

    if corridor["confidence"] == "INSUFFICIENT_DATA":
        # Fallback to current price
        return {
            "sell_price": current_price,
            "source": "current_price_fallback",
            "confidence": "LOW",
            "intrinsic_corridor": corridor,
            "warning": corridor.get("reason", "Insufficient historical data"),
        }

    # Use median as sell price
    return {
        "sell_price": corridor["median"],
        "source": "intrinsic_median",
        "confidence": corridor["confidence"],
        "intrinsic_corridor": corridor,
        "warning": None,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/intrinsic_value_service.py backend/tests/services/test_intrinsic_value_service.py
git commit -m "feat(intrinsic-value): add core intrinsic value corridor calculation

- Calculate [P25, Median, P75] from historical prices
- Filter outliers using P5-P95 range
- Confidence scoring based on data points and volatility
- Fallback to current price when insufficient data

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Add Confidence Score Tests

**Files:**
- Modify: `backend/tests/services/test_intrinsic_value_service.py`

**Step 1: Write additional failing tests**

```python
# Add to backend/tests/services/test_intrinsic_value_service.py

class TestConfidenceScoring:
    """Tests for confidence level determination."""

    def test_high_confidence_stable_prices(self):
        """High confidence with 30+ points and low volatility."""
        base_time = datetime.now()
        # Stable prices around $50 with low variance
        price_history = [
            (base_time - timedelta(days=i), 50.0 + (i % 3) - 1)
            for i in range(60)
        ]

        result = calculate_intrinsic_value_corridor(price_history)

        assert result["confidence"] == "HIGH"
        assert result["volatility"] < 0.20

    def test_medium_confidence_moderate_volatility(self):
        """Medium confidence with moderate data and volatility."""
        base_time = datetime.now()
        # More volatile prices
        price_history = [
            (base_time - timedelta(days=i), 50.0 + (i % 20) - 10)
            for i in range(20)
        ]

        result = calculate_intrinsic_value_corridor(price_history)

        assert result["confidence"] in ["MEDIUM", "LOW"]

    def test_low_confidence_high_volatility(self):
        """Low confidence when prices are highly volatile."""
        base_time = datetime.now()
        # Very volatile - prices swing wildly
        import random
        random.seed(42)
        price_history = [
            (base_time - timedelta(days=i), random.uniform(20, 80))
            for i in range(15)
        ]

        result = calculate_intrinsic_value_corridor(price_history)

        assert result["confidence"] in ["LOW", "MEDIUM"]
        assert result["volatility"] > 0.20


class TestGetSellPriceForStrategy:
    """Tests for strategy-based sell price selection."""

    def test_textbook_strategy_uses_12_month_window(self):
        """Textbook strategy should use 365-day window."""
        base_time = datetime.now()
        # Data spanning 400 days
        price_history = [
            (base_time - timedelta(days=i), 60.0)
            for i in range(400)
        ]

        parsed_data = {
            "price_history": price_history,
            "current_price": 45.0,
        }

        result = get_sell_price_for_strategy(parsed_data, strategy="textbook")

        assert result["source"] == "intrinsic_median"
        assert result["sell_price"] == 60.0
        assert result["intrinsic_corridor"]["window_days"] == 365

    def test_velocity_strategy_uses_90_day_window(self):
        """Velocity strategy should use 90-day window."""
        base_time = datetime.now()
        price_history = [
            (base_time - timedelta(days=i), 30.0)
            for i in range(100)
        ]

        parsed_data = {
            "price_history": price_history,
            "current_price": 25.0,
        }

        result = get_sell_price_for_strategy(parsed_data, strategy="velocity")

        assert result["intrinsic_corridor"]["window_days"] == 90

    def test_fallback_to_current_price_when_no_history(self):
        """Should fallback to current price with warning."""
        parsed_data = {
            "price_history": [],
            "current_price": 35.0,
        }

        result = get_sell_price_for_strategy(parsed_data, strategy="balanced")

        assert result["source"] == "current_price_fallback"
        assert result["sell_price"] == 35.0
        assert result["warning"] is not None
        assert result["confidence"] == "LOW"
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py::TestConfidenceScoring -v
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py::TestGetSellPriceForStrategy -v
```

Expected: Tests should PASS (implementation already handles these cases)

**Step 3: Verify and commit**

```bash
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py -v
git add backend/tests/services/test_intrinsic_value_service.py
git commit -m "test(intrinsic-value): add confidence scoring and strategy tests

- Test HIGH/MEDIUM/LOW confidence thresholds
- Test textbook vs velocity window selection
- Test fallback behavior when insufficient data

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Integrate Intrinsic Value into Pricing Service

**Files:**
- Modify: `backend/app/services/pricing_service.py`
- Test: `backend/tests/services/test_pricing_intrinsic_integration.py`

**Step 1: Write the failing integration test**

```python
# backend/tests/services/test_pricing_intrinsic_integration.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic


class TestPricingWithIntrinsicValue:
    """Tests for pricing metrics using intrinsic value."""

    @pytest.fixture
    def sample_parsed_data_with_history(self):
        """Parsed Keepa data with price history."""
        base_time = datetime.now()
        return {
            "asin": "B08XYZ123",
            "current_price": 35.0,
            "current_buybox_price": 35.0,
            "current_fba_price": 28.0,
            "offers_by_condition": {
                "good": {
                    "minimum_price": 30.0,
                    "seller_count": 5,
                    "fba_count": 2,
                }
            },
            "price_history": [
                (base_time - timedelta(days=i), 50.0 + (i % 5) - 2)
                for i in range(90)
            ],
        }

    def test_uses_intrinsic_value_when_available(self, sample_parsed_data_with_history):
        """ROI should be calculated using intrinsic median, not current price."""
        source_price = 20.0
        config = {"amazon_fee_pct": 0.15, "shipping_cost": 3.0}

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=sample_parsed_data_with_history,
            source_price=source_price,
            config=config,
            strategy="textbook",
        )

        # Intrinsic median is ~50, not current price of 35
        assert result["intrinsic_value"]["median"] is not None
        assert result["intrinsic_value"]["median"] > 45.0
        assert result["sell_price_used"] == result["intrinsic_value"]["median"]
        # ROI should be based on ~50, not 35
        # ROI = (50 - fees - 20) / 20
        assert result["roi_pct"] > 0.80  # Should be > 80% with $50 sell price

    def test_fallback_to_current_price(self):
        """Should use current price when no history available."""
        parsed_data = {
            "asin": "B08XYZ123",
            "current_price": 35.0,
            "current_buybox_price": 35.0,
            "offers_by_condition": {},
            "price_history": [],
        }
        source_price = 20.0
        config = {"amazon_fee_pct": 0.15, "shipping_cost": 3.0}

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data,
            source_price=source_price,
            config=config,
            strategy="balanced",
        )

        assert result["sell_price_used"] == 35.0
        assert result["intrinsic_value"]["confidence"] == "INSUFFICIENT_DATA"
        assert result["pricing_warning"] is not None

    def test_includes_confidence_in_output(self, sample_parsed_data_with_history):
        """Output should include confidence score."""
        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=sample_parsed_data_with_history,
            source_price=20.0,
            config={},
            strategy="textbook",
        )

        assert "intrinsic_value" in result
        assert "confidence" in result["intrinsic_value"]
        assert result["intrinsic_value"]["confidence"] in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"]
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_pricing_intrinsic_integration.py -v
```

Expected: FAIL with `ImportError: cannot import name 'calculate_pricing_metrics_with_intrinsic'`

**Step 3: Implement the integration**

```python
# Add to backend/app/services/pricing_service.py (at the end of file)

from app.services.intrinsic_value_service import (
    calculate_intrinsic_value_corridor,
    get_sell_price_for_strategy,
)


def calculate_pricing_metrics_with_intrinsic(
    parsed_data: Dict[str, Any],
    source_price: float,
    config: Dict[str, Any],
    strategy: str = "balanced",
) -> Dict[str, Any]:
    """
    Calculate pricing metrics using intrinsic value instead of snapshot price.

    This is the UPGRADED version of calculate_pricing_metrics_unified that
    uses historical price data to determine the true sell price.

    Args:
        parsed_data: Output from parse_keepa_product_unified()
        source_price: Acquisition cost in dollars
        config: Fee configuration
        strategy: "textbook", "velocity", or "balanced"

    Returns:
        Standard pricing metrics dict with additional intrinsic_value fields
    """
    # Get intrinsic-based sell price
    sell_price_result = get_sell_price_for_strategy(parsed_data, strategy, config)
    sell_price = sell_price_result["sell_price"]

    # Extract config with defaults
    amazon_fee_pct = config.get("amazon_fee_pct", 0.15)
    shipping_cost = config.get("shipping_cost", 3.0)

    # Calculate fees
    amazon_fees = sell_price * amazon_fee_pct if sell_price else 0
    net_revenue = sell_price - amazon_fees - shipping_cost if sell_price else 0

    # Calculate ROI
    roi_value = net_revenue - source_price
    roi_pct = (roi_value / source_price) if source_price > 0 else 0

    # Calculate profit margin
    profit_margin = (roi_value / sell_price) if sell_price and sell_price > 0 else 0

    return {
        # Core metrics
        "sell_price_used": sell_price,
        "source_price": source_price,
        "amazon_fees": round(amazon_fees, 2),
        "shipping_cost": shipping_cost,
        "net_revenue": round(net_revenue, 2),
        "roi_value": round(roi_value, 2),
        "roi_pct": round(roi_pct, 4),  # As decimal (0.80 = 80%)
        "profit_margin": round(profit_margin, 4),

        # Intrinsic value data
        "intrinsic_value": sell_price_result["intrinsic_corridor"],
        "pricing_source": sell_price_result["source"],
        "pricing_confidence": sell_price_result["confidence"],
        "pricing_warning": sell_price_result["warning"],

        # Comparison with current price
        "current_price": parsed_data.get("current_price"),
        "current_vs_intrinsic_pct": _calculate_price_gap(
            parsed_data.get("current_price"),
            sell_price_result["intrinsic_corridor"].get("median"),
        ),

        # Strategy used
        "strategy": strategy,
    }


def _calculate_price_gap(current: float, intrinsic: float) -> Optional[float]:
    """Calculate percentage gap between current and intrinsic price."""
    if not current or not intrinsic or intrinsic == 0:
        return None
    return round((intrinsic - current) / intrinsic, 4)
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_pricing_intrinsic_integration.py -v
```

Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/pricing_service.py backend/tests/services/test_pricing_intrinsic_integration.py
git commit -m "feat(pricing): integrate intrinsic value into pricing calculations

- Add calculate_pricing_metrics_with_intrinsic() function
- Use historical median instead of snapshot price
- Include confidence scoring in output
- Fallback gracefully when insufficient data
- Add current vs intrinsic gap calculation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Update Unified Analysis to Use Intrinsic Pricing

**Files:**
- Modify: `backend/app/services/unified_analysis.py`
- Test: `backend/tests/services/test_unified_analysis_intrinsic.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_unified_analysis_intrinsic.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.unified_analysis import build_unified_product_v2


class TestUnifiedAnalysisWithIntrinsic:
    """Tests for unified analysis using intrinsic value."""

    @pytest.fixture
    def mock_keepa_response_with_history(self):
        """Mock Keepa response with price history."""
        base_time = datetime.now()
        return {
            "asin": "0134685991",
            "title": "Effective Java (3rd Edition)",
            "current_bsr": 15000,
            "current_price": 35.0,
            "current_buybox_price": 35.0,
            "current_fba_price": 28.0,
            "offers_by_condition": {
                "good": {"minimum_price": 30.0, "seller_count": 5, "fba_count": 2}
            },
            "price_history": [
                (base_time - timedelta(days=i), 55.0 + (i % 5) - 2)
                for i in range(120)
            ],
            "bsr_history": [
                (base_time - timedelta(days=i), 15000 + (i * 100))
                for i in range(120)
            ],
            "sales_drops_30": 25,
        }

    @pytest.mark.asyncio
    async def test_unified_product_includes_intrinsic_value(self, mock_keepa_response_with_history):
        """Unified product should include intrinsic value data."""
        mock_service = AsyncMock()
        config = {"strategy": "textbook"}

        with patch("app.services.unified_analysis.parse_keepa_product_unified") as mock_parse:
            mock_parse.return_value = mock_keepa_response_with_history

            result = await build_unified_product_v2(
                raw_keepa={"products": [mock_keepa_response_with_history]},
                keepa_service=mock_service,
                config=config,
                view_type="analyse_manuelle",
                strategy="textbook",
            )

            # Should have intrinsic value data
            assert "intrinsic_value" in result
            assert result["intrinsic_value"]["median"] is not None
            assert result["intrinsic_value"]["confidence"] in ["HIGH", "MEDIUM", "LOW"]

    @pytest.mark.asyncio
    async def test_roi_uses_intrinsic_not_current(self, mock_keepa_response_with_history):
        """ROI calculation should use intrinsic median."""
        mock_service = AsyncMock()
        config = {"strategy": "textbook", "source_price": 20.0}

        with patch("app.services.unified_analysis.parse_keepa_product_unified") as mock_parse:
            mock_parse.return_value = mock_keepa_response_with_history

            result = await build_unified_product_v2(
                raw_keepa={"products": [mock_keepa_response_with_history]},
                keepa_service=mock_service,
                config=config,
                view_type="analyse_manuelle",
                strategy="textbook",
            )

            # Intrinsic median is ~55, current is 35
            # ROI with intrinsic should be higher
            assert result["intrinsic_roi_pct"] > result.get("legacy_roi_pct", 0)
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_unified_analysis_intrinsic.py -v
```

Expected: FAIL (function signature or return value mismatch)

**Step 3: Modify unified_analysis.py**

Add at the top of the file:
```python
# backend/app/services/unified_analysis.py - Add import
from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic
```

Modify the `build_unified_product_v2` function to include intrinsic value:

```python
# In build_unified_product_v2, after parsing and before return, add:

    # Calculate intrinsic value metrics
    source_price = config.get("source_price", parsed.get("current_fba_price", 0))
    intrinsic_metrics = calculate_pricing_metrics_with_intrinsic(
        parsed_data=parsed,
        source_price=source_price,
        config=config,
        strategy=strategy or "balanced",
    )

    # Add intrinsic value data to result
    result["intrinsic_value"] = intrinsic_metrics["intrinsic_value"]
    result["intrinsic_roi_pct"] = intrinsic_metrics["roi_pct"]
    result["intrinsic_sell_price"] = intrinsic_metrics["sell_price_used"]
    result["pricing_confidence"] = intrinsic_metrics["pricing_confidence"]
    result["pricing_source"] = intrinsic_metrics["pricing_source"]
    result["current_vs_intrinsic_pct"] = intrinsic_metrics["current_vs_intrinsic_pct"]

    # Keep legacy ROI for comparison (based on current price)
    result["legacy_roi_pct"] = _calculate_legacy_roi(parsed, source_price, config)
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_unified_analysis_intrinsic.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/unified_analysis.py backend/tests/services/test_unified_analysis_intrinsic.py
git commit -m "feat(unified-analysis): integrate intrinsic value into product output

- Add intrinsic_value, intrinsic_roi_pct to unified product
- Keep legacy_roi_pct for comparison
- Include pricing_confidence and pricing_source
- Add current_vs_intrinsic gap percentage

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Update Business Rules Configuration

**Files:**
- Modify: `backend/config/business_rules.json`
- Test: Manual verification

**Step 1: Update business_rules.json**

```json
{
  "strategies": {
    "textbook": {
      "description": "Textbook arbitrage - high margin, seasonal, intrinsic value based",
      "roi_min": 50.0,
      "velocity_min": 20.0,
      "stability_min": 60.0,
      "min_sell_price": 30.0,
      "min_intrinsic_value": 35.0,
      "max_bsr": 300000,
      "holding_period_days": [45, 120],
      "buy_price_source": "current_fba_price",
      "sell_price_source": "intrinsic_median",
      "use_intrinsic_value": true,
      "intrinsic_window_days": 365,
      "fees_estimate_pct": 22.0,
      "weights": {
        "roi": 0.6,
        "velocity": 0.2,
        "stability": 0.2
      },
      "enabled": true,
      "priority": 1,
      "development_focus": true
    },
    "velocity": {
      "description": "Fast rotation books - moderate margin, quick turnover",
      "roi_min": 40.0,
      "velocity_min": 60.0,
      "stability_min": 40.0,
      "min_sell_price": 15.0,
      "min_intrinsic_value": 25.0,
      "max_bsr": 100000,
      "holding_period_days": [7, 30],
      "buy_price_source": "current_fba_price",
      "sell_price_source": "intrinsic_median",
      "use_intrinsic_value": true,
      "intrinsic_window_days": 90,
      "fees_estimate_pct": 22.0,
      "weights": {
        "roi": 0.3,
        "velocity": 0.5,
        "stability": 0.2
      },
      "enabled": true,
      "priority": 2,
      "development_focus": false
    },
    "balanced": {
      "description": "Balanced approach - moderate everything",
      "roi_min": 35.0,
      "velocity_min": 40.0,
      "stability_min": 50.0,
      "min_sell_price": 20.0,
      "min_intrinsic_value": 25.0,
      "max_bsr": 150000,
      "holding_period_days": [14, 60],
      "buy_price_source": "current_fba_price",
      "sell_price_source": "intrinsic_median",
      "use_intrinsic_value": true,
      "intrinsic_window_days": 90,
      "fees_estimate_pct": 22.0,
      "weights": {
        "roi": 0.4,
        "velocity": 0.35,
        "stability": 0.25
      },
      "enabled": true,
      "priority": 3,
      "development_focus": false
    }
  },
  "feature_flags": {
    "intrinsic_value_enabled": true,
    "intrinsic_value_shadow_mode": false,
    "strategy_profiles_v2": true,
    "seasonal_detection_enabled": false
  },
  "income_smoothing": {
    "reserve_percentage": 25,
    "target_monthly_income": 2000,
    "evergreen_portfolio_percentage": 30
  }
}
```

**Step 2: Verify configuration loads correctly**

```bash
cd backend && python -c "import json; print(json.load(open('config/business_rules.json'))['strategies']['textbook'])"
```

Expected: Textbook strategy config printed

**Step 3: Commit**

```bash
git add backend/config/business_rules.json
git commit -m "config: update business rules for intrinsic value pricing

- Enable intrinsic_value for all strategies
- Set textbook as priority 1 with 365-day window
- Adjust ROI minimums: textbook 50%, velocity 40%, balanced 35%
- Add min_intrinsic_value thresholds
- Add income_smoothing configuration
- Add feature_flags for gradual rollout

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Seasonal Detection & Textbook Features (Days 6-10)

### Task 6: Create Seasonal Pattern Detector

**Files:**
- Create: `backend/app/services/seasonal_detector_service.py`
- Test: `backend/tests/services/test_seasonal_detector.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_seasonal_detector.py
import pytest
from datetime import datetime, timedelta
from app.services.seasonal_detector_service import (
    detect_seasonal_pattern,
    SeasonalPattern,
    get_days_until_peak,
)


class TestSeasonalPatternDetection:
    """Tests for seasonal pattern detection."""

    @pytest.fixture
    def college_fall_price_history(self):
        """Price history showing college fall pattern (peak in Aug-Sept)."""
        history = []
        base = datetime(2024, 1, 1)

        for month in range(1, 13):
            for day in range(1, 29, 7):  # Weekly data points
                date = datetime(2024, month, day)
                # Peak in Aug-Sept
                if month in [8, 9]:
                    price = 80.0 + (day % 10)
                elif month in [7, 10]:
                    price = 60.0 + (day % 10)
                else:
                    price = 40.0 + (day % 10)
                history.append((date, price))

        return history

    @pytest.fixture
    def college_spring_price_history(self):
        """Price history showing college spring pattern (peak in Dec-Jan)."""
        history = []

        for year in [2023, 2024]:
            for month in range(1, 13):
                for day in range(1, 29, 7):
                    date = datetime(year, month, day)
                    # Peak in Dec-Jan
                    if month in [12, 1]:
                        price = 75.0 + (day % 10)
                    elif month in [11, 2]:
                        price = 55.0 + (day % 10)
                    else:
                        price = 35.0 + (day % 10)
                    history.append((date, price))

        return history

    def test_detect_college_fall_pattern(self, college_fall_price_history):
        """Should detect college fall seasonal pattern."""
        result = detect_seasonal_pattern(college_fall_price_history)

        assert result.pattern_type == "COLLEGE_FALL"
        assert result.peak_months == [8, 9]
        assert result.confidence >= 0.7

    def test_detect_college_spring_pattern(self, college_spring_price_history):
        """Should detect college spring seasonal pattern."""
        result = detect_seasonal_pattern(college_spring_price_history)

        assert result.pattern_type == "COLLEGE_SPRING"
        assert 12 in result.peak_months or 1 in result.peak_months
        assert result.confidence >= 0.6

    def test_get_days_until_peak_college_fall(self):
        """Should calculate days until college fall peak."""
        # Test from June 1st
        test_date = datetime(2024, 6, 1)
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            confidence=0.8,
        )

        days = get_days_until_peak(pattern, reference_date=test_date)

        # August 15 is ~75 days from June 1
        assert 60 <= days <= 90

    def test_no_pattern_detected_for_stable_prices(self):
        """Should return STABLE pattern for non-seasonal prices."""
        base = datetime(2024, 1, 1)
        # Stable prices all year
        history = [
            (base + timedelta(days=i * 7), 50.0 + (i % 5) - 2)
            for i in range(52)
        ]

        result = detect_seasonal_pattern(history)

        assert result.pattern_type == "STABLE"
        assert result.confidence >= 0.5
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_seasonal_detector.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Implement seasonal detector**

```python
# backend/app/services/seasonal_detector_service.py
"""
Seasonal Pattern Detector - Identify textbook seasonal patterns.

Textbook seasons:
- COLLEGE_FALL: Peak Aug-Sept (fall semester)
- COLLEGE_SPRING: Peak Dec-Jan (spring semester)
- HIGH_SCHOOL: Peak May-June (end of school year)
- EVERGREEN: No clear seasonal pattern (certification, professional)
- STABLE: Consistent pricing year-round
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from statistics import mean, stdev

logger = logging.getLogger(__name__)


@dataclass
class SeasonalPattern:
    """Detected seasonal pattern for a product."""
    pattern_type: str  # COLLEGE_FALL, COLLEGE_SPRING, HIGH_SCHOOL, EVERGREEN, STABLE
    peak_months: List[int]  # Months with peak prices (1-12)
    trough_months: List[int]  # Months with lowest prices
    confidence: float  # 0.0 to 1.0
    avg_peak_price: Optional[float] = None
    avg_trough_price: Optional[float] = None
    price_swing_pct: Optional[float] = None  # (peak - trough) / trough


# Known seasonal patterns
SEASONAL_PATTERNS = {
    "COLLEGE_FALL": {"peak": [8, 9], "trough": [4, 5, 6]},
    "COLLEGE_SPRING": {"peak": [12, 1], "trough": [6, 7, 8]},
    "HIGH_SCHOOL": {"peak": [5, 6], "trough": [9, 10, 11]},
}


def detect_seasonal_pattern(
    price_history: List[Tuple[datetime, float]],
    min_data_months: int = 6,
) -> SeasonalPattern:
    """
    Detect seasonal pattern from price history.

    Args:
        price_history: List of (timestamp, price) tuples
        min_data_months: Minimum months of data required

    Returns:
        SeasonalPattern with detected pattern type and confidence
    """
    if not price_history or len(price_history) < 20:
        return SeasonalPattern(
            pattern_type="UNKNOWN",
            peak_months=[],
            trough_months=[],
            confidence=0.0,
        )

    # Group prices by month
    monthly_prices = defaultdict(list)
    for ts, price in price_history:
        if price > 0:
            monthly_prices[ts.month].append(price)

    if len(monthly_prices) < min_data_months:
        return SeasonalPattern(
            pattern_type="INSUFFICIENT_DATA",
            peak_months=[],
            trough_months=[],
            confidence=0.0,
        )

    # Calculate monthly averages
    monthly_averages = {
        month: mean(prices)
        for month, prices in monthly_prices.items()
        if prices
    }

    if not monthly_averages:
        return SeasonalPattern(
            pattern_type="UNKNOWN",
            peak_months=[],
            trough_months=[],
            confidence=0.0,
        )

    # Find peak and trough months
    avg_price = mean(monthly_averages.values())
    std_price = stdev(monthly_averages.values()) if len(monthly_averages) > 1 else 0

    # If low variance, it's stable
    cv = std_price / avg_price if avg_price > 0 else 0
    if cv < 0.15:
        return SeasonalPattern(
            pattern_type="STABLE",
            peak_months=[],
            trough_months=[],
            confidence=0.8,
            avg_peak_price=avg_price,
            avg_trough_price=avg_price,
            price_swing_pct=0,
        )

    # Identify peaks (> avg + 0.5 std) and troughs (< avg - 0.5 std)
    peak_months = [m for m, p in monthly_averages.items() if p > avg_price + 0.5 * std_price]
    trough_months = [m for m, p in monthly_averages.items() if p < avg_price - 0.5 * std_price]

    # Match against known patterns
    best_match = None
    best_confidence = 0.0

    for pattern_name, pattern_def in SEASONAL_PATTERNS.items():
        peak_overlap = len(set(peak_months) & set(pattern_def["peak"]))
        trough_overlap = len(set(trough_months) & set(pattern_def["trough"]))

        # Calculate confidence based on overlap
        confidence = (peak_overlap + trough_overlap) / (
            len(pattern_def["peak"]) + len(pattern_def["trough"])
        )

        if confidence > best_confidence:
            best_confidence = confidence
            best_match = pattern_name

    # Calculate price swing
    peak_price = mean([monthly_averages[m] for m in peak_months]) if peak_months else avg_price
    trough_price = mean([monthly_averages[m] for m in trough_months]) if trough_months else avg_price
    price_swing = (peak_price - trough_price) / trough_price if trough_price > 0 else 0

    if best_match and best_confidence >= 0.5:
        return SeasonalPattern(
            pattern_type=best_match,
            peak_months=peak_months,
            trough_months=trough_months,
            confidence=best_confidence,
            avg_peak_price=round(peak_price, 2),
            avg_trough_price=round(trough_price, 2),
            price_swing_pct=round(price_swing, 4),
        )

    # Check if it's evergreen (high prices year-round)
    if avg_price > 30 and cv < 0.25:
        return SeasonalPattern(
            pattern_type="EVERGREEN",
            peak_months=[],
            trough_months=[],
            confidence=0.7,
            avg_peak_price=avg_price,
            avg_trough_price=avg_price,
            price_swing_pct=0,
        )

    return SeasonalPattern(
        pattern_type="IRREGULAR",
        peak_months=peak_months,
        trough_months=trough_months,
        confidence=0.4,
        avg_peak_price=round(peak_price, 2) if peak_months else None,
        avg_trough_price=round(trough_price, 2) if trough_months else None,
        price_swing_pct=round(price_swing, 4) if price_swing else None,
    )


def get_days_until_peak(
    pattern: SeasonalPattern,
    reference_date: Optional[datetime] = None,
) -> Optional[int]:
    """
    Calculate days until the next peak season.

    Args:
        pattern: Detected seasonal pattern
        reference_date: Date to calculate from (default: now)

    Returns:
        Number of days until peak, or None if no pattern
    """
    if not pattern.peak_months:
        return None

    ref = reference_date or datetime.now()
    current_month = ref.month
    current_day = ref.day

    # Find next peak month
    for offset in range(12):
        check_month = ((current_month - 1 + offset) % 12) + 1
        if check_month in pattern.peak_months:
            # Calculate days to middle of that month
            if check_month >= current_month:
                target_year = ref.year
            else:
                target_year = ref.year + 1

            target_date = datetime(target_year, check_month, 15)
            delta = target_date - ref
            return max(0, delta.days)

    return None


def get_optimal_buy_window(pattern: SeasonalPattern) -> Dict[str, Any]:
    """
    Get the optimal buying window for a seasonal pattern.

    Returns:
        {
            "start_month": int,
            "end_month": int,
            "months_before_peak": int,
            "recommendation": str,
        }
    """
    if pattern.pattern_type == "COLLEGE_FALL":
        return {
            "start_month": 3,
            "end_month": 6,
            "months_before_peak": 3,
            "recommendation": "Buy March-June for August-September peak",
        }
    elif pattern.pattern_type == "COLLEGE_SPRING":
        return {
            "start_month": 9,
            "end_month": 11,
            "months_before_peak": 2,
            "recommendation": "Buy September-November for December-January peak",
        }
    elif pattern.pattern_type == "HIGH_SCHOOL":
        return {
            "start_month": 1,
            "end_month": 4,
            "months_before_peak": 2,
            "recommendation": "Buy January-April for May-June peak",
        }
    elif pattern.pattern_type == "EVERGREEN":
        return {
            "start_month": None,
            "end_month": None,
            "months_before_peak": 0,
            "recommendation": "Buy anytime - stable year-round demand",
        }
    else:
        return {
            "start_month": None,
            "end_month": None,
            "months_before_peak": None,
            "recommendation": "No clear seasonal pattern detected",
        }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_seasonal_detector.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/seasonal_detector_service.py backend/tests/services/test_seasonal_detector.py
git commit -m "feat(seasonal): add seasonal pattern detector for textbooks

- Detect COLLEGE_FALL, COLLEGE_SPRING, HIGH_SCHOOL patterns
- Identify EVERGREEN and STABLE books
- Calculate days until peak and optimal buy windows
- Confidence scoring based on pattern match

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Create Evergreen Identifier

**Files:**
- Create: `backend/app/services/evergreen_identifier_service.py`
- Test: `backend/tests/services/test_evergreen_identifier.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_evergreen_identifier.py
import pytest
from datetime import datetime, timedelta
from app.services.evergreen_identifier_service import (
    identify_evergreen,
    EvergreenClassification,
)


class TestEvergreenIdentification:
    """Tests for evergreen book identification."""

    def test_identify_nursing_book_as_evergreen(self):
        """Nursing/medical books should be identified as evergreen."""
        product_data = {
            "title": "Pharmacology for Nurses: A Pathophysiologic Approach",
            "category": "Medical Books",
            "bsr": 25000,
            "avg_price_12m": 65.0,
            "price_volatility": 0.12,
            "sales_per_month": 15,
        }

        result = identify_evergreen(product_data)

        assert result.is_evergreen is True
        assert result.evergreen_type == "PROFESSIONAL_CERTIFICATION"
        assert result.confidence >= 0.7

    def test_identify_programming_book_as_evergreen(self):
        """Core programming books should be identified as evergreen."""
        product_data = {
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "category": "Computer Science",
            "bsr": 5000,
            "avg_price_12m": 35.0,
            "price_volatility": 0.08,
            "sales_per_month": 50,
        }

        result = identify_evergreen(product_data)

        assert result.is_evergreen is True
        assert result.evergreen_type in ["PROFESSIONAL_CERTIFICATION", "CLASSIC"]

    def test_seasonal_textbook_not_evergreen(self):
        """Seasonal textbooks should not be classified as evergreen."""
        product_data = {
            "title": "Introduction to Organic Chemistry, 6th Edition",
            "category": "Textbooks",
            "bsr": 50000,
            "avg_price_12m": 80.0,
            "price_volatility": 0.35,  # High volatility = seasonal
            "sales_per_month": 8,
        }

        result = identify_evergreen(product_data)

        assert result.is_evergreen is False
        assert result.evergreen_type == "SEASONAL"
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_evergreen_identifier.py -v
```

**Step 3: Implement evergreen identifier**

```python
# backend/app/services/evergreen_identifier_service.py
"""
Evergreen Book Identifier - Identify books with year-round consistent demand.

Evergreen books are critical for income smoothing during off-peak seasons.
They provide baseline revenue when seasonal textbooks are not selling.

Categories of evergreens:
- PROFESSIONAL_CERTIFICATION: NCLEX, CPA, PMP, MCAT, LSAT prep
- CLASSIC: Timeless programming, business, literature texts
- REFERENCE: Dictionaries, style guides, essential references
- SKILL_BASED: Language learning, music theory, art technique
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvergreenClassification:
    """Classification result for evergreen identification."""
    is_evergreen: bool
    evergreen_type: str  # PROFESSIONAL_CERTIFICATION, CLASSIC, REFERENCE, SKILL_BASED, SEASONAL
    confidence: float
    reasons: List[str]
    recommended_stock_level: int  # Suggested units to keep in inventory
    expected_monthly_sales: Optional[float] = None


# Keywords that indicate evergreen content
EVERGREEN_KEYWORDS = {
    "PROFESSIONAL_CERTIFICATION": [
        "nclex", "cpa", "pmp", "mcat", "lsat", "gmat", "gre",
        "pharmacology", "anatomy", "physiology", "nursing",
        "medical", "clinical", "pathophysiology", "certification",
        "board review", "exam prep", "license", "registered nurse",
    ],
    "CLASSIC": [
        "clean code", "design patterns", "algorithms", "data structures",
        "effective java", "python crash course", "javascript",
        "leadership", "management", "7 habits", "how to win friends",
        "thinking fast and slow", "sapiens",
    ],
    "REFERENCE": [
        "dictionary", "thesaurus", "style guide", "apa manual",
        "chicago manual", "reference", "handbook", "encyclopedia",
        "atlas", "almanac",
    ],
    "SKILL_BASED": [
        "spanish", "french", "german", "japanese", "chinese",
        "piano", "guitar", "music theory", "drawing", "painting",
        "photography", "yoga", "meditation",
    ],
}


def identify_evergreen(product_data: Dict[str, Any]) -> EvergreenClassification:
    """
    Identify if a book is evergreen (consistent year-round demand).

    Args:
        product_data: {
            "title": str,
            "category": str,
            "bsr": int,
            "avg_price_12m": float,
            "price_volatility": float,  # Coefficient of variation
            "sales_per_month": float,
        }

    Returns:
        EvergreenClassification with type and confidence
    """
    title = product_data.get("title", "").lower()
    category = product_data.get("category", "").lower()
    bsr = product_data.get("bsr", 999999)
    volatility = product_data.get("price_volatility", 1.0)
    monthly_sales = product_data.get("sales_per_month", 0)
    avg_price = product_data.get("avg_price_12m", 0)

    reasons = []
    confidence = 0.0
    evergreen_type = "SEASONAL"  # Default

    # Check keyword matches
    for eg_type, keywords in EVERGREEN_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in title or kw in category]
        if matches:
            evergreen_type = eg_type
            confidence += 0.3 * min(len(matches), 3)  # Up to 0.9 for 3+ matches
            reasons.append(f"Matches {eg_type} keywords: {', '.join(matches[:3])}")
            break

    # Low volatility indicates stable demand
    if volatility < 0.15:
        confidence += 0.3
        reasons.append(f"Low price volatility ({volatility:.2%})")
    elif volatility < 0.25:
        confidence += 0.15
        reasons.append(f"Moderate price volatility ({volatility:.2%})")

    # Good BSR indicates consistent sales
    if bsr < 50000:
        confidence += 0.2
        reasons.append(f"Strong BSR ({bsr:,})")
    elif bsr < 100000:
        confidence += 0.1
        reasons.append(f"Good BSR ({bsr:,})")

    # Consistent monthly sales
    if monthly_sales >= 10:
        confidence += 0.2
        reasons.append(f"High monthly sales ({monthly_sales:.0f}/month)")
    elif monthly_sales >= 5:
        confidence += 0.1
        reasons.append(f"Moderate monthly sales ({monthly_sales:.0f}/month)")

    # Determine if evergreen
    is_evergreen = confidence >= 0.5 and volatility < 0.30

    if not is_evergreen:
        evergreen_type = "SEASONAL"
        reasons = ["Does not meet evergreen criteria: " + (
            "high volatility" if volatility >= 0.30 else "low confidence score"
        )]

    # Calculate recommended stock level
    if is_evergreen:
        # Keep 2-3 months of inventory
        recommended_stock = max(2, int(monthly_sales * 2.5))
    else:
        recommended_stock = 0

    return EvergreenClassification(
        is_evergreen=is_evergreen,
        evergreen_type=evergreen_type,
        confidence=min(confidence, 1.0),
        reasons=reasons,
        recommended_stock_level=recommended_stock,
        expected_monthly_sales=monthly_sales if monthly_sales > 0 else None,
    )


def get_evergreen_portfolio_targets() -> Dict[str, Any]:
    """
    Get target allocation for evergreen portfolio.

    Returns recommended distribution for income smoothing.
    """
    return {
        "target_portfolio_pct": 30,  # 30% of inventory should be evergreen
        "categories": {
            "PROFESSIONAL_CERTIFICATION": {
                "target_pct": 40,
                "examples": ["NCLEX prep", "CPA review", "PMP guide"],
                "avg_roi": 45,
                "avg_monthly_sales": 8,
            },
            "CLASSIC": {
                "target_pct": 30,
                "examples": ["Clean Code", "Design Patterns", "CLRS Algorithms"],
                "avg_roi": 35,
                "avg_monthly_sales": 12,
            },
            "SKILL_BASED": {
                "target_pct": 20,
                "examples": ["Spanish textbooks", "Piano method books"],
                "avg_roi": 40,
                "avg_monthly_sales": 6,
            },
            "REFERENCE": {
                "target_pct": 10,
                "examples": ["APA Manual", "Medical dictionaries"],
                "avg_roi": 30,
                "avg_monthly_sales": 4,
            },
        },
        "min_evergreens_for_smoothing": 15,
        "target_monthly_revenue": 1000,  # $1000/month from evergreens
    }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_evergreen_identifier.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/evergreen_identifier_service.py backend/tests/services/test_evergreen_identifier.py
git commit -m "feat(evergreen): add evergreen book identifier for income smoothing

- Identify PROFESSIONAL_CERTIFICATION, CLASSIC, REFERENCE, SKILL_BASED
- Keyword matching for nursing, programming, language books
- Confidence scoring based on volatility, BSR, sales
- Portfolio allocation targets for 30% evergreen mix

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Create Reserve Calculator Service

**Files:**
- Create: `backend/app/services/reserve_calculator_service.py`
- Test: `backend/tests/services/test_reserve_calculator.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_reserve_calculator.py
import pytest
from app.services.reserve_calculator_service import (
    calculate_smoothing_reserve,
    project_annual_income,
    ReserveRecommendation,
)


class TestReserveCalculator:
    """Tests for income smoothing reserve calculations."""

    def test_calculate_reserve_for_target_income(self):
        """Should calculate reserve needed for target monthly income."""
        result = calculate_smoothing_reserve(
            target_monthly_income=2000,
            avg_peak_monthly=4500,
            avg_trough_monthly=800,
            trough_months=5,
        )

        assert isinstance(result, ReserveRecommendation)
        assert result.recommended_reserve > 0
        # Need to cover gap of $1200/month for 5 months = $6000
        assert result.recommended_reserve >= 5000
        assert result.recommended_reserve <= 8000
        assert result.monthly_contribution > 0

    def test_project_annual_income_with_seasonality(self):
        """Should project annual income accounting for seasonality."""
        monthly_projections = {
            1: 3500, 2: 800, 3: 600, 4: 1000,
            5: 4500, 6: 3500, 7: 1000, 8: 5500,
            9: 4500, 10: 1200, 11: 1500, 12: 3000,
        }

        result = project_annual_income(
            monthly_projections=monthly_projections,
            reserve_percentage=25,
        )

        assert result["annual_gross"] > 0
        assert result["annual_net_after_reserve"] < result["annual_gross"]
        assert result["avg_monthly_smoothed"] > 0
        assert "peak_months" in result
        assert "trough_months" in result

    def test_zero_trough_income_handled(self):
        """Should handle case where trough income is zero."""
        result = calculate_smoothing_reserve(
            target_monthly_income=2000,
            avg_peak_monthly=5000,
            avg_trough_monthly=0,
            trough_months=4,
        )

        # Should recommend full coverage for trough months
        assert result.recommended_reserve >= 2000 * 4
```

**Step 2: Implement reserve calculator**

```python
# backend/app/services/reserve_calculator_service.py
"""
Reserve Calculator Service - Calculate income smoothing reserves.

This service helps textbook sellers maintain consistent monthly income
despite seasonal fluctuations by calculating required reserves.

The Reservoir System:
- During peak months: Save 25% of profits to reserve
- During trough months: Draw from reserve to maintain target income
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReserveRecommendation:
    """Recommendation for income smoothing reserve."""
    recommended_reserve: float  # Total reserve amount needed
    monthly_contribution: float  # How much to save per peak month
    months_to_build: int  # How many peak months to build reserve
    coverage_months: int  # How many trough months this covers
    target_monthly_income: float
    safety_margin_pct: float  # Buffer above minimum


def calculate_smoothing_reserve(
    target_monthly_income: float,
    avg_peak_monthly: float,
    avg_trough_monthly: float,
    trough_months: int = 5,
    safety_margin: float = 0.15,
) -> ReserveRecommendation:
    """
    Calculate the reserve needed to smooth income across seasons.

    Args:
        target_monthly_income: Desired consistent monthly income
        avg_peak_monthly: Average profit during peak months
        avg_trough_monthly: Average profit during trough months
        trough_months: Number of low-income months per year
        safety_margin: Additional buffer (15% default)

    Returns:
        ReserveRecommendation with amounts and timeline
    """
    # Calculate monthly gap during trough
    monthly_gap = max(0, target_monthly_income - avg_trough_monthly)

    # Total reserve needed = gap * trough months + safety margin
    base_reserve = monthly_gap * trough_months
    reserve_with_margin = base_reserve * (1 + safety_margin)

    # Calculate monthly contribution from peak months
    peak_months = 12 - trough_months
    if peak_months > 0 and avg_peak_monthly > target_monthly_income:
        surplus_per_peak = avg_peak_monthly - target_monthly_income
        contribution_rate = 0.25  # Save 25% of surplus
        monthly_contribution = surplus_per_peak * contribution_rate

        # How many peak months to build full reserve
        if monthly_contribution > 0:
            months_to_build = int(reserve_with_margin / monthly_contribution) + 1
        else:
            months_to_build = peak_months * 2  # Will take 2 years
    else:
        monthly_contribution = 0
        months_to_build = 0

    return ReserveRecommendation(
        recommended_reserve=round(reserve_with_margin, 2),
        monthly_contribution=round(monthly_contribution, 2),
        months_to_build=months_to_build,
        coverage_months=trough_months,
        target_monthly_income=target_monthly_income,
        safety_margin_pct=safety_margin,
    )


def project_annual_income(
    monthly_projections: Dict[int, float],
    reserve_percentage: float = 25,
) -> Dict[str, Any]:
    """
    Project annual income with income smoothing.

    Args:
        monthly_projections: Dict of month (1-12) to projected profit
        reserve_percentage: Percentage of peak profits to reserve

    Returns:
        Annual projection with smoothing metrics
    """
    if not monthly_projections:
        return {"error": "No projections provided"}

    # Calculate totals
    annual_gross = sum(monthly_projections.values())
    avg_monthly = annual_gross / 12

    # Identify peaks and troughs
    sorted_months = sorted(monthly_projections.items(), key=lambda x: x[1], reverse=True)
    peak_months = [m for m, v in sorted_months[:4]]  # Top 4 months
    trough_months = [m for m, v in sorted_months[-5:]]  # Bottom 5 months

    # Calculate what goes to reserve
    peak_profits = sum(v for m, v in monthly_projections.items() if m in peak_months)
    reserve_contribution = peak_profits * (reserve_percentage / 100)

    # Net after reserve
    annual_net = annual_gross - reserve_contribution

    # Calculate smoothed monthly (using reserve to supplement troughs)
    trough_total = sum(v for m, v in monthly_projections.items() if m in trough_months)
    smoothed_trough_income = (trough_total + reserve_contribution) / len(trough_months)

    return {
        "annual_gross": round(annual_gross, 2),
        "annual_net_after_reserve": round(annual_net, 2),
        "reserve_contribution": round(reserve_contribution, 2),
        "avg_monthly_raw": round(avg_monthly, 2),
        "avg_monthly_smoothed": round((annual_net + reserve_contribution) / 12, 2),
        "peak_months": peak_months,
        "trough_months": trough_months,
        "peak_avg": round(peak_profits / len(peak_months), 2),
        "trough_avg": round(trough_total / len(trough_months), 2),
        "smoothed_trough_income": round(smoothed_trough_income, 2),
    }


def get_capital_growth_projection(
    initial_capital: float,
    monthly_roi_pct: float = 50,
    reinvestment_rate: float = 75,
    months: int = 12,
) -> List[Dict[str, Any]]:
    """
    Project capital growth over time with reinvestment.

    Args:
        initial_capital: Starting capital
        monthly_roi_pct: Expected ROI per cycle (as percentage)
        reinvestment_rate: Percentage of profits reinvested
        months: Number of months to project

    Returns:
        List of monthly projections with capital, profit, pocket
    """
    projections = []
    current_capital = initial_capital

    for month in range(1, months + 1):
        # Calculate profit
        gross_profit = current_capital * (monthly_roi_pct / 100)

        # Account for ~10% failures
        net_profit = gross_profit * 0.90

        # Split profits
        reinvested = net_profit * (reinvestment_rate / 100)
        pocket = net_profit - reinvested

        # Update capital
        new_capital = current_capital + reinvested

        projections.append({
            "month": month,
            "starting_capital": round(current_capital, 2),
            "gross_profit": round(gross_profit, 2),
            "net_profit": round(net_profit, 2),
            "reinvested": round(reinvested, 2),
            "pocket": round(pocket, 2),
            "ending_capital": round(new_capital, 2),
            "cumulative_pocket": round(sum(p["pocket"] for p in projections) + pocket, 2),
        })

        current_capital = new_capital

    return projections
```

**Step 3: Run tests**

```bash
cd backend && python -m pytest tests/services/test_reserve_calculator.py -v
```

**Step 4: Commit**

```bash
git add backend/app/services/reserve_calculator_service.py backend/tests/services/test_reserve_calculator.py
git commit -m "feat(reserve): add income smoothing reserve calculator

- Calculate reserve needed for target monthly income
- Project annual income with seasonality
- Capital growth projection with reinvestment
- Support 25% reserve contribution from peaks

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: API Endpoints & Frontend (Days 11-14)

### Task 9: Create Textbook Analysis API Endpoint

**Files:**
- Create: `backend/app/api/v1/routers/textbook_analysis.py`
- Modify: `backend/app/api/v1/__init__.py`
- Test: `backend/tests/api/test_textbook_analysis_api.py`

**Step 1: Write API test**

```python
# backend/tests/api/test_textbook_analysis_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestTextbookAnalysisAPI:
    """Tests for textbook analysis API endpoints."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_analyze_textbook_returns_intrinsic_value(self, client):
        """POST /api/v1/textbook/analyze should return intrinsic value data."""
        mock_response = {
            "asin": "0134685991",
            "title": "Effective Java",
            "intrinsic_value": {
                "low": 45.0,
                "median": 55.0,
                "high": 65.0,
                "confidence": "HIGH",
            },
            "seasonal_pattern": {
                "pattern_type": "COLLEGE_FALL",
                "days_until_peak": 45,
            },
            "recommendation": "BUY",
        }

        with patch("app.api.v1.routers.textbook_analysis.analyze_textbook") as mock:
            mock.return_value = mock_response

            response = client.post(
                "/api/v1/textbook/analyze",
                json={"asin": "0134685991", "source_price": 25.0},
            )

            assert response.status_code == 200
            data = response.json()
            assert "intrinsic_value" in data
            assert "seasonal_pattern" in data
```

**Step 2: Implement API router**

```python
# backend/app/api/v1/routers/textbook_analysis.py
"""
Textbook Analysis API - Endpoints for textbook-specific analysis.

Provides intrinsic value calculation, seasonal detection, and
textbook-optimized recommendations.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.intrinsic_value_service import get_sell_price_for_strategy
from app.services.seasonal_detector_service import detect_seasonal_pattern, get_days_until_peak
from app.services.evergreen_identifier_service import identify_evergreen
from app.services.reserve_calculator_service import calculate_smoothing_reserve
from app.services.keepa_service import KeepaService
from app.services.keepa_parser_v2 import parse_keepa_product_unified
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/textbook", tags=["textbook"])


class TextbookAnalysisRequest(BaseModel):
    """Request for textbook analysis."""
    asin: str = Field(..., min_length=10, max_length=10)
    source_price: Optional[float] = Field(None, ge=0)


class TextbookAnalysisResponse(BaseModel):
    """Response from textbook analysis."""
    asin: str
    title: str
    intrinsic_value: Dict[str, Any]
    seasonal_pattern: Dict[str, Any]
    evergreen_classification: Dict[str, Any]
    recommendation: str
    roi_metrics: Dict[str, Any]
    confidence_score: float


@router.post("/analyze", response_model=TextbookAnalysisResponse)
async def analyze_textbook(
    request: TextbookAnalysisRequest,
    keepa_service: KeepaService = Depends(),
    current_user = Depends(get_current_user),
) -> TextbookAnalysisResponse:
    """
    Analyze a textbook ASIN with intrinsic value and seasonal detection.

    Returns comprehensive analysis optimized for textbook arbitrage.
    """
    try:
        # Fetch from Keepa
        raw_keepa = await keepa_service.get_product(request.asin)
        if not raw_keepa:
            raise HTTPException(status_code=404, detail="Product not found")

        # Parse Keepa data
        parsed = parse_keepa_product_unified(raw_keepa)

        # Get intrinsic value
        intrinsic = get_sell_price_for_strategy(parsed, strategy="textbook")

        # Detect seasonal pattern
        seasonal = detect_seasonal_pattern(parsed.get("price_history", []))
        days_to_peak = get_days_until_peak(seasonal)

        # Check if evergreen
        evergreen = identify_evergreen({
            "title": parsed.get("title", ""),
            "category": parsed.get("category", ""),
            "bsr": parsed.get("current_bsr", 999999),
            "avg_price_12m": intrinsic.get("intrinsic_corridor", {}).get("median", 0),
            "price_volatility": intrinsic.get("intrinsic_corridor", {}).get("volatility", 1),
            "sales_per_month": parsed.get("sales_drops_30", 0),
        })

        # Calculate ROI if source price provided
        roi_metrics = {}
        if request.source_price:
            sell_price = intrinsic["sell_price"]
            if sell_price:
                fees = sell_price * 0.22  # Estimated 22% fees
                profit = sell_price - fees - request.source_price
                roi_metrics = {
                    "source_price": request.source_price,
                    "estimated_sell_price": sell_price,
                    "estimated_fees": round(fees, 2),
                    "estimated_profit": round(profit, 2),
                    "roi_pct": round(profit / request.source_price, 4) if request.source_price > 0 else 0,
                }

        # Generate recommendation
        recommendation = _generate_recommendation(
            intrinsic=intrinsic,
            seasonal=seasonal,
            evergreen=evergreen,
            roi_metrics=roi_metrics,
        )

        return TextbookAnalysisResponse(
            asin=request.asin,
            title=parsed.get("title", "Unknown"),
            intrinsic_value=intrinsic.get("intrinsic_corridor", {}),
            seasonal_pattern={
                "pattern_type": seasonal.pattern_type,
                "peak_months": seasonal.peak_months,
                "days_until_peak": days_to_peak,
                "buy_recommendation": seasonal.price_swing_pct,
            },
            evergreen_classification={
                "is_evergreen": evergreen.is_evergreen,
                "type": evergreen.evergreen_type,
                "confidence": evergreen.confidence,
            },
            recommendation=recommendation,
            roi_metrics=roi_metrics,
            confidence_score=intrinsic.get("confidence", 0),
        )

    except Exception as e:
        logger.error(f"Textbook analysis failed for {request.asin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendation(
    intrinsic: Dict,
    seasonal: Any,
    evergreen: Any,
    roi_metrics: Dict,
) -> str:
    """Generate buy/skip recommendation based on analysis."""
    confidence = intrinsic.get("confidence", "LOW")
    roi = roi_metrics.get("roi_pct", 0)

    if confidence == "INSUFFICIENT_DATA":
        return "SKIP - Insufficient price history"

    if evergreen.is_evergreen and evergreen.confidence > 0.7:
        if roi >= 0.35:
            return "STRONG_BUY - Evergreen with good ROI"
        elif roi >= 0.25:
            return "BUY - Evergreen, consistent demand"

    if seasonal.pattern_type in ["COLLEGE_FALL", "COLLEGE_SPRING", "HIGH_SCHOOL"]:
        if roi >= 0.50:
            return f"STRONG_BUY - {seasonal.pattern_type} seasonal, excellent ROI"
        elif roi >= 0.35:
            return f"BUY - {seasonal.pattern_type} seasonal"

    if roi >= 0.40 and confidence in ["HIGH", "MEDIUM"]:
        return "BUY - Good intrinsic value"
    elif roi >= 0.25:
        return "CONSIDER - Moderate opportunity"
    else:
        return "SKIP - ROI below threshold"
```

**Step 3: Register router**

Add to `backend/app/api/v1/__init__.py`:
```python
from app.api.v1.routers.textbook_analysis import router as textbook_router
# ... in router registration
app.include_router(textbook_router, prefix="/api/v1")
```

**Step 4: Commit**

```bash
git add backend/app/api/v1/routers/textbook_analysis.py backend/tests/api/test_textbook_analysis_api.py
git commit -m "feat(api): add textbook analysis endpoint

- POST /api/v1/textbook/analyze
- Returns intrinsic value, seasonal pattern, evergreen classification
- Generates BUY/SKIP recommendation
- Calculates ROI with textbook strategy

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Run Full Test Suite & Final Verification

**Step 1: Run all new tests**

```bash
cd backend && python -m pytest tests/services/test_intrinsic_value_service.py tests/services/test_seasonal_detector.py tests/services/test_evergreen_identifier.py tests/services/test_reserve_calculator.py -v
```

**Step 2: Run existing tests to ensure no regression**

```bash
cd backend && python -m pytest tests/ -v --tb=short
```

**Step 3: Type check**

```bash
cd backend && mypy app/services/intrinsic_value_service.py app/services/seasonal_detector_service.py app/services/evergreen_identifier_service.py app/services/reserve_calculator_service.py
```

**Step 4: Final commit**

```bash
git add .
git commit -m "chore: complete Phase 1-2 of textbook pivot implementation

Summary:
- Intrinsic Value Service with [P25, Median, P75] corridor
- Seasonal Pattern Detector (COLLEGE_FALL, COLLEGE_SPRING, HIGH_SCHOOL)
- Evergreen Identifier for income smoothing
- Reserve Calculator for year-round stability
- Textbook Analysis API endpoint
- Updated business rules with intrinsic value config

All tests passing. Ready for Phase 3 (Frontend).

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Summary

### Files Created (8)
- `backend/app/services/intrinsic_value_service.py`
- `backend/app/services/seasonal_detector_service.py`
- `backend/app/services/evergreen_identifier_service.py`
- `backend/app/services/reserve_calculator_service.py`
- `backend/app/api/v1/routers/textbook_analysis.py`
- `backend/tests/services/test_intrinsic_value_service.py`
- `backend/tests/services/test_seasonal_detector.py`
- `backend/tests/services/test_evergreen_identifier.py`
- `backend/tests/services/test_reserve_calculator.py`

### Files Modified (3)
- `backend/app/services/pricing_service.py`
- `backend/app/services/unified_analysis.py`
- `backend/config/business_rules.json`

### Key Capabilities Added
1. **Intrinsic Value Calculation** - Historical median instead of snapshot
2. **Confidence Scoring** - Know when to trust the data
3. **Seasonal Detection** - College Fall, Spring, High School patterns
4. **Evergreen Identification** - Year-round income sources
5. **Reserve Calculator** - Income smoothing math
6. **Textbook API** - Dedicated endpoint for textbook analysis

### Estimated Time
- Phase 1 (Tasks 1-5): 5 days
- Phase 2 (Tasks 6-8): 4 days
- Phase 3 (Tasks 9-10): 3 days
- **Total: 12 days**
