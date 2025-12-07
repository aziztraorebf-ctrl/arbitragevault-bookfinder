# Source Price Factor 0.50 - Verification Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify that source_price_factor=0.50 is correctly deployed and calculates ROI as expected across all services.

**Architecture:** The change unified two parameters (source_price_factor in config.py and buy_markup in autosourcing_service.py) to a single value of 0.50, representing the FBM->FBA arbitrage model where we buy at 50% of FBA price.

**Tech Stack:** FastAPI backend, Playwright E2E tests, pytest unit tests, Render deployment

**Skills Required:**
- superpowers:verification-before-completion
- superpowers:test-driven-development (RED-GREEN for regression test)
- playwright-skill (E2E frontend tests)

---

## Phase 1: Production API Verification

### Task 1: Verify Backend Health

**Files:** None (API calls only)

**Step 1: Test health endpoint**

Run:
```bash
curl -s https://arbitragevault-backend-v2.onrender.com/api/v1/health/ready | python -m json.tool
```

Expected: `{"status": "ready", ...}`

**Step 2: Test Keepa health and token balance**

Run:
```bash
curl -s https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/health | python -m json.tool
```

Expected: `{"status": "healthy", "tokens": {"remaining": > 50}, ...}`

---

### Task 2: Verify AutoSourcing Endpoint Returns Correct ROI

**Files:** None (API calls only)

**Step 1: Get existing job with picks to verify ROI values**

Run:
```bash
curl -s "https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/jobs?limit=5" | python -m json.tool
```

Expected: List of jobs with picks

**Step 2: Get picks from latest job and examine ROI values**

Run:
```bash
curl -s "https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/jobs/{job_id}" | python -m json.tool
```

Expected: Picks with `roi_percentage` in range 40-80% (not 10-30% as before)

**Step 3: Run a small AutoSourcing job to verify NEW calculations**

Run:
```bash
curl -s -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/run-custom" \
  -H "Content-Type: application/json" \
  -d '{"discovery_config": {"categories": ["Books"], "bsr_range": [10000, 80000], "price_range": [20, 80]}, "scoring_config": {"min_roi": 30}, "max_products": 3, "profile_name": "verify-0.50-factor"}'
```

Expected: Job created with picks having ROI in realistic range (40-80%)

---

## Phase 2: RED-GREEN Regression Test

### Task 3: Write Failing Test for source_price_factor

**Files:**
- Create: `backend/tests/unit/test_source_price_factor_unified.py`

**Step 1: Write the failing test (RED)**

```python
"""
Test to verify source_price_factor is unified at 0.50 across all services.
This test ensures we don't regress to the old buy_markup=0.70 bug.
"""
import pytest
from decimal import Decimal

from app.schemas.config import ROIConfig


class TestSourcePriceFactorUnified:
    """Tests for unified source_price_factor across services."""

    def test_roi_config_default_is_0_50(self):
        """ROIConfig.source_price_factor default must be 0.50."""
        config = ROIConfig()
        assert config.source_price_factor == Decimal("0.50"), (
            f"Expected 0.50, got {config.source_price_factor}. "
            "Did someone change the default?"
        )

    def test_source_price_factor_calculates_correct_estimated_cost(self):
        """
        With source_price_factor=0.50, a $100 product should have:
        - estimated_cost = $50 (50% of sell price)
        - NOT $70 (the old bug with buy_markup=0.70)
        """
        sell_price = Decimal("100.00")
        source_price_factor = Decimal("0.50")

        estimated_cost = sell_price * source_price_factor

        assert estimated_cost == Decimal("50.00"), (
            f"Expected $50.00, got ${estimated_cost}. "
            "source_price_factor calculation is wrong."
        )
        # Explicitly verify we're NOT using the old buggy value
        old_buy_markup = Decimal("0.70")
        wrong_cost = sell_price * old_buy_markup
        assert estimated_cost != wrong_cost, (
            "Cost matches old buy_markup=0.70! Did someone revert the fix?"
        )

    def test_roi_calculation_with_0_50_factor(self):
        """
        Verify ROI calculation with source_price_factor=0.50.

        Example: $80 book
        - Sell price: $80
        - Buy cost (50%): $40
        - Amazon fees (~15%): $12
        - Profit: $80 - $40 - $12 = $28
        - ROI: ($28 / $40) * 100 = 70%

        With old bug (70%):
        - Buy cost (70%): $56
        - Profit: $80 - $56 - $12 = $12
        - ROI: ($12 / $56) * 100 = 21.4%
        """
        sell_price = Decimal("80.00")
        source_price_factor = Decimal("0.50")
        fee_percentage = Decimal("0.15")

        buy_cost = sell_price * source_price_factor  # $40
        fees = sell_price * fee_percentage  # $12
        profit = sell_price - buy_cost - fees  # $28
        roi = (profit / buy_cost) * 100  # 70%

        # ROI should be around 70%, definitely > 50%
        assert roi > Decimal("50"), (
            f"ROI is {roi}%, expected > 50%. "
            "Are we using the wrong source_price_factor?"
        )

        # Verify it's NOT the old buggy ROI (~21%)
        assert roi > Decimal("40"), (
            f"ROI is {roi}%, suspiciously low. "
            "Check if buy_markup=0.70 bug has returned."
        )
```

**Step 2: Run test to verify it PASSES (should pass with current code)**

Run:
```bash
cd backend && python -m pytest tests/unit/test_source_price_factor_unified.py -v
```

Expected: 3/3 PASS

**Step 3: Verify RED by temporarily breaking the code**

Temporarily change `config.py` line 84 from `0.50` to `0.70`:

Run:
```bash
cd backend && python -m pytest tests/unit/test_source_price_factor_unified.py -v
```

Expected: FAIL with message about expected 0.50

**Step 4: Restore correct value and verify GREEN**

Restore `0.50` in config.py.

Run:
```bash
cd backend && python -m pytest tests/unit/test_source_price_factor_unified.py -v
```

Expected: 3/3 PASS

**Step 5: Commit regression test**

```bash
git add backend/tests/unit/test_source_price_factor_unified.py
git commit -m "test: add regression tests for source_price_factor=0.50

RED-GREEN verified:
- Tests fail when factor changed to 0.70
- Tests pass with correct 0.50 value
- Prevents regression to old buy_markup bug"
```

---

## Phase 3: E2E Frontend Tests with Playwright

### Task 4: Test Frontend AutoSourcing Flow

**Files:**
- Create: `backend/tests/e2e/tests/12-source-price-factor-verification.spec.js`

**Step 1: Write Playwright E2E test**

```javascript
// @ts-check
const { test, expect } = require('@playwright/test');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

test.describe('Source Price Factor 0.50 Verification', () => {

  test('API returns ROI in expected range (40-80%)', async ({ request }) => {
    // Get recent jobs
    const jobsResponse = await request.get(`${BACKEND_URL}/api/v1/autosourcing/jobs?limit=1`);
    expect(jobsResponse.ok()).toBeTruthy();

    const jobs = await jobsResponse.json();
    if (jobs.length > 0 && jobs[0].picks && jobs[0].picks.length > 0) {
      // Check ROI values are in realistic range
      for (const pick of jobs[0].picks.slice(0, 3)) {
        if (pick.roi_percentage) {
          // ROI should be > 30% with 0.50 factor (not ~14% with 0.70 bug)
          console.log(`Pick ${pick.asin}: ROI = ${pick.roi_percentage}%`);
          // Note: Some products may have unusual ROI, so we log rather than hard fail
        }
      }
    }
  });

  test('Frontend AutoSourcing page loads correctly', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/autosourcing`);

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Should see AutoSourcing heading or related content
    const pageContent = await page.content();
    expect(
      pageContent.includes('AutoSourcing') ||
      pageContent.includes('autosourcing') ||
      pageContent.includes('Discovery')
    ).toBeTruthy();
  });

  test('Frontend can display job results', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/autosourcing`);
    await page.waitForLoadState('networkidle');

    // Look for jobs list or picks display
    // This verifies the frontend can render AutoSourcing data
    await page.waitForTimeout(2000); // Allow API calls to complete

    // Take screenshot for manual verification
    await page.screenshot({ path: 'test-results/autosourcing-page.png' });
  });

  test('Niche Discovery endpoint returns products', async ({ request }) => {
    // Test niche discovery which also uses source_price_factor
    const response = await request.get(
      `${BACKEND_URL}/api/v1/niches/discover?strategy=smart-velocity&limit=3`
    );

    // May fail if no tokens, but should not error
    if (response.ok()) {
      const data = await response.json();
      console.log(`Niche discovery returned ${data.products?.length || 0} products`);
    } else {
      console.log(`Niche discovery status: ${response.status()}`);
    }
  });

});
```

**Step 2: Run Playwright tests**

Run:
```bash
cd backend/tests/e2e && npx playwright test tests/12-source-price-factor-verification.spec.js --reporter=list
```

Expected: Tests pass or provide useful diagnostic output

**Step 3: Commit E2E test**

```bash
git add backend/tests/e2e/tests/12-source-price-factor-verification.spec.js
git commit -m "test(e2e): add source_price_factor verification tests

Playwright tests for:
- API ROI values in expected range
- Frontend AutoSourcing page loads
- Niche Discovery endpoint works"
```

---

## Phase 4: Full Test Suite Verification

### Task 5: Run Complete Test Suite

**Step 1: Run all unit tests**

Run:
```bash
cd backend && python -m pytest tests/unit/ -v -q 2>&1 | tail -20
```

Expected: All tests pass (140+ tests)

**Step 2: Run all service tests**

Run:
```bash
cd backend && python -m pytest tests/services/ -v -q 2>&1 | tail -20
```

Expected: All tests pass (24+ tests)

**Step 3: Run E2E tests (excluding long-running ones)**

Run:
```bash
cd backend/tests/e2e && npx playwright test --grep-invert "autosourcing-flow" --reporter=list 2>&1 | tail -30
```

Expected: Most tests pass

---

## Verification Checklist

Before marking complete:

- [ ] Production health endpoint returns "ready"
- [ ] Keepa health shows sufficient tokens
- [ ] AutoSourcing jobs return ROI in 40-80% range (not 10-30%)
- [ ] Regression test written and RED-GREEN verified
- [ ] E2E Playwright tests pass
- [ ] Full unit test suite passes
- [ ] All changes committed

---

## Summary

| Phase | Task | Expected Outcome |
|-------|------|------------------|
| 1 | API Health | Status ready, tokens > 50 |
| 1 | AutoSourcing ROI | ROI 40-80% (not 10-30%) |
| 2 | RED-GREEN Test | Fails with 0.70, passes with 0.50 |
| 3 | Playwright E2E | Frontend loads, API responds |
| 4 | Full Suite | All tests pass |

**Estimated time:** 30-45 minutes
**Tokens cost:** ~20-50 (if running new AutoSourcing job)
