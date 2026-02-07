# Phase 2D - Daily Review Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Daily Review card on the dashboard that classifies AutoSourcing picks into 5 categories (STABLE, JACKPOT, REVENANT, FLUKE, REJECT) and surfaces actionable daily summaries.

**Architecture:** Backend classification service consumes existing AutoSourcing picks + ASINHistory data to produce daily reviews. A new API endpoint serves the review. Frontend adds a DailyReviewCard component to the existing Dashboard, following the established KpiCard/ActionCard patterns.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, React, TypeScript, TanStack Query, Tailwind CSS (Vault Elegance design system)

---

## Scope

### In Scope
- Backend: Classification service with 5 categories
- Backend: Pydantic schemas for DailyReview
- Backend: API endpoint `GET /api/v1/daily-review/today`
- Frontend: DailyReviewCard dashboard component
- Frontend: Hook for data fetching
- Tests: Unit tests for classification logic

### Out of Scope (Future Phases)
- N8N email automation (Phase 14)
- Dedicated Daily Review page (full page, not just dashboard card)
- Database persistence of reviews (computed on-the-fly for now)
- Historical review comparison (day-over-day trends)

---

## Classification Rules

| Category | Criteria | Color | Action |
|----------|----------|-------|--------|
| STABLE | Seen 2+ times in ASINHistory, ROI 15-80%, BSR > 0, no Amazon seller | Green | Achat recommande |
| JACKPOT | ROI > 80%, BSR > 0 | Yellow/Gold | Verification manuelle |
| REVENANT | ASIN seen in ASINHistory 24h+ ago, reappears today | Blue | Pattern a surveiller |
| FLUKE | Seen only once, OR BSR=-1, OR price=0 | Gray | Ignorer |
| REJECT | Amazon on listing, OR ROI < 0, OR BSR=-1 with no offers | Red | A eviter |

**Priority order:** REJECT > FLUKE > JACKPOT > REVENANT > STABLE (first match wins)

---

## Task 1: Classification Service - Core Logic

**Files:**
- Create: `backend/app/services/daily_review_service.py`
- Test: `backend/tests/services/test_daily_review_service.py`

### Step 1: Write the failing tests

```python
# backend/tests/services/test_daily_review_service.py
import pytest
from datetime import datetime, timezone, timedelta
from app.services.daily_review_service import classify_product, Classification


class TestClassifyProduct:
    """Unit tests for product classification logic."""

    def test_reject_amazon_seller(self):
        product = make_pick(roi=30.0, bsr=500, amazon_on_listing=True)
        result = classify_product(product, history=[])
        assert result == Classification.REJECT

    def test_reject_negative_roi(self):
        product = make_pick(roi=-5.0, bsr=500, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.REJECT

    def test_fluke_no_history(self):
        product = make_pick(roi=30.0, bsr=500, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.FLUKE

    def test_fluke_bad_bsr(self):
        product = make_pick(roi=30.0, bsr=-1, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=48)])
        assert result == Classification.REJECT

    def test_jackpot_high_roi(self):
        product = make_pick(roi=95.0, bsr=200, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=48)])
        assert result == Classification.JACKPOT

    def test_revenant_returns_after_gap(self):
        product = make_pick(roi=35.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=72)]  # Last seen 3 days ago
        result = classify_product(product, history=history)
        assert result == Classification.REVENANT

    def test_stable_consistent(self):
        product = make_pick(roi=40.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.STABLE

    def test_stable_roi_boundary_15(self):
        product = make_pick(roi=15.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.STABLE

    def test_jackpot_roi_boundary_80(self):
        product = make_pick(roi=80.1, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12)]
        result = classify_product(product, history=history)
        assert result == Classification.JACKPOT


def make_pick(roi: float, bsr: int, amazon_on_listing: bool) -> dict:
    return {
        "asin": "0593655036",
        "title": "Test Book",
        "roi_percentage": roi,
        "bsr": bsr,
        "amazon_on_listing": amazon_on_listing,
        "current_price": 15.99,
        "buy_price": 8.99,
    }


def make_history(hours_ago: float) -> dict:
    return {
        "tracked_at": datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        "bsr": 300,
        "price": 15.99,
    }
```

### Step 2: Run tests to verify they fail

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder && python -m pytest backend/tests/services/test_daily_review_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.daily_review_service'`

### Step 3: Write the classification service

```python
# backend/app/services/daily_review_service.py
"""
Daily Review Service - Product classification engine.
Classifies AutoSourcing picks into actionable categories.
"""
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Classification(str, Enum):
    STABLE = "STABLE"
    JACKPOT = "JACKPOT"
    REVENANT = "REVENANT"
    FLUKE = "FLUKE"
    REJECT = "REJECT"


CLASSIFICATION_META = {
    Classification.STABLE: {
        "label": "Opportunite fiable",
        "action": "Achat recommande",
        "color": "green",
    },
    Classification.JACKPOT: {
        "label": "ROI exceptionnel",
        "action": "Verification manuelle requise",
        "color": "yellow",
    },
    Classification.REVENANT: {
        "label": "Produit de retour",
        "action": "Pattern a surveiller",
        "color": "blue",
    },
    Classification.FLUKE: {
        "label": "Donnees suspectes",
        "action": "Ignorer",
        "color": "gray",
    },
    Classification.REJECT: {
        "label": "A eviter",
        "action": "Ne pas acheter",
        "color": "red",
    },
}

# Thresholds
JACKPOT_ROI_THRESHOLD = 80.0
STABLE_MIN_ROI = 15.0
REVENANT_GAP_HOURS = 24
MIN_HISTORY_FOR_STABLE = 2


def classify_product(
    product: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Classification:
    """
    Classify a product based on its metrics and history.
    Priority: REJECT > FLUKE > JACKPOT > REVENANT > STABLE
    """
    roi = product.get("roi_percentage", 0.0) or 0.0
    bsr = product.get("bsr", -1) or -1
    amazon = product.get("amazon_on_listing", False)

    # --- REJECT ---
    if amazon:
        return Classification.REJECT
    if roi < 0:
        return Classification.REJECT
    if bsr <= 0:
        return Classification.REJECT

    # --- FLUKE (no history = never seen before) ---
    if not history:
        return Classification.FLUKE

    # --- JACKPOT ---
    if roi > JACKPOT_ROI_THRESHOLD:
        return Classification.JACKPOT

    # --- REVENANT (last seen 24h+ ago) ---
    most_recent = max(history, key=lambda h: h["tracked_at"])
    gap = datetime.now(timezone.utc) - most_recent["tracked_at"]
    if gap > timedelta(hours=REVENANT_GAP_HOURS):
        return Classification.REVENANT

    # --- STABLE (2+ sightings, decent ROI) ---
    if len(history) >= MIN_HISTORY_FOR_STABLE and roi >= STABLE_MIN_ROI:
        return Classification.STABLE

    # Default: FLUKE (not enough evidence)
    return Classification.FLUKE
```

### Step 4: Run tests to verify they pass

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder && python -m pytest backend/tests/services/test_daily_review_service.py -v`
Expected: 9 PASSED

### Step 5: Commit

```bash
git add backend/app/services/daily_review_service.py backend/tests/services/test_daily_review_service.py
git commit -m "feat(phase-2d): add classification engine with 5 categories + tests"
```

---

## Task 2: Daily Review Generator - Aggregate Picks into Review

**Files:**
- Modify: `backend/app/services/daily_review_service.py`
- Test: `backend/tests/services/test_daily_review_service.py` (add tests)

### Step 1: Write the failing tests

```python
# Add to test_daily_review_service.py

class TestGenerateDailyReview:
    """Tests for the review generator."""

    def test_empty_picks_returns_empty_review(self):
        review = generate_daily_review(picks=[], history_map={})
        assert review["total"] == 0
        assert review["counts"] == {
            "STABLE": 0, "JACKPOT": 0, "REVENANT": 0, "FLUKE": 0, "REJECT": 0
        }
        assert review["top_opportunities"] == []

    def test_mixed_picks_classified_correctly(self):
        picks = [
            make_pick(roi=40.0, bsr=300, amazon_on_listing=False),  # Will be STABLE (with history)
            make_pick(roi=95.0, bsr=200, amazon_on_listing=False),  # Will be JACKPOT (with history)
            make_pick(roi=30.0, bsr=500, amazon_on_listing=True),   # Will be REJECT
        ]
        picks[0]["asin"] = "ASIN001"
        picks[1]["asin"] = "ASIN002"
        picks[2]["asin"] = "ASIN003"

        history_map = {
            "ASIN001": [make_history(12), make_history(36)],
            "ASIN002": [make_history(48)],
            "ASIN003": [],
        }
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert review["total"] == 3
        assert review["counts"]["STABLE"] == 1
        assert review["counts"]["JACKPOT"] == 1
        assert review["counts"]["REJECT"] == 1

    def test_top_opportunities_sorted_by_roi(self):
        picks = [
            make_pick(roi=30.0, bsr=300, amazon_on_listing=False),
            make_pick(roi=60.0, bsr=200, amazon_on_listing=False),
            make_pick(roi=45.0, bsr=250, amazon_on_listing=False),
        ]
        for i, p in enumerate(picks):
            p["asin"] = f"ASIN{i:03d}"

        history_map = {p["asin"]: [make_history(12), make_history(36)] for p in picks}
        review = generate_daily_review(picks=picks, history_map=history_map)
        rois = [opp["roi_percentage"] for opp in review["top_opportunities"]]
        assert rois == sorted(rois, reverse=True)

    def test_top_opportunities_max_3(self):
        picks = [make_pick(roi=30 + i, bsr=300, amazon_on_listing=False) for i in range(10)]
        for i, p in enumerate(picks):
            p["asin"] = f"ASIN{i:03d}"
        history_map = {p["asin"]: [make_history(12), make_history(36)] for p in picks}
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert len(review["top_opportunities"]) <= 3

    def test_summary_text_generated(self):
        picks = [make_pick(roi=40.0, bsr=300, amazon_on_listing=False)]
        picks[0]["asin"] = "ASIN001"
        history_map = {"ASIN001": [make_history(12), make_history(36)]}
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert isinstance(review["summary"], str)
        assert len(review["summary"]) > 0
```

### Step 2: Run tests to confirm failure

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder && python -m pytest backend/tests/services/test_daily_review_service.py::TestGenerateDailyReview -v`
Expected: FAIL with `ImportError: cannot import name 'generate_daily_review'`

### Step 3: Implement generate_daily_review

```python
# Add to daily_review_service.py

def generate_daily_review(
    picks: List[Dict[str, Any]],
    history_map: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Generate a daily review from a list of AutoSourcing picks.
    Returns classified products, counts, top opportunities, and summary.
    """
    classified: List[Dict[str, Any]] = []
    counts = {c.value: 0 for c in Classification}

    for pick in picks:
        asin = pick.get("asin", "")
        history = history_map.get(asin, [])
        category = classify_product(pick, history)
        counts[category.value] += 1
        meta = CLASSIFICATION_META[category]
        classified.append({
            **pick,
            "classification": category.value,
            "classification_label": meta["label"],
            "classification_action": meta["action"],
            "classification_color": meta["color"],
        })

    # Top opportunities: non-REJECT, non-FLUKE, sorted by ROI desc, max 3
    actionable = [
        p for p in classified
        if p["classification"] not in (Classification.REJECT.value, Classification.FLUKE.value)
    ]
    top_opportunities = sorted(
        actionable, key=lambda p: p.get("roi_percentage", 0), reverse=True
    )[:3]

    # Summary
    buy_count = counts[Classification.STABLE.value]
    jackpot_count = counts[Classification.JACKPOT.value]
    reject_count = counts[Classification.REJECT.value]
    avg_roi = 0.0
    if actionable:
        avg_roi = sum(p.get("roi_percentage", 0) for p in actionable) / len(actionable)

    parts = []
    if buy_count > 0:
        parts.append(f"{buy_count} achat(s) recommande(s)")
    if jackpot_count > 0:
        parts.append(f"{jackpot_count} jackpot(s) a verifier")
    if reject_count > 0:
        parts.append(f"{reject_count} rejete(s)")
    if avg_roi > 0:
        parts.append(f"ROI moyen {avg_roi:.1f}%")

    summary = ". ".join(parts) if parts else "Aucune opportunite aujourd'hui."

    return {
        "review_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total": len(picks),
        "counts": counts,
        "classified_products": classified,
        "top_opportunities": top_opportunities,
        "summary": summary,
    }
```

### Step 4: Run tests

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder && python -m pytest backend/tests/services/test_daily_review_service.py -v`
Expected: 14 PASSED

### Step 5: Commit

```bash
git add backend/app/services/daily_review_service.py backend/tests/services/test_daily_review_service.py
git commit -m "feat(phase-2d): add review generator with summary and top opportunities"
```

---

## Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/daily_review.py`

### Step 1: Write schemas

```python
# backend/app/schemas/daily_review.py
"""Pydantic schemas for Daily Review API responses."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ClassifiedProductResponse(BaseModel):
    asin: str
    title: str = ""
    roi_percentage: float = 0.0
    bsr: int = 0
    current_price: Optional[float] = None
    buy_price: Optional[float] = None
    amazon_on_listing: bool = False
    classification: str
    classification_label: str
    classification_action: str
    classification_color: str

    class Config:
        from_attributes = True


class DailyReviewCounts(BaseModel):
    STABLE: int = 0
    JACKPOT: int = 0
    REVENANT: int = 0
    FLUKE: int = 0
    REJECT: int = 0


class DailyReviewResponse(BaseModel):
    review_date: str
    total: int = 0
    counts: DailyReviewCounts
    top_opportunities: List[ClassifiedProductResponse] = Field(default_factory=list)
    summary: str = ""

    class Config:
        from_attributes = True
```

### Step 2: Commit

```bash
git add backend/app/schemas/daily_review.py
git commit -m "feat(phase-2d): add Pydantic schemas for Daily Review API"
```

---

## Task 4: API Endpoint

**Files:**
- Create: `backend/app/api/v1/routers/daily_review.py`
- Modify: `backend/app/api/v1/router.py` (register the new router)

### Step 1: Write the endpoint

```python
# backend/app/api/v1/routers/daily_review.py
"""Daily Review API - Serves classified product reviews."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.deps import get_db, get_current_user
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob, ActionStatus
from app.models.analytics import ASINHistory
from app.schemas.daily_review import DailyReviewResponse
from app.services.daily_review_service import generate_daily_review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-review", tags=["daily-review"])


@router.get("/today", response_model=DailyReviewResponse)
async def get_daily_review(
    days_back: int = Query(default=1, ge=1, le=7, description="Days of picks to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate today's daily review from recent AutoSourcing picks.
    Classifies products and returns actionable summary.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    # Fetch recent picks (non-ignored) from AutoSourcing jobs
    picks_query = (
        select(AutoSourcingPick)
        .join(AutoSourcingJob)
        .where(
            and_(
                AutoSourcingJob.created_at >= cutoff,
                AutoSourcingPick.action != ActionStatus.IGNORED,
            )
        )
    )
    result = await db.execute(picks_query)
    picks_rows = result.scalars().all()

    # Convert to dicts for classification
    picks = []
    asin_set = set()
    for pick in picks_rows:
        asin_set.add(pick.asin)
        picks.append({
            "asin": pick.asin,
            "title": pick.title or "",
            "roi_percentage": float(pick.roi_percentage or 0),
            "bsr": int(pick.bsr or -1),
            "amazon_on_listing": bool(pick.amazon_on_listing),
            "current_price": float(pick.sell_price) if pick.sell_price else None,
            "buy_price": float(pick.buy_price) if pick.buy_price else None,
        })

    # Fetch history for all ASINs in one query
    history_map = {}
    if asin_set:
        history_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        history_query = (
            select(ASINHistory)
            .where(
                and_(
                    ASINHistory.asin.in_(asin_set),
                    ASINHistory.tracked_at >= history_cutoff,
                )
            )
        )
        hist_result = await db.execute(history_query)
        for row in hist_result.scalars().all():
            history_map.setdefault(row.asin, []).append({
                "tracked_at": row.tracked_at,
                "bsr": row.bsr,
                "price": float(row.price) if row.price else None,
            })

    review = generate_daily_review(picks=picks, history_map=history_map)
    return DailyReviewResponse(**review)
```

### Step 2: Register the router

Find the main v1 router file and add the daily_review router import.
Look at: `backend/app/api/v1/router.py`
Add: `from app.api.v1.routers.daily_review import router as daily_review_router`
Add: `api_router.include_router(daily_review_router)`

### Step 3: Run backend to verify endpoint loads

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder/backend && timeout 10 python -m uvicorn app.main:app --port 8001 2>&1 | head -20`
Expected: Server starts without import errors

### Step 4: Commit

```bash
git add backend/app/api/v1/routers/daily_review.py backend/app/api/v1/router.py backend/app/schemas/daily_review.py
git commit -m "feat(phase-2d): add GET /daily-review/today endpoint"
```

---

## Task 5: Frontend - DailyReviewCard Component

**Files:**
- Create: `frontend/src/components/vault/DailyReviewCard.tsx`
- Modify: `frontend/src/hooks/useDashboardData.ts` (add daily review fetch)
- Modify: `frontend/src/components/Dashboard/Dashboard.tsx` (add card)

### Step 1: Add API call to useDashboardData.ts

Add a new fetch function and include it in the Promise.all:

```typescript
// Add to useDashboardData.ts types
interface DailyReviewData {
  review_date: string
  total: number
  counts: {
    STABLE: number
    JACKPOT: number
    REVENANT: number
    FLUKE: number
    REJECT: number
  }
  top_opportunities: Array<{
    asin: string
    title: string
    roi_percentage: number
    classification: string
    classification_label: string
    classification_color: string
  }>
  summary: string
}

// Add fetch function
async function fetchDailyReview(): Promise<DailyReviewData | null> {
  try {
    const response = await api.get('/api/v1/daily-review/today')
    return response.data
  } catch (error) {
    console.warn('[Dashboard] Daily review not available:', error)
    return null
  }
}

// Add to Promise.all in fetchDashboardData
// Add dailyReview to return object
// Add to hook return value
```

### Step 2: Create DailyReviewCard component

```tsx
// frontend/src/components/vault/DailyReviewCard.tsx
// Classification badge colors, summary display, top 3 opportunities list
// Follows Vault Elegance design: rounded-vault-sm, vault-card bg, vault-text colors
// Mobile-first: single column on mobile, adapts on desktop
```

Key elements:
- Title: "Daily Review" with date
- Summary text (from API)
- Classification badges (color-coded pills: STABLE=green, JACKPOT=yellow, etc.)
- Count indicators per category
- Top 3 opportunities mini-list with ASIN, ROI%, classification badge
- Empty state when no picks available
- Loading skeleton matching card size

### Step 3: Add to Dashboard.tsx

Insert DailyReviewCard as a new section between KPI Cards and Action Cards:
```tsx
{/* DAILY REVIEW */}
<section>
  <DailyReviewCard review={dailyReview} isLoading={isLoading} />
</section>
```

### Step 4: Verify build

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder/frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

### Step 5: Commit

```bash
git add frontend/src/components/vault/DailyReviewCard.tsx frontend/src/hooks/useDashboardData.ts frontend/src/components/Dashboard/Dashboard.tsx
git commit -m "feat(phase-2d): add DailyReviewCard to dashboard with real data"
```

---

## Task 6: Update Documentation & Memory

**Files:**
- Modify: `frontend/src/pages/docs/DailyReviewDocs.tsx` (update roadmap status)
- Modify: `.claude/compact_current.md` (mark Phase 2D complete)

### Step 1: Update DailyReviewDocs.tsx roadmap

Change Phase 2 (Backend Integration) from yellow to green, Phase 4 (Frontend Page) from gray to green.

### Step 2: Update compact_current.md

Mark Phase 2D as complete in the changelog and next actions.

### Step 3: Commit

```bash
git add frontend/src/pages/docs/DailyReviewDocs.tsx .claude/compact_current.md
git commit -m "docs(phase-2d): update roadmap and project memory"
```

---

## Task 7: Integration Test & Senior Review

### Step 1: Run all backend tests

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder/backend && python -m pytest tests/ -v --tb=short -q`
Expected: All existing tests + new tests pass (760+ total)

### Step 2: Run frontend build

Run: `cd /Users/clawdbot/Workspace/arbitragevault_bookfinder/frontend && npm run build`
Expected: Build succeeds

### Step 3: Playwright test (if production deployed)

Visual validation of the dashboard with the new DailyReviewCard.
- Desktop viewport (1920x1080)
- Mobile viewport (375x812)

### Step 4: Senior Review Gate

Answer the 5 questions:
1. Gaps dans la couverture de tests? -> Classification logic 100% covered
2. Services combines = resultats absurdes? -> Verify REJECT priority over JACKPOT
3. Seuils hardcodes documentes? -> ROI 80% JACKPOT, 15% STABLE min, 24h REVENANT gap
4. Frontend teste? -> Build + Playwright
5. Edge cases? -> Empty picks, all REJECT, no history, single pick

---

## Summary

| Task | Description | Estimated Steps |
|------|-------------|----------------|
| 1 | Classification engine + tests | 5 |
| 2 | Review generator + tests | 5 |
| 3 | Pydantic schemas | 2 |
| 4 | API endpoint + router registration | 4 |
| 5 | Frontend card + hook + dashboard integration | 5 |
| 6 | Documentation updates | 3 |
| 7 | Integration test + Senior Review | 4 |
| **Total** | | **28 steps, 7 commits** |

---

## Dependencies Between Tasks

```
Task 1 (Classification) --> Task 2 (Generator) --> Task 4 (API)
                                                      |
Task 3 (Schemas) ---------------------------------> Task 4
                                                      |
                                                      v
                                               Task 5 (Frontend)
                                                      |
                                                      v
                                               Task 6 (Docs)
                                                      |
                                                      v
                                               Task 7 (Review)
```

Tasks 1 and 3 can run in parallel. All others are sequential.
