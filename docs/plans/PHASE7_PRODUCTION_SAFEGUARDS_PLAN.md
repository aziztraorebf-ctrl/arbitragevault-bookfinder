# Phase 7 - Production Safeguards & Polish - Plan Detaille

**Date Creation** : 13 Novembre 2025
**Status** : PLANIFICATION
**Prerequis** : Phase 6 Complete (28/28 tests passing)

---

## OBJECTIF GLOBAL

Securiser l'application production contre epuisement tokens et ameliorer UX avec feedback utilisateur transparent.

**Principe Directeur** : Backend protection AVANT frontend polish

---

## ARCHITECTURE PHASE 7

### Phase 7.0 - AutoSourcing Safeguards (CRITIQUE)
**Priorite** : URGENT - Protection budgetaire
**Temps Estime** : 1-2 jours
**Token Cost Tests** : ~50 tokens

### Phase 7.1 - TokenErrorAlert Component (POLISH)
**Priorite** : Haute - UX improvement
**Temps Estime** : 3-4 heures
**Token Cost Tests** : 0 tokens (mocked)

### Phase 7.2 - Dashboard Enhancements (OPTIONNEL)
**Priorite** : Moyenne
**Temps Estime** : 1 jour

### Phase 7.3 - Export Features (OPTIONNEL)
**Priorite** : Basse
**Temps Estime** : 1 jour

---

## PHASE 7.0 - AUTOSOURCING SAFEGUARDS

### Probleme Actuel

**Risk Assessment** :
- AutoSourcing job SANS limites peut consommer 500+ tokens
- Product Finder discovery non plafonnee
- Pas de deduplication (memes ASINs analyses multiple fois)
- Pas d'estimation cout AVANT lancement job
- Timeout indefini (jobs peuvent tourner 10+ minutes)

**Impact Production** :
- Epuisement balance tokens en 1-2 jobs
- Utilisateur bloque sans comprendre pourquoi
- Couts non previsibles

### Solution Architecture

#### Backend Safeguards

**Fichier** : `backend/app/api/v1/autosourcing.py`

**Constantes Protection** :
```python
MAX_PRODUCTS_PER_SEARCH = 10
MAX_TOKENS_PER_JOB = 200
TIMEOUT_PER_JOB = 120
MIN_TOKEN_BALANCE_REQUIRED = 50
```

**Validation Pre-Job** :
```python
async def validate_job_requirements(
    discovery_config: DiscoveryConfigSchema,
    scoring_config: ScoringConfigSchema
) -> JobValidationResult:
    estimated_tokens = estimate_job_cost(discovery_config)

    if estimated_tokens > MAX_TOKENS_PER_JOB:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "JOB_TOO_EXPENSIVE",
                "estimated_tokens": estimated_tokens,
                "max_allowed": MAX_TOKENS_PER_JOB,
                "suggestion": "Reduce max_results or narrow filters"
            }
        )

    current_balance = await get_keepa_balance()
    if current_balance < MIN_TOKEN_BALANCE_REQUIRED:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "INSUFFICIENT_TOKENS",
                "balance": current_balance,
                "required": MIN_TOKEN_BALANCE_REQUIRED
            }
        )

    return JobValidationResult(
        estimated_tokens=estimated_tokens,
        current_balance=current_balance,
        safe_to_proceed=True
    )
```

**Deduplication Logic** :
```python
async def process_job_with_deduplication(
    job_id: UUID,
    asins_to_analyze: List[str]
) -> JobResult:
    analyzed_asins = set()
    results = []
    tokens_used = 0

    for asin in asins_to_analyze:
        if asin in analyzed_asins:
            continue

        if tokens_used >= MAX_TOKENS_PER_JOB:
            break

        result = await analyze_product(asin)
        analyzed_asins.add(asin)
        results.append(result)
        tokens_used += result.tokens_consumed

    return JobResult(
        job_id=job_id,
        products_analyzed=len(results),
        unique_asins=len(analyzed_asins),
        tokens_used=tokens_used,
        results=results
    )
```

**Timeout Protection** :
```python
async def run_autosourcing_job(job_id: UUID):
    try:
        async with asyncio.timeout(TIMEOUT_PER_JOB):
            return await _execute_job_logic(job_id)
    except asyncio.TimeoutError:
        await update_job_status(
            job_id,
            status="TIMEOUT",
            error="Job exceeded timeout limit (120s)"
        )
        raise HTTPException(
            status_code=408,
            detail="Job timeout - reduce search scope"
        )
```

#### Frontend Cost Estimation

**Fichier** : `frontend/src/components/AutoSourcingJobModal.tsx`

**Feature** : Bouton [Estimer Cout]

```typescript
const estimateJobCost = async (config: JobConfig): Promise<CostEstimate> => {
  const response = await fetch('/api/v1/autosourcing/estimate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });

  const estimate: CostEstimate = await response.json();
  return estimate;
};

interface CostEstimate {
  estimated_tokens: number;
  current_balance: number;
  safe_to_proceed: boolean;
  warning_message?: string;
}
```

**UI Display** :
```tsx
{estimate && (
  <div className="cost-estimate-panel">
    <p>Cout estime : {estimate.estimated_tokens} tokens</p>
    <p>Balance actuelle : {estimate.current_balance} tokens</p>

    {!estimate.safe_to_proceed && (
      <Alert variant="warning">
        {estimate.warning_message}
      </Alert>
    )}
  </div>
)}
```

### Tests Required

**Backend Tests** : `backend/tests/test_autosourcing_safeguards.py`

```python
def test_job_validation_rejects_expensive_jobs():
    config = DiscoveryConfigSchema(
        categories=["books"],
        max_results=500  # Too expensive
    )

    with pytest.raises(HTTPException) as exc:
        validate_job_requirements(config, scoring_config)

    assert exc.value.status_code == 400
    assert "JOB_TOO_EXPENSIVE" in exc.value.detail["error"]

def test_deduplication_prevents_duplicate_analysis():
    asins = ["ASIN1", "ASIN2", "ASIN1", "ASIN3"]  # ASIN1 duplicate

    result = process_job_with_deduplication(job_id, asins)

    assert result.unique_asins == 3
    assert result.products_analyzed == 3

def test_timeout_protection_cancels_long_jobs():
    with pytest.raises(HTTPException) as exc:
        await run_autosourcing_job(long_running_job_id)

    assert exc.value.status_code == 408
```

**E2E Tests** : `backend/tests/e2e/tests/08-autosourcing-safeguards.spec.js`

```javascript
test('Should display cost estimate before job submission', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/autosourcing`);

  await page.fill('input[name="max_results"]', '50');

  const estimateButton = page.locator('button:has-text("Estimer")');
  await estimateButton.click();

  await page.waitForSelector('text=/Cout estime/i');

  const costEstimate = page.locator('text=/\\d+ tokens/').first();
  await expect(costEstimate).toBeVisible();
});

test('Should reject job if cost exceeds limit', async ({ page }) => {
  await page.route('**/api/v1/autosourcing/run_custom', route => {
    route.fulfill({
      status: 400,
      body: JSON.stringify({
        error: "JOB_TOO_EXPENSIVE",
        estimated_tokens: 500,
        max_allowed: 200
      })
    });
  });

  await submitExpensiveJob();

  await page.waitForSelector('text=/JOB_TOO_EXPENSIVE/i');
});
```

---

## PHASE 7.1 - TOKENERRORALERT COMPONENT

### Implementation Plan

#### Component Creation

**Fichier** : `frontend/src/components/TokenErrorAlert.tsx`

```tsx
import React from 'react';
import { AlertCircle } from 'lucide-react';

interface TokenErrorAlertProps {
  balance: number;
  required: number;
  onRetry?: () => void;
}

export const TokenErrorAlert: React.FC<TokenErrorAlertProps> = ({
  balance,
  required,
  onRetry
}) => {
  const deficit = required - balance;

  return (
    <div className="token-error-alert">
      <div className="alert-header">
        <AlertCircle className="alert-icon" />
        <h3>Tokens insuffisants</h3>
      </div>

      <div className="token-badges">
        <div className="badge balance">
          <span className="label">Balance actuelle</span>
          <span className="value">{balance} tokens</span>
        </div>

        <div className="badge required">
          <span className="label">Requis</span>
          <span className="value">{required} tokens</span>
        </div>

        <div className="badge deficit">
          <span className="label">Deficit</span>
          <span className="value danger">-{deficit} tokens</span>
        </div>
      </div>

      <p className="message">
        Cette operation necessite {required} tokens, mais votre balance
        actuelle est de {balance} tokens. Veuillez attendre le rechargement
        automatique (50 tokens toutes les 3 heures).
      </p>

      {onRetry && (
        <button onClick={onRetry} className="retry-button">
          Reessayer
        </button>
      )}
    </div>
  );
};
```

#### Integration Points

**Fichier** : `frontend/src/utils/tokenErrorHandler.ts`

```typescript
export interface TokenError {
  type: 'TOKEN_ERROR';
  balance: number;
  required: number;
  retryAfter?: number;
}

export const parseTokenError = (error: any): TokenError | null => {
  if (error.response?.status === 429) {
    const headers = error.response.headers;
    return {
      type: 'TOKEN_ERROR',
      balance: parseInt(headers['x-token-balance'] || '0'),
      required: parseInt(headers['x-token-required'] || '0'),
      retryAfter: parseInt(headers['retry-after'] || '0')
    };
  }
  return null;
};
```

#### Test Updates

**Fichier** : `backend/tests/e2e/tests/06-token-error-handling.spec.js`

**Modifications** :
```javascript
// BEFORE (generic error)
await page.waitForSelector('text=/Erreur/i');

// AFTER (dedicated component)
await page.waitForSelector('[data-testid="token-error-alert"]');

const balanceBadge = page.locator('[data-testid="balance-badge"]');
await expect(balanceBadge).toContainText('5 tokens');

const requiredBadge = page.locator('[data-testid="required-badge"]');
await expect(requiredBadge).toContainText('10 tokens');

const deficitBadge = page.locator('[data-testid="deficit-badge"]');
await expect(deficitBadge).toContainText('-5 tokens');
```

---

## DELIVERABLES PHASE 7.0

### Backend Files
- [ ] `backend/app/api/v1/autosourcing.py` - Safeguards implementation
- [ ] `backend/app/services/autosourcing_validator.py` - Validation logic
- [ ] `backend/tests/test_autosourcing_safeguards.py` - Unit tests

### Frontend Files
- [ ] `frontend/src/components/AutoSourcingJobModal.tsx` - Cost estimation
- [ ] `frontend/src/services/autosourcingService.ts` - API integration

### Tests
- [ ] Unit tests backend (8 tests)
- [ ] E2E tests (3 tests - 08-autosourcing-safeguards.spec.js)

### Documentation
- [ ] `docs/AUTOSOURCING_SAFEGUARDS.md` - Configuration guide
- [ ] Update `compact_master.md` with Phase 7.0 completion

---

## DELIVERABLES PHASE 7.1

### Frontend Files
- [ ] `frontend/src/components/TokenErrorAlert.tsx` - Component
- [ ] `frontend/src/components/TokenErrorBadge.tsx` - Compact variant
- [ ] `frontend/src/utils/tokenErrorHandler.ts` - Error parsing

### Tests
- [ ] Update `06-token-error-handling.spec.js` (3 tests)

### Documentation
- [ ] Update `compact_master.md` with Phase 7.1 completion

---

## SUCCESS CRITERIA

### Phase 7.0
- [ ] AutoSourcing jobs plafonnees a 200 tokens max
- [ ] Deduplication elimine analyses repetees
- [ ] Timeout protection a 120 secondes
- [ ] Frontend affiche estimation cout AVANT soumission
- [ ] Tests backend 100% passing
- [ ] Tests E2E 100% passing

### Phase 7.1
- [ ] TokenErrorAlert component implemente
- [ ] Badges balance/required/deficit visibles
- [ ] Message francais convivial
- [ ] Bouton retry fonctionnel
- [ ] Tests E2E updates 100% passing

---

## NEXT STEPS

1. **Brainstorming Session** : Utiliser superpowers:brainstorming pour affiner implementation details
2. **Create Implementation Plan** : Utiliser superpowers:writing-plans pour plan detaille avec tasks
3. **TDD Implementation** : Utiliser superpowers:test-driven-development pour chaque feature
4. **Code Review** : Utiliser superpowers:requesting-code-review apres completion

---

**Auteurs** :
- Aziz Traore
- Claude (Anthropic AI Assistant)

**Date** : 13 Novembre 2025
**Version** : Phase 7 Planning Draft
