# Textbook UX Simplification - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify product display with clear buy/sell guidance, rename technical fields to user-friendly labels, and add explanatory tooltips.

**Architecture:** Add a `BuyingGuidanceService` backend to calculate max buy price and estimated profit. Update frontend `UnifiedProductTable` to display simplified columns with tooltips explaining each metric. Replace technical jargon ("intrinsic") with clear labels ("Prix de vente estime").

**Tech Stack:** Python 3.11+, FastAPI, React 18, TypeScript, Tailwind CSS, Lucide React icons

---

## Phase 1: Backend - Buying Guidance Service (Tasks 1-3)

### Task 1: Create Buying Guidance Service

**Files:**
- Create: `backend/app/services/buying_guidance_service.py`
- Test: `backend/tests/services/test_buying_guidance_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_buying_guidance_service.py
"""
Tests for Buying Guidance Service.

This service provides clear buy/sell recommendations with explanations.
"""

import pytest
from app.services.buying_guidance_service import (
    calculate_buying_guidance,
    BuyingGuidance,
)


class TestBuyingGuidance:
    """Tests for buying guidance calculations."""

    def test_calculate_guidance_with_valid_data(self):
        """Test guidance calculation with complete data."""
        # Arrange
        intrinsic_data = {
            "low": 45.0,
            "median": 52.0,
            "high": 58.0,
            "confidence": "HIGH",
            "volatility": 0.08,
            "data_points": 98,
        }
        bsr = 12450
        sales_per_month = 45

        # Act
        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            current_bsr=bsr,
            estimated_monthly_sales=sales_per_month,
            target_roi_pct=0.50,
            amazon_fee_pct=0.22,
        )

        # Assert
        assert isinstance(result, BuyingGuidance)
        assert result.max_buy_price > 0
        assert result.target_sell_price == 52.0
        assert result.estimated_profit > 0
        assert result.estimated_roi_pct >= 0.50
        assert result.estimated_days_to_sell > 0
        assert result.recommendation in ["BUY", "HOLD", "SKIP"]
        assert result.confidence_label in ["Fiable", "Modere", "Incertain", "Donnees insuffisantes"]

    def test_calculate_max_buy_price_for_50_roi(self):
        """Max buy price should guarantee 50% ROI after fees."""
        intrinsic_data = {
            "low": 45.0,
            "median": 52.0,
            "high": 58.0,
            "confidence": "HIGH",
        }

        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            target_roi_pct=0.50,
            amazon_fee_pct=0.22,
        )

        # Verify: sell_price - fees - max_buy = 50% of max_buy
        # $52 - ($52 * 0.22) - max_buy = 0.50 * max_buy
        # $52 - $11.44 = 1.50 * max_buy
        # max_buy = $40.56 / 1.50 = $27.04
        expected_max = (52.0 * (1 - 0.22)) / 1.50
        assert abs(result.max_buy_price - expected_max) < 0.01

    def test_guidance_with_insufficient_data(self):
        """Should return SKIP when confidence is insufficient."""
        intrinsic_data = {
            "low": None,
            "median": None,
            "high": None,
            "confidence": "INSUFFICIENT_DATA",
        }

        result = calculate_buying_guidance(intrinsic_corridor=intrinsic_data)

        assert result.recommendation == "SKIP"
        assert result.confidence_label == "Donnees insuffisantes"
        assert "pas assez" in result.recommendation_reason.lower()

    def test_estimated_days_to_sell_from_bsr(self):
        """Days to sell should be calculated from sales velocity."""
        intrinsic_data = {"median": 50.0, "confidence": "HIGH"}

        # 45 sales/month = ~1.5 sales/day = ~0.67 days per sale
        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            current_bsr=12450,
            estimated_monthly_sales=45,
        )

        # Should be around 1 day (30 days / 45 sales)
        assert 0 < result.estimated_days_to_sell < 5

    def test_price_range_formatting(self):
        """Price range should be formatted as string."""
        intrinsic_data = {
            "low": 45.0,
            "median": 52.0,
            "high": 58.0,
            "confidence": "HIGH",
        }

        result = calculate_buying_guidance(intrinsic_corridor=intrinsic_data)

        assert result.price_range == "$45 - $58"

    def test_explanations_are_provided(self):
        """Each field should have an explanation."""
        intrinsic_data = {"median": 50.0, "confidence": "HIGH", "data_points": 90}

        result = calculate_buying_guidance(intrinsic_corridor=intrinsic_data)

        assert result.explanations is not None
        assert "max_buy_price" in result.explanations
        assert "target_sell_price" in result.explanations
        assert "confidence" in result.explanations
        assert len(result.explanations["max_buy_price"]) > 10  # Not empty


class TestRecommendationLogic:
    """Tests for recommendation generation."""

    def test_strong_buy_high_roi_high_confidence(self):
        """STRONG BUY when ROI > 100% and confidence HIGH."""
        intrinsic_data = {
            "median": 100.0,
            "low": 90.0,
            "high": 110.0,
            "confidence": "HIGH",
        }

        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            source_price=20.0,  # ROI would be very high
        )

        assert "BUY" in result.recommendation

    def test_skip_low_roi(self):
        """SKIP when ROI < 30%."""
        intrinsic_data = {
            "median": 25.0,
            "confidence": "HIGH",
        }

        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            source_price=20.0,  # Very low margin
        )

        # With $25 sell, $5.50 fees, $20 buy = -$0.50 loss
        assert result.recommendation == "SKIP"

    def test_hold_medium_confidence(self):
        """HOLD when confidence is MEDIUM and ROI is moderate."""
        intrinsic_data = {
            "median": 50.0,
            "confidence": "MEDIUM",
        }

        result = calculate_buying_guidance(
            intrinsic_corridor=intrinsic_data,
            source_price=25.0,  # ~56% ROI
        )

        assert result.recommendation in ["HOLD", "BUY"]
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_buying_guidance_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.buying_guidance_service'`

**Step 3: Write minimal implementation**

```python
# backend/app/services/buying_guidance_service.py
"""
Buying Guidance Service - Clear Buy/Sell Recommendations.

This service transforms technical pricing data into actionable guidance:
- Maximum price to pay for target ROI
- Expected sell price (historical median)
- Estimated profit and time to sell
- Clear recommendation with explanation

All labels are user-friendly French, not technical jargon.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS - User-Friendly Labels
# =============================================================================

CONFIDENCE_LABELS = {
    "HIGH": "Fiable",
    "MEDIUM": "Modere",
    "LOW": "Incertain",
    "INSUFFICIENT_DATA": "Donnees insuffisantes",
}

RECOMMENDATION_THRESHOLDS = {
    "strong_buy_roi": 1.00,  # 100% ROI
    "buy_roi": 0.50,         # 50% ROI
    "hold_roi": 0.30,        # 30% ROI
    # Below 30% = SKIP
}

EXPLANATIONS = {
    "max_buy_price": "Prix maximum a payer pour garantir {target_roi}% de ROI apres frais Amazon.",
    "target_sell_price": "Prix median des {days} derniers jours. Plus fiable qu'un prix ponctuel.",
    "estimated_profit": "Profit estime: prix vente - prix achat - frais Amazon ({fee_pct}%).",
    "price_range": "Le livre se vend generalement dans cette fourchette de prix.",
    "estimated_days_to_sell": "Temps moyen pour vendre base sur le BSR et les ventes mensuelles.",
    "confidence": "Fiabilite basee sur {data_points} points de donnees et {volatility}% de volatilite.",
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BuyingGuidance:
    """User-friendly buying guidance with explanations."""

    # Core guidance
    max_buy_price: float
    target_sell_price: float
    estimated_profit: float
    estimated_roi_pct: float
    price_range: str
    estimated_days_to_sell: int

    # Recommendation
    recommendation: str  # BUY, HOLD, SKIP
    recommendation_reason: str
    confidence_label: str  # Fiable, Modere, Incertain, Donnees insuffisantes

    # Explanations for tooltips
    explanations: Dict[str, str]

    # Raw data for debugging
    raw_confidence: str
    raw_data_points: int


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_buying_guidance(
    intrinsic_corridor: Dict[str, Any],
    current_bsr: Optional[int] = None,
    estimated_monthly_sales: Optional[int] = None,
    source_price: Optional[float] = None,
    target_roi_pct: float = 0.50,
    amazon_fee_pct: float = 0.22,
    window_days: int = 90,
) -> BuyingGuidance:
    """
    Calculate clear buying guidance from intrinsic value data.

    Args:
        intrinsic_corridor: Output from calculate_intrinsic_value_corridor()
        current_bsr: Best Seller Rank for velocity estimation
        estimated_monthly_sales: Estimated sales per month
        source_price: Actual price user would pay (for real ROI calc)
        target_roi_pct: Target ROI for max_buy_price calculation (default 50%)
        amazon_fee_pct: Amazon fee percentage (default 22%)
        window_days: Days of historical data used

    Returns:
        BuyingGuidance with all user-friendly fields and explanations
    """
    confidence = intrinsic_corridor.get("confidence", "INSUFFICIENT_DATA")
    median = intrinsic_corridor.get("median")
    low = intrinsic_corridor.get("low")
    high = intrinsic_corridor.get("high")
    data_points = intrinsic_corridor.get("data_points", 0)
    volatility = intrinsic_corridor.get("volatility", 0)

    # Handle insufficient data
    if confidence == "INSUFFICIENT_DATA" or median is None:
        return _insufficient_data_guidance(intrinsic_corridor)

    # Calculate max buy price for target ROI
    # Formula: sell_price * (1 - fee_pct) = max_buy * (1 + target_roi)
    # Therefore: max_buy = sell_price * (1 - fee_pct) / (1 + target_roi)
    net_after_fees = median * (1 - amazon_fee_pct)
    max_buy_price = net_after_fees / (1 + target_roi_pct)

    # Calculate estimated profit (if source_price provided)
    if source_price is not None:
        estimated_profit = net_after_fees - source_price
        estimated_roi_pct = estimated_profit / source_price if source_price > 0 else 0
    else:
        # Use max_buy_price as reference
        estimated_profit = net_after_fees - max_buy_price
        estimated_roi_pct = target_roi_pct

    # Format price range
    if low is not None and high is not None:
        price_range = f"${low:.0f} - ${high:.0f}"
    else:
        price_range = f"~${median:.0f}"

    # Estimate days to sell
    if estimated_monthly_sales and estimated_monthly_sales > 0:
        estimated_days_to_sell = max(1, round(30 / estimated_monthly_sales))
    elif current_bsr:
        # Rough estimate: BSR 10000 = ~30 sales/month
        estimated_monthly = max(1, 300000 / current_bsr)
        estimated_days_to_sell = max(1, round(30 / estimated_monthly))
    else:
        estimated_days_to_sell = 14  # Default 2 weeks

    # Generate recommendation
    recommendation, reason = _generate_recommendation(
        estimated_roi_pct=estimated_roi_pct,
        confidence=confidence,
        source_price=source_price,
        max_buy_price=max_buy_price,
    )

    # Build explanations
    explanations = _build_explanations(
        target_roi_pct=target_roi_pct,
        amazon_fee_pct=amazon_fee_pct,
        window_days=window_days,
        data_points=data_points,
        volatility=volatility,
    )

    return BuyingGuidance(
        max_buy_price=round(max_buy_price, 2),
        target_sell_price=round(median, 2),
        estimated_profit=round(estimated_profit, 2),
        estimated_roi_pct=round(estimated_roi_pct, 4),
        price_range=price_range,
        estimated_days_to_sell=estimated_days_to_sell,
        recommendation=recommendation,
        recommendation_reason=reason,
        confidence_label=CONFIDENCE_LABELS.get(confidence, "Inconnu"),
        explanations=explanations,
        raw_confidence=confidence,
        raw_data_points=data_points,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _insufficient_data_guidance(intrinsic_corridor: Dict[str, Any]) -> BuyingGuidance:
    """Return guidance when data is insufficient."""
    reason = intrinsic_corridor.get("reason", "Pas assez de donnees historiques")

    return BuyingGuidance(
        max_buy_price=0.0,
        target_sell_price=0.0,
        estimated_profit=0.0,
        estimated_roi_pct=0.0,
        price_range="N/A",
        estimated_days_to_sell=0,
        recommendation="SKIP",
        recommendation_reason=f"Donnees insuffisantes: {reason}",
        confidence_label=CONFIDENCE_LABELS["INSUFFICIENT_DATA"],
        explanations={
            "max_buy_price": "Impossible a calculer sans historique de prix.",
            "target_sell_price": "Impossible a calculer sans historique de prix.",
            "confidence": "Pas assez de points de donnees pour une estimation fiable.",
        },
        raw_confidence="INSUFFICIENT_DATA",
        raw_data_points=0,
    )


def _generate_recommendation(
    estimated_roi_pct: float,
    confidence: str,
    source_price: Optional[float],
    max_buy_price: float,
) -> tuple[str, str]:
    """Generate recommendation and reason."""

    # Check if source price exceeds max buy
    if source_price is not None and source_price > max_buy_price:
        return "SKIP", f"Prix source (${source_price:.2f}) depasse le max recommande (${max_buy_price:.2f})"

    # ROI-based recommendation
    if estimated_roi_pct >= RECOMMENDATION_THRESHOLDS["strong_buy_roi"]:
        if confidence == "HIGH":
            return "BUY", f"ROI excellent ({estimated_roi_pct:.0%}) avec donnees fiables"
        else:
            return "BUY", f"ROI excellent ({estimated_roi_pct:.0%}) mais verifier les donnees"

    elif estimated_roi_pct >= RECOMMENDATION_THRESHOLDS["buy_roi"]:
        if confidence in ["HIGH", "MEDIUM"]:
            return "BUY", f"Bon ROI ({estimated_roi_pct:.0%}) avec confiance {CONFIDENCE_LABELS.get(confidence, confidence)}"
        else:
            return "HOLD", f"ROI acceptable ({estimated_roi_pct:.0%}) mais donnees incertaines"

    elif estimated_roi_pct >= RECOMMENDATION_THRESHOLDS["hold_roi"]:
        return "HOLD", f"ROI modere ({estimated_roi_pct:.0%}), a evaluer selon votre strategie"

    else:
        return "SKIP", f"ROI trop faible ({estimated_roi_pct:.0%}) pour etre rentable"


def _build_explanations(
    target_roi_pct: float,
    amazon_fee_pct: float,
    window_days: int,
    data_points: int,
    volatility: float,
) -> Dict[str, str]:
    """Build user-friendly explanations for each field."""
    return {
        "max_buy_price": EXPLANATIONS["max_buy_price"].format(
            target_roi=int(target_roi_pct * 100)
        ),
        "target_sell_price": EXPLANATIONS["target_sell_price"].format(
            days=window_days
        ),
        "estimated_profit": EXPLANATIONS["estimated_profit"].format(
            fee_pct=int(amazon_fee_pct * 100)
        ),
        "price_range": EXPLANATIONS["price_range"],
        "estimated_days_to_sell": EXPLANATIONS["estimated_days_to_sell"],
        "confidence": EXPLANATIONS["confidence"].format(
            data_points=data_points,
            volatility=round(volatility * 100, 1),
        ),
    }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "calculate_buying_guidance",
    "BuyingGuidance",
]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_buying_guidance_service.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/buying_guidance_service.py backend/tests/services/test_buying_guidance_service.py
git commit -m "feat(guidance): add buying guidance service with user-friendly labels

- Calculate max buy price for target ROI
- Generate BUY/HOLD/SKIP recommendations with reasons
- French labels: Fiable, Modere, Incertain
- Explanations for each field (tooltips)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Integrate Buying Guidance into Unified Analysis

**Files:**
- Modify: `backend/app/services/unified_analysis.py`
- Test: `backend/tests/services/test_unified_analysis_guidance.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_unified_analysis_guidance.py
"""
Tests for buying guidance integration in unified analysis.
"""

import pytest
from datetime import datetime, timedelta
from app.services.unified_analysis import build_unified_product_v2


class TestUnifiedAnalysisGuidance:
    """Tests for buying guidance in unified product response."""

    @pytest.fixture
    def sample_keepa_parsed(self):
        """Sample parsed Keepa data with price history."""
        base_time = datetime.now()
        return {
            "asin": "0134685991",
            "title": "Effective Java",
            "current_bsr": 12450,
            "sales_drops_30": 45,
            "price_history": [
                (base_time - timedelta(days=i), 52.0 + (i % 5) - 2)
                for i in range(90)
            ],
        }

    def test_response_includes_buying_guidance(self, sample_keepa_parsed):
        """Unified response should include buying_guidance section."""
        result = build_unified_product_v2(
            parsed_data=sample_keepa_parsed,
            strategy="textbook",
        )

        assert "buying_guidance" in result
        guidance = result["buying_guidance"]
        assert "max_buy_price" in guidance
        assert "target_sell_price" in guidance
        assert "recommendation" in guidance
        assert "confidence_label" in guidance
        assert "explanations" in guidance

    def test_guidance_uses_intrinsic_value(self, sample_keepa_parsed):
        """Guidance should use intrinsic median, not current price."""
        result = build_unified_product_v2(
            parsed_data=sample_keepa_parsed,
            strategy="textbook",
        )

        guidance = result["buying_guidance"]
        # Median should be around 52 based on fixture
        assert 48 <= guidance["target_sell_price"] <= 56

    def test_guidance_with_source_price(self, sample_keepa_parsed):
        """When source_price provided, calculate real ROI."""
        result = build_unified_product_v2(
            parsed_data=sample_keepa_parsed,
            strategy="textbook",
            source_price=15.0,
        )

        guidance = result["buying_guidance"]
        assert guidance["estimated_profit"] > 0
        assert guidance["estimated_roi_pct"] > 0.50  # Should be good ROI
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/services/test_unified_analysis_guidance.py -v
```

Expected: FAIL (buying_guidance not in response)

**Step 3: Modify unified_analysis.py**

Add to `build_unified_product_v2` function:

```python
# Add import at top
from app.services.buying_guidance_service import calculate_buying_guidance

# Inside build_unified_product_v2, after intrinsic value calculation:

    # Calculate buying guidance
    buying_guidance_result = calculate_buying_guidance(
        intrinsic_corridor=corridor,
        current_bsr=parsed_data.get("current_bsr"),
        estimated_monthly_sales=parsed_data.get("sales_drops_30"),
        source_price=source_price,
        target_roi_pct=0.50,
        amazon_fee_pct=0.22,
    )

    # Add to response
    result["buying_guidance"] = {
        "max_buy_price": buying_guidance_result.max_buy_price,
        "target_sell_price": buying_guidance_result.target_sell_price,
        "estimated_profit": buying_guidance_result.estimated_profit,
        "estimated_roi_pct": buying_guidance_result.estimated_roi_pct,
        "price_range": buying_guidance_result.price_range,
        "estimated_days_to_sell": buying_guidance_result.estimated_days_to_sell,
        "recommendation": buying_guidance_result.recommendation,
        "recommendation_reason": buying_guidance_result.recommendation_reason,
        "confidence_label": buying_guidance_result.confidence_label,
        "explanations": buying_guidance_result.explanations,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/services/test_unified_analysis_guidance.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/unified_analysis.py backend/tests/services/test_unified_analysis_guidance.py
git commit -m "feat(unified): integrate buying guidance into product response

- Add buying_guidance section to unified product response
- Include max_buy_price, target_sell_price, recommendation
- Include explanations for frontend tooltips

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Update API Response Schema

**Files:**
- Modify: `backend/app/api/v1/routers/textbook_analysis.py`
- Test: `backend/tests/api/test_textbook_analysis_guidance.py`

**Step 1: Write the failing test**

```python
# backend/tests/api/test_textbook_analysis_guidance.py
"""
Tests for buying guidance in textbook analysis API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestTextbookAnalysisGuidance:
    """Tests for buying guidance in API response."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_response_includes_buying_guidance(self, client):
        """API response should include buying_guidance section."""
        mock_response = {
            "asin": "0134685991",
            "title": "Effective Java",
            "buying_guidance": {
                "max_buy_price": 27.04,
                "target_sell_price": 52.0,
                "estimated_profit": 25.0,
                "recommendation": "BUY",
                "confidence_label": "Fiable",
                "explanations": {
                    "max_buy_price": "Prix maximum pour 50% ROI",
                },
            },
        }

        with patch("app.api.v1.routers.textbook_analysis.analyze_textbook_full") as mock:
            mock.return_value = mock_response

            response = client.post(
                "/api/v1/textbook/analyze",
                json={"asin": "0134685991", "source_price": 15.0},
            )

            assert response.status_code == 200
            data = response.json()
            assert "buying_guidance" in data
            assert data["buying_guidance"]["recommendation"] == "BUY"
```

**Step 2: Run test, update router, verify**

Update the textbook_analysis router to include buying_guidance in response.

**Step 3: Commit**

```bash
git add backend/app/api/v1/routers/textbook_analysis.py backend/tests/api/test_textbook_analysis_guidance.py
git commit -m "feat(api): add buying guidance to textbook analysis response

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Frontend - Simplified Display with Tooltips (Tasks 4-8)

> **For Claude:** Use `frontend-design` skill for Tasks 4-8.

### Task 4: Create Tooltip Component

**Files:**
- Create: `frontend/src/components/ui/Tooltip.tsx`
- Test: `frontend/src/components/ui/__tests__/Tooltip.test.tsx`

**Step 1: Create reusable Tooltip component**

```tsx
// frontend/src/components/ui/Tooltip.tsx
/**
 * Tooltip Component - User-friendly explanations on hover.
 *
 * Uses Tailwind group-hover pattern for accessibility.
 */

import { HelpCircle } from 'lucide-react';
import { ReactNode } from 'react';

interface TooltipProps {
  content: string;
  children?: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  showIcon?: boolean;
}

export function Tooltip({
  content,
  children,
  position = 'top',
  showIcon = true
}: TooltipProps) {
  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className="relative inline-flex items-center group">
      {children}
      {showIcon && (
        <HelpCircle
          className="w-4 h-4 ml-1 text-gray-400 cursor-help"
          aria-label={content}
        />
      )}
      <div
        className={`
          absolute ${positionClasses[position]}
          px-3 py-2 text-sm text-white bg-gray-900 rounded-lg
          opacity-0 invisible group-hover:opacity-100 group-hover:visible
          transition-all duration-200 z-50
          min-w-[200px] max-w-[300px]
          shadow-lg
        `}
        role="tooltip"
      >
        {content}
        <div
          className={`
            absolute w-2 h-2 bg-gray-900 transform rotate-45
            ${position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -mt-1' : ''}
            ${position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1' : ''}
          `}
        />
      </div>
    </div>
  );
}

export default Tooltip;
```

**Step 2: Commit**

```bash
git add frontend/src/components/ui/Tooltip.tsx
git commit -m "feat(ui): add Tooltip component for field explanations

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Create Confidence Badge Component

**Files:**
- Create: `frontend/src/components/ui/ConfidenceBadge.tsx`

**Step 1: Create component**

```tsx
// frontend/src/components/ui/ConfidenceBadge.tsx
/**
 * Confidence Badge - Visual indicator of data reliability.
 */

interface ConfidenceBadgeProps {
  level: 'Fiable' | 'Modere' | 'Incertain' | 'Donnees insuffisantes' | string;
  showLabel?: boolean;
}

const BADGE_STYLES = {
  'Fiable': {
    bg: 'bg-green-100',
    text: 'text-green-800',
    dot: 'bg-green-500',
  },
  'Modere': {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    dot: 'bg-yellow-500',
  },
  'Incertain': {
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    dot: 'bg-orange-500',
  },
  'Donnees insuffisantes': {
    bg: 'bg-red-100',
    text: 'text-red-800',
    dot: 'bg-red-500',
  },
};

export function ConfidenceBadge({ level, showLabel = true }: ConfidenceBadgeProps) {
  const styles = BADGE_STYLES[level] || BADGE_STYLES['Incertain'];

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium
        ${styles.bg} ${styles.text}
      `}
    >
      <span className={`w-2 h-2 rounded-full ${styles.dot}`} />
      {showLabel && level}
    </span>
  );
}

export default ConfidenceBadge;
```

**Step 2: Commit**

```bash
git add frontend/src/components/ui/ConfidenceBadge.tsx
git commit -m "feat(ui): add ConfidenceBadge component with color coding

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Create Buying Guidance Card Component

**Files:**
- Create: `frontend/src/components/product/BuyingGuidanceCard.tsx`

**Step 1: Create component**

```tsx
// frontend/src/components/product/BuyingGuidanceCard.tsx
/**
 * Buying Guidance Card - Clear buy/sell recommendations.
 *
 * Displays:
 * - Max buy price
 * - Target sell price
 * - Estimated profit
 * - Recommendation with confidence
 */

import { Tooltip } from '../ui/Tooltip';
import { ConfidenceBadge } from '../ui/ConfidenceBadge';
import { TrendingUp, TrendingDown, DollarSign, Clock } from 'lucide-react';

interface BuyingGuidance {
  max_buy_price: number;
  target_sell_price: number;
  estimated_profit: number;
  estimated_roi_pct: number;
  price_range: string;
  estimated_days_to_sell: number;
  recommendation: 'BUY' | 'HOLD' | 'SKIP';
  recommendation_reason: string;
  confidence_label: string;
  explanations: Record<string, string>;
}

interface BuyingGuidanceCardProps {
  guidance: BuyingGuidance;
  sourcePrice?: number;
}

const RECOMMENDATION_STYLES = {
  BUY: 'bg-green-600 text-white',
  HOLD: 'bg-yellow-500 text-white',
  SKIP: 'bg-red-600 text-white',
};

export function BuyingGuidanceCard({ guidance, sourcePrice }: BuyingGuidanceCardProps) {
  const formatCurrency = (value: number) =>
    value > 0 ? `$${value.toFixed(2)}` : 'N/A';

  return (
    <div className="bg-white rounded-lg shadow-md p-4 space-y-4">
      {/* Header with Recommendation */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Guide Achat/Vente</h3>
        <div className="flex items-center gap-2">
          <ConfidenceBadge level={guidance.confidence_label} />
          <span
            className={`px-3 py-1 rounded-full text-sm font-bold ${RECOMMENDATION_STYLES[guidance.recommendation]}`}
          >
            {guidance.recommendation === 'BUY' ? 'ACHETER' :
             guidance.recommendation === 'HOLD' ? 'A EVALUER' : 'PASSER'}
          </span>
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-3 gap-4">
        {/* Max Buy Price */}
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <Tooltip content={guidance.explanations.max_buy_price}>
            <div className="text-sm text-gray-600 mb-1">Achete max</div>
          </Tooltip>
          <div className="text-xl font-bold text-blue-700">
            {formatCurrency(guidance.max_buy_price)}
          </div>
        </div>

        {/* Target Sell Price */}
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <Tooltip content={guidance.explanations.target_sell_price}>
            <div className="text-sm text-gray-600 mb-1">Vends cible</div>
          </Tooltip>
          <div className="text-xl font-bold text-green-700">
            {formatCurrency(guidance.target_sell_price)}
          </div>
          <div className="text-xs text-gray-500">{guidance.price_range}</div>
        </div>

        {/* Estimated Profit */}
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <Tooltip content={guidance.explanations.estimated_profit}>
            <div className="text-sm text-gray-600 mb-1">Profit</div>
          </Tooltip>
          <div className="text-xl font-bold text-purple-700">
            {formatCurrency(guidance.estimated_profit)}
          </div>
          <div className="text-xs text-gray-500">
            {(guidance.estimated_roi_pct * 100).toFixed(0)}% ROI
          </div>
        </div>
      </div>

      {/* Secondary Info */}
      <div className="flex items-center justify-between text-sm text-gray-600 pt-2 border-t">
        <Tooltip content={guidance.explanations.estimated_days_to_sell}>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>~{guidance.estimated_days_to_sell}j pour vendre</span>
          </div>
        </Tooltip>
        <Tooltip content={guidance.explanations.confidence}>
          <div className="text-gray-500 italic">
            {guidance.recommendation_reason}
          </div>
        </Tooltip>
      </div>
    </div>
  );
}

export default BuyingGuidanceCard;
```

**Step 2: Commit**

```bash
git add frontend/src/components/product/BuyingGuidanceCard.tsx
git commit -m "feat(product): add BuyingGuidanceCard with clear buy/sell display

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Update ProductScore Type

**Files:**
- Modify: `frontend/src/types/views.ts`

**Step 1: Add buying_guidance to ProductScore**

```typescript
// Add to ProductScore interface in views.ts

  // Buying Guidance (Phase: Textbook UX Simplification)
  buying_guidance?: {
    max_buy_price: number;
    target_sell_price: number;
    estimated_profit: number;
    estimated_roi_pct: number;
    price_range: string;
    estimated_days_to_sell: number;
    recommendation: 'BUY' | 'HOLD' | 'SKIP';
    recommendation_reason: string;
    confidence_label: string;
    explanations: Record<string, string>;
  };
```

**Step 2: Commit**

```bash
git add frontend/src/types/views.ts
git commit -m "feat(types): add buying_guidance to ProductScore type

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Update UnifiedProductTable for Simplified Display

**Files:**
- Modify: `frontend/src/components/unified/UnifiedProductTable.tsx`
- Modify: `frontend/src/components/unified/UnifiedProductRow.tsx`

**Step 1: Simplify table columns**

Replace complex columns with simplified ones:

| Old Column | New Column | Source |
|------------|------------|--------|
| ROI (%) | ROI estime | `buying_guidance.estimated_roi_pct` |
| Current Price | Prix vente | `buying_guidance.target_sell_price` |
| Score | (removed) | - |
| - | Achete max | `buying_guidance.max_buy_price` |
| - | Fiabilite | `buying_guidance.confidence_label` |
| - | Action | `buying_guidance.recommendation` |

**Step 2: Add column header tooltips**

```tsx
// In table headers
<th>
  <Tooltip content="Retour sur investissement base sur le prix median historique">
    ROI estime
  </Tooltip>
</th>
<th>
  <Tooltip content="Prix median des 90 derniers jours">
    Prix vente
  </Tooltip>
</th>
<th>
  <Tooltip content="Prix maximum pour garantir 50% de ROI">
    Achete max
  </Tooltip>
</th>
```

**Step 3: Update row display**

```tsx
// In UnifiedProductRow
<td>
  <ConfidenceBadge level={product.buying_guidance?.confidence_label || 'Incertain'} />
</td>
<td>
  <span className={`px-2 py-1 rounded text-sm font-medium ${
    product.buying_guidance?.recommendation === 'BUY' ? 'bg-green-100 text-green-800' :
    product.buying_guidance?.recommendation === 'HOLD' ? 'bg-yellow-100 text-yellow-800' :
    'bg-red-100 text-red-800'
  }`}>
    {product.buying_guidance?.recommendation === 'BUY' ? 'ACHETER' :
     product.buying_guidance?.recommendation === 'HOLD' ? 'EVALUER' : 'PASSER'}
  </span>
</td>
```

**Step 4: Commit**

```bash
git add frontend/src/components/unified/UnifiedProductTable.tsx frontend/src/components/unified/UnifiedProductRow.tsx
git commit -m "feat(table): simplify product table with buying guidance

- Replace technical columns with user-friendly ones
- Add tooltips explaining each metric
- Show recommendation badges (ACHETER/EVALUER/PASSER)
- Display confidence with color-coded badges

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Final Integration (Task 9-10)

### Task 9: Update All Pages Using UnifiedProductTable

**Files:**
- Modify: `frontend/src/pages/AnalyseManuelle.tsx`
- Modify: `frontend/src/pages/AutoSourcing.tsx`
- Modify: `frontend/src/pages/NicheDiscovery.tsx`

Update feature flags and ensure consistent display across all pages.

**Step 1: Commit**

```bash
git add frontend/src/pages/AnalyseManuelle.tsx frontend/src/pages/AutoSourcing.tsx frontend/src/pages/NicheDiscovery.tsx
git commit -m "feat(pages): update all pages with simplified product display

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Run Full Test Suite & Push

**Step 1: Run backend tests**

```bash
cd backend && python -m pytest tests/ --ignore=tests/audit --ignore=tests/integration -v --tb=short
```

**Step 2: Run frontend build**

```bash
cd frontend && npm run build
```

**Step 3: Commit and push**

```bash
git push origin main
```

---

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| **Prix de vente** | `current_buybox_price` (snapshot) | `target_sell_price` (median 90j) |
| **ROI** | `roi_pct` (ancien calcul) | `estimated_roi_pct` (base median) |
| **Confiance** | Aucune | Badge colore (Fiable/Modere/Incertain) |
| **Guidance** | Aucune | Achete max / Vends cible / Profit |
| **Tooltips** | Aucun | Explication sur chaque colonne |
| **Recommandation** | Badge technique | ACHETER / EVALUER / PASSER |

## Files Created/Modified

**Backend (6 files):**
- `backend/app/services/buying_guidance_service.py` (NEW)
- `backend/tests/services/test_buying_guidance_service.py` (NEW)
- `backend/tests/services/test_unified_analysis_guidance.py` (NEW)
- `backend/tests/api/test_textbook_analysis_guidance.py` (NEW)
- `backend/app/services/unified_analysis.py` (MODIFIED)
- `backend/app/api/v1/routers/textbook_analysis.py` (MODIFIED)

**Frontend (8 files):**
- `frontend/src/components/ui/Tooltip.tsx` (NEW)
- `frontend/src/components/ui/ConfidenceBadge.tsx` (NEW)
- `frontend/src/components/product/BuyingGuidanceCard.tsx` (NEW)
- `frontend/src/types/views.ts` (MODIFIED)
- `frontend/src/components/unified/UnifiedProductTable.tsx` (MODIFIED)
- `frontend/src/components/unified/UnifiedProductRow.tsx` (MODIFIED)
- `frontend/src/pages/AnalyseManuelle.tsx` (MODIFIED)
- `frontend/src/pages/AutoSourcing.tsx` (MODIFIED)
