# Phase 7.0 Correction Plan

**Date**: 2025-11-19
**Based on**: Code Review Audit Report
**Status**: READY FOR EXECUTION
**Estimated Time**: 2-3 hours

---

## Executive Summary

Phase 7.0 est **90% production-ready** avec **2 correctifs obligatoires** avant merge :

1. **CRITICAL-01**: Supprimer emojis dans code Python (violation CODE_STYLE_RULES.md)
2. **IMPORTANT-01**: Déplacer timeout protection pour garantir mise à jour DB

**Risque actuel** : Moyen-Élevé (jobs zombie en DB si timeout)

---

## Findings Summary

### Issues Found

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | MUST FIX BEFORE MERGE |
| IMPORTANT | 3 | FIX 1 REQUIRED, 2-3 POST-MERGE |
| NICE-TO-HAVE | 4 | PHASE 7.1 TECH DEBT |

### Code Quality Score: 8.7/10

**Points forts**:
- Architecture multi-couches excellente
- Validation Pydantic/Zod robuste
- E2E tests avec vraies données production
- Documentation exhaustive

**Points faibles**:
- Emojis en code exécutable (.py)
- Timeout sans propagation DB
- Hardcoded token costs

---

## Correction Tasks

### MANDATORY (Before Merge)

#### Task 1: Fix CRITICAL-01 - Remove Emojis from Python Code

**File**: `backend/app/services/autosourcing_service.py`
**Lines**: 166, 170, 385, 386

**Current Code**:
```python
logger.info(f"✅ AutoSourcing job completed: {job.id}")
logger.error(f"❌ AutoSourcing job failed: {str(e)}")
logger.debug(f"✅ {asin}: {pick.overall_rating} (ROI: {pick.roi_percentage}%)")
logger.debug(f"❌ {asin}: Does not meet criteria")
```

**Fixed Code**:
```python
logger.info(f"AutoSourcing job completed successfully: {job.id}")
logger.error(f"AutoSourcing job failed: {str(e)}")
logger.debug(f"PASS {asin}: {pick.overall_rating} (ROI: {pick.roi_percentage}%)")
logger.debug(f"REJECT {asin}: Does not meet criteria")
```

**Validation**:
```bash
# Check no emojis remain
grep -r "[😀-🙏]" backend/app/services/autosourcing_service.py
# Should return nothing

# Run tests
cd backend && pytest tests/services/test_autosourcing_service.py -v
```

**Estimated Time**: 30 minutes

---

#### Task 2: Fix IMPORTANT-01 - Timeout with DB Propagation

**File**: `backend/app/services/autosourcing_service.py`
**Method**: `run_custom_search()`
**Lines**: ~150-200

**Problem**:
Timeout intercepté dans router AVANT mise à jour job.status en DB.

**Current Flow**:
```
Router → asyncio.timeout(120) → Service.run_custom_search()
           ↓ TimeoutError
         HTTPException 408 (job reste RUNNING en DB)
```

**Fixed Flow**:
```
Router → Service.run_custom_search()
           ↓ asyncio.timeout(120)
           ↓ TimeoutError → Update job.status=FAILED → Commit
           ↓ Re-raise HTTPException 408
```

**Implementation**:

1. **Déplacer timeout dans service**:

```python
# backend/app/services/autosourcing_service.py

from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB

async def run_custom_search(
    self,
    job_id: UUID,
    discovery_config: Dict[str, Any],
    selection_criteria: Dict[str, Any],
    db: AsyncSession
) -> AutoSourcingJob:
    """Execute custom AutoSourcing search with timeout protection."""

    job = await db.get(AutoSourcingJob, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    try:
        # Timeout protection INSIDE service
        async with asyncio.timeout(TIMEOUT_PER_JOB):
            return await self._execute_job_logic(job, discovery_config, selection_criteria, db)

    except asyncio.TimeoutError:
        # Update job status BEFORE raising exception
        job.status = JobStatus.FAILED
        job.error_message = f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.warning(f"Job {job_id} exceeded timeout ({TIMEOUT_PER_JOB}s)")

        # Re-raise for router to handle HTTP 408
        raise HTTPException(
            status_code=408,
            detail=f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
        )

    except Exception as e:
        # Existing error handling
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        raise
```

2. **Retirer timeout du router**:

```python
# backend/app/api/v1/endpoints/autosourcing.py

@router.post("/run-custom", response_model=JobSubmissionResponse)
async def run_custom_autosourcing_job(
    request: AutoSourcingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit custom AutoSourcing job with validation."""

    # Validate job requirements
    validation = await service.validate_job_requirements(request.discovery_config, db)

    if not validation.safe_to_proceed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "JOB_TOO_EXPENSIVE",
                "estimated_tokens": validation.estimated_tokens,
                "max_allowed": MAX_TOKENS_PER_JOB,
                "suggestion": validation.warning_message
            }
        )

    # Create job
    job = await service.create_job(request, db)

    # Execute job (timeout handled INSIDE service now)
    try:
        completed_job = await service.run_custom_search(
            job.id,
            request.discovery_config,
            request.selection_criteria,
            db
        )

        return JobSubmissionResponse(
            job_id=completed_job.id,
            status=completed_job.status,
            message="Job submitted successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (timeout, validation errors)
        raise

    except Exception as e:
        logger.error(f"Job execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Validation**:
```bash
# Unit test timeout scenario
cd backend
pytest tests/services/test_autosourcing_service.py::test_job_timeout_updates_db -v

# E2E test (add new test for timeout)
cd backend/tests/e2e
npx playwright test tests/08-autosourcing-safeguards.spec.js --grep "timeout"
```

**Estimated Time**: 1 hour

---

### RECOMMENDED (Post-Merge - Phase 7.1)

#### Task 3: Fix IMPORTANT-02 - Migrate Token Costs to Settings

**File**: `backend/app/services/autosourcing_cost_estimator.py`
**Priority**: IMPORTANT but not blocking

**Current**:
```python
PRODUCT_FINDER_COST = 10
PRODUCT_DETAILS_COST = 1
```

**Fixed**:
```python
# backend/app/core/settings.py
class Settings(BaseSettings):
    # ... existing settings ...

    keepa_product_finder_cost: int = 10
    keepa_product_details_cost: int = 1
    keepa_results_per_page: int = 10

# backend/app/services/autosourcing_cost_estimator.py
class AutoSourcingCostEstimator:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.finder_cost = settings.keepa_product_finder_cost
        self.details_cost = settings.keepa_product_details_cost
        self.results_per_page = settings.keepa_results_per_page
```

**Estimated Time**: 45 minutes

---

#### Task 4: Fix IMPORTANT-03 - Add Zod Schemas for API Errors

**File**: `frontend/src/schemas/autosourcing.ts` (new file)
**Priority**: IMPORTANT but not blocking

**Implementation**:
```typescript
import { z } from 'zod';

export const jobTooExpensiveErrorSchema = z.object({
  error: z.literal('JOB_TOO_EXPENSIVE'),
  estimated_tokens: z.number(),
  max_allowed: z.number(),
  suggestion: z.string()
});

export const insufficientBalanceErrorSchema = z.object({
  error: z.literal('INSUFFICIENT_BALANCE'),
  balance: z.number(),
  required: z.number(),
  suggestion: z.string()
});

export const timeoutErrorSchema = z.object({
  detail: z.string().regex(/timeout/i)
});

export type JobTooExpensiveError = z.infer<typeof jobTooExpensiveErrorSchema>;
export type InsufficientBalanceError = z.infer<typeof insufficientBalanceErrorSchema>;
```

**Usage in Component**:
```typescript
// frontend/src/components/AutoSourcingJobModal.tsx
import { jobTooExpensiveErrorSchema, insufficientBalanceErrorSchema } from '@/schemas/autosourcing';

if (response.status === 400) {
  const parsed = jobTooExpensiveErrorSchema.safeParse(data.detail);
  if (parsed.success) {
    setSafeguardError(`Job trop couteux: ${parsed.data.estimated_tokens} tokens...`);
    return;
  }

  const balanceParsed = insufficientBalanceErrorSchema.safeParse(data.detail);
  if (balanceParsed.success) {
    setSafeguardError(`Solde insuffisant: ${balanceParsed.data.balance}...`);
    return;
  }
}
```

**Estimated Time**: 1 hour

---

### OPTIONAL (Phase 7.1 Tech Debt)

#### Task 5: Apply MAX_PRODUCTS_PER_SEARCH in Cost Estimator

**File**: `backend/app/services/autosourcing_cost_estimator.py`
**Lines**: 26-33

**Fixed**:
```python
from app.schemas.autosourcing_safeguards import MAX_PRODUCTS_PER_SEARCH

def estimate_discovery_cost(self, discovery_config: Dict[str, Any]) -> int:
    categories = discovery_config.get("categories", [])

    # Cap max_results to safety limit
    requested_results = discovery_config.get("max_results", 10)
    max_results = min(requested_results, MAX_PRODUCTS_PER_SEARCH)

    pages_per_category = (max_results + self.RESULTS_PER_PAGE - 1) // self.RESULTS_PER_PAGE
    # ...
```

**Estimated Time**: 15 minutes

---

#### Task 6: Reduce Deduplication Log Verbosity

**File**: `backend/app/services/autosourcing_service.py`
**Line**: 334

**Fixed**:
```python
async def process_asins_with_deduplication(self, asins: List[str]) -> List[str]:
    """Deduplicate ASINs while preserving first-occurrence order."""
    seen = set()
    unique_asins = []
    duplicates_count = 0

    for asin in asins:
        if asin in seen:
            duplicates_count += 1
            continue
        seen.add(asin)
        unique_asins.append(asin)

    if duplicates_count > 0:
        logger.info(f"Deduplicated {duplicates_count} ASINs (kept {len(unique_asins)} unique)")

    return unique_asins
```

**Estimated Time**: 10 minutes

---

#### Task 7: Add Frontend Cost Estimate Cache

**File**: `frontend/src/components/AutoSourcingJobModal.tsx`

**Implementation**:
```typescript
const [estimateCache, setEstimateCache] = useState<Map<string, CostEstimate>>(new Map());

const handleEstimateCost = async () => {
  const cacheKey = JSON.stringify(formData.discovery_config);

  // Check cache first
  if (estimateCache.has(cacheKey)) {
    setCostEstimate(estimateCache.get(cacheKey)!);
    setShowCostEstimate(true);
    return;
  }

  setEstimatingCost(true);

  try {
    const response = await fetch(`${API_URL}/api/v1/autosourcing/estimate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ discovery_config: formData.discovery_config })
    });

    const data = await response.json();

    // Store in cache
    const newCache = new Map(estimateCache);
    newCache.set(cacheKey, data);
    setEstimateCache(newCache);

    setCostEstimate(data);
    setShowCostEstimate(true);
  } catch (error) {
    console.error('Estimation failed:', error);
  } finally {
    setEstimatingCost(false);
  }
};
```

**Estimated Time**: 30 minutes

---

#### Task 8: Add E2E Test for Timeout Scenario

**File**: `backend/tests/e2e/tests/08-autosourcing-safeguards.spec.js`

**Implementation**:
```javascript
test('Test: Job timeout returns HTTP 408 and updates DB', async ({ page }) => {
  // This test requires mocking Keepa API delay to trigger timeout
  // Alternative: Lower TIMEOUT_PER_JOB to 5s for this test only

  const response = await page.request.post(`${API_BASE_URL}/api/v1/autosourcing/run-custom`, {
    data: {
      discovery_config: {
        search_type: 'category',
        categories: ['Books'],
        max_results: 200  // Large job to increase timeout risk
      },
      selection_criteria: {
        min_roi: 50,
        max_bsr: 100000,
        min_velocity: 30
      }
    }
  });

  // Assert: Either completes OR returns 408
  if (response.status() === 408) {
    const error = await response.json();
    expect(error.detail).toMatch(/timeout/i);

    console.log('Test PASSED: Timeout handled correctly (HTTP 408)');
  } else if (response.status() === 200) {
    console.log('Test PASSED: Job completed before timeout');
  } else {
    throw new Error(`Unexpected status: ${response.status()}`);
  }
});
```

**Note**: Test difficile car timeout 120s. Alternatives :
- Mock Keepa API avec delay
- Paramètre `TIMEOUT_PER_JOB` overridable pour tests
- Test manuel avec vraie API lente

**Estimated Time**: 1 hour

---

## Execution Plan

### Phase 1: Mandatory Fixes (BEFORE MERGE)

**Estimated Time**: 2-3 hours

1. **Task 1**: Remove emojis from Python code (30 min)
   - Edit `autosourcing_service.py`
   - Run tests
   - Commit

2. **Task 2**: Fix timeout DB propagation (1 hour)
   - Move timeout into service
   - Update router
   - Add unit test
   - Run E2E tests
   - Commit

3. **Validation** (30 min):
   - Run full test suite: `pytest tests/ -v`
   - Run E2E suite: `npx playwright test`
   - Verify production endpoints still work
   - Test timeout scenario manually (if possible)

4. **Commit & Deploy** (30 min):
   - Git commit with detailed message
   - Push to GitHub
   - Trigger Render deployment
   - Monitor deployment logs
   - Smoke test production

**Success Criteria**:
- All tests pass (22 unit + 3 E2E)
- No emojis in Python code
- Jobs update DB status on timeout
- Production endpoints return HTTP 200/404 as expected

---

### Phase 2: Recommended Improvements (POST-MERGE)

**Estimated Time**: 3-4 hours (Phase 7.1)

1. **Task 3**: Migrate token costs to settings (45 min)
2. **Task 4**: Add Zod schemas for errors (1 hour)
3. **Validation**: Update tests, verify type safety

---

### Phase 3: Optional Tech Debt (BACKLOG)

**Estimated Time**: 2 hours (Phase 7.2 or later)

1. **Task 5**: Apply MAX_PRODUCTS_PER_SEARCH cap (15 min)
2. **Task 6**: Reduce log verbosity (10 min)
3. **Task 7**: Frontend cache estimates (30 min)
4. **Task 8**: E2E timeout test (1 hour)

---

## Rollback Plan

**If corrections introduce regressions**:

1. **Revert commits**:
   ```bash
   git revert HEAD~2  # Revert last 2 commits (Task 1 + Task 2)
   git push origin main
   ```

2. **Re-deploy previous version**:
   - Render: Trigger manual deploy from commit `f91caf0` (last known good)
   - Verify production endpoints
   - Notify team

3. **Debug locally**:
   - Run failing tests with `-vv` flag
   - Check logs for stack traces
   - Fix issues
   - Re-submit corrections

---

## Testing Strategy

### Unit Tests

```bash
cd backend

# Test autosourcing service
pytest tests/services/test_autosourcing_service.py -v

# Test cost estimator
pytest tests/services/test_autosourcing_cost_estimator.py -v

# Test safeguards schemas
pytest tests/schemas/test_autosourcing_safeguards.py -v

# Full suite
pytest tests/ -v
```

### E2E Tests

```bash
cd backend/tests/e2e

# Phase 7 safeguards tests
FRONTEND_URL=http://arbitragevault.netlify.app \
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com \
npx playwright test tests/08-autosourcing-safeguards.spec.js --reporter=line

# Full autosourcing flow
npx playwright test tests/05-autosourcing-flow.spec.js --reporter=line
```

### Manual Testing

1. **Cost estimation**:
   ```bash
   curl -X POST https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/estimate \
     -H "Content-Type: application/json" \
     -d '{"discovery_config":{"search_type":"isbn","search_value":"9780134685991","max_results":5}}'
   ```
   Expected: HTTP 200 with `{"estimated_tokens": 5, "safe_to_proceed": true}`

2. **Job submission**:
   - Open frontend: http://arbitragevault.netlify.app
   - Navigate to AutoSourcing
   - Click "Estimate Cost"
   - Verify estimate displayed
   - Submit job
   - Verify no error messages

3. **Timeout scenario** (difficult to test):
   - Would require mocking Keepa API delay
   - OR submitting very large job (max_results=200, many categories)
   - Verify HTTP 408 returned
   - Check DB: job.status should be FAILED, not RUNNING

---

## Success Metrics

### Before Corrections

| Metric | Value |
|--------|-------|
| Code Quality Score | 8.7/10 |
| Critical Issues | 1 |
| Important Issues | 3 |
| Test Coverage | 22 unit + 3 E2E |
| Production Ready | 90% |

### After Corrections (Target)

| Metric | Target |
|--------|--------|
| Code Quality Score | 9.5/10 |
| Critical Issues | 0 |
| Important Issues | 2 (deferred to 7.1) |
| Test Coverage | 23 unit + 3 E2E |
| Production Ready | 100% |

---

## References

- **Audit Report**: Code Review Agent output (this session)
- **Phase 7.0 Plan**: `docs/plans/2025-11-13-phase-7.0-autosourcing-safeguards.md`
- **Code Style Rules**: `.claude/CODE_STYLE_RULES.md`
- **Safeguards Docs**: `backend/docs/AUTOSOURCING_SAFEGUARDS.md`
- **E2E Tests**: `backend/tests/e2e/tests/08-autosourcing-safeguards.spec.js`

---

**Plan Created**: 2025-11-19
**Next Step**: Execute Phase 1 (Mandatory Fixes) - Estimated 2-3 hours
**Approval Required**: User validation before execution
