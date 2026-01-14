# Buying Guidance - Views.py Integration Fix

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix empty buying guidance columns in Analyse Manuelle and AutoSourcing by adding the missing `buying_guidance` field to the `ProductScore` Pydantic schema.

**Architecture:** The backend `unified_analysis.py` already calculates and returns `buying_guidance` (line 701), but the Pydantic schema `ProductScore` in `views.py` (lines 73-135) does NOT include this field. Pydantic automatically excludes undeclared fields, causing the data to be filtered out.

**Tech Stack:** FastAPI, Pydantic, TypeScript (frontend already ready)

---

## Task 1: Add buying_guidance Field to ProductScore Schema

**Files:**
- Modify: `backend/app/api/v1/routers/views.py:125-135` (after `pricing` field)

**Step 1: Add the missing field**

Add the following field to `ProductScore` class, after the `pricing` field (around line 128):

```python
    # Buying Guidance (Textbook UX Simplification)
    buying_guidance: Optional[Dict[str, Any]] = Field(
        None,
        description="User-friendly buying guidance with max buy price, target sell price, ROI, and recommendations"
    )
```

**Step 2: Verify the import Dict, Any is already present**

Check line 10 - should already have: `from typing import List, Optional, Dict, Any`

**Step 3: Run backend tests**

Run: `cd backend && pytest tests/api/ -v -k "views" --tb=short`
Expected: All tests pass (existing behavior unchanged, new field is Optional)

**Step 4: Commit**

```bash
git add backend/app/api/v1/routers/views.py
git commit -m "feat(api): add buying_guidance field to ProductScore schema

Fixes empty buying guidance columns in Analyse Manuelle and AutoSourcing.
The field was already calculated in unified_analysis.py but filtered out
by Pydantic because it wasn't declared in the response schema.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Verify API Response Contains buying_guidance

**Files:**
- Test: API endpoint `/api/v1/views/mes_niches`

**Step 1: Start backend locally (or use production API)**

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Or use production: `https://arbitragevault-backend-v2.onrender.com`

**Step 2: Test API with curl**

```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/views/mes_niches" \
  -H "Content-Type: application/json" \
  -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \
  -d '{"identifiers":["0593655036"],"strategy":"textbook"}' | jq '.products[0].buying_guidance'
```

Expected output:
```json
{
  "max_buy_price": 12.50,
  "target_sell_price": 24.99,
  "estimated_profit": 5.25,
  "estimated_roi_pct": 50.0,
  "recommendation": "BUY",
  "confidence_label": "HIGH",
  "explanations": {...}
}
```

**Step 3: Verify frontend displays data**

```bash
cd frontend
npm run dev
```

Navigate to Analyse Manuelle, enter ASIN `0593655036`, verify columns show:
- Achete max: value (not "-")
- Vends cible: value (not "-")
- ROI: percentage (not "-")
- Fiabilite: badge (not "-")
- Action: recommendation badge (not "-")

---

## Task 3: Deploy and Validate Production

**Step 1: Push to main**

```bash
git push origin main
```

**Step 2: Monitor Render deployment**

Wait for deployment to complete on Render dashboard.

**Step 3: Verify production API**

```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/views/mes_niches" \
  -H "Content-Type: application/json" \
  -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \
  -d '{"identifiers":["0593655036"]}' | jq '.products[0].buying_guidance'
```

Expected: Same output as Step 2 above.

**Step 4: Verify Netlify frontend (production)**

Navigate to production frontend, test Analyse Manuelle with same ASIN.

---

## Summary

| Task | Action | Validation |
|------|--------|------------|
| 1 | Add `buying_guidance` to `ProductScore` schema | Tests pass |
| 2 | Verify API returns data | curl + frontend check |
| 3 | Deploy and validate production | Production API + Netlify |

**Root Cause:** Pydantic schema was missing the `buying_guidance` field declaration, causing the data to be silently excluded from API responses.

**Fix:** Single-line addition to `views.py` ProductScore class.
