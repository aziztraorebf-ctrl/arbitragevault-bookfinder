# AutoSourcing Safeguards Configuration Guide

**Version** : 1.0.0
**Date** : 14 Novembre 2025
**Status** : IMPLEMENTED

## Overview

AutoSourcing Safeguards protect the production system from Keepa API token exhaustion through multiple layers of protection:

1. **Token Cost Limits** - Maximum tokens per job
2. **Balance Requirements** - Minimum balance before job execution
3. **Timeout Protection** - Maximum execution time per job
4. **ASIN Deduplication** - Prevent analyzing duplicate products
5. **Cost Estimation** - Preview costs before execution

## Configuration Constants

All safeguards are configured in `backend/app/schemas/autosourcing_safeguards.py`:

```python
# Protection Constants
MAX_TOKENS_PER_JOB = 200          # Maximum tokens a single job can consume
MAX_PRODUCTS_PER_SEARCH = 10      # Maximum unique products to analyze
TIMEOUT_PER_JOB = 120             # Maximum seconds for job execution
MIN_TOKEN_BALANCE_REQUIRED = 50   # Minimum balance to start any job
```

## API Endpoints

### Cost Estimation

**Endpoint**: `POST /api/v1/autosourcing/estimate`

Estimates the token cost of a job without consuming any tokens.

**Request Body**:
```json
{
  "discovery_config": {
    "categories": ["books"],
    "max_results": 20,
    "price_range": [10, 50],
    "bsr_range": [10000, 50000]
  }
}
```

**Response**:
```json
{
  "estimated_tokens": 30,
  "current_balance": 150,
  "safe_to_proceed": true,
  "max_allowed": 200,
  "warning_message": null,
  "suggestion": null
}
```

### Job Execution with Validation

**Endpoint**: `POST /api/v1/autosourcing/run_custom`

Validates job requirements before execution.

**Validation Checks**:
1. Estimated cost < MAX_TOKENS_PER_JOB (200)
2. Current balance >= MIN_TOKEN_BALANCE_REQUIRED (50)
3. Timeout protection via asyncio.timeout(TIMEOUT_PER_JOB)

**Error Responses**:

#### Job Too Expensive (400)
```json
{
  "detail": {
    "error": "JOB_TOO_EXPENSIVE",
    "estimated_tokens": 250,
    "max_allowed": 200,
    "suggestion": "Reduce max_results or narrow filters"
  }
}
```

#### Insufficient Tokens (429)
```json
{
  "detail": {
    "error": "INSUFFICIENT_TOKENS",
    "balance": 30,
    "required": 50
  }
}
```

#### Timeout (408)
```json
{
  "detail": "Job timeout - reduce search scope"
}
```

## Cost Calculation Formula

The `AutoSourcingCostEstimator` calculates costs as:

```python
discovery_cost = (max_results / RESULTS_PER_PAGE) * PRODUCT_FINDER_COST
analysis_cost = unique_products * PRODUCT_DETAILS_COST
total_cost = discovery_cost + analysis_cost
```

Where:
- `PRODUCT_FINDER_COST` = 10 tokens per page
- `PRODUCT_DETAILS_COST` = 1 token per ASIN
- `RESULTS_PER_PAGE` = 10

### Examples

1. **Small Search** (10 products):
   - Discovery: 1 page × 10 tokens = 10 tokens
   - Analysis: 10 products × 1 token = 10 tokens
   - Total: 20 tokens ✅ (under limit)

2. **Medium Search** (50 products):
   - Discovery: 5 pages × 10 tokens = 50 tokens
   - Analysis: 50 products × 1 token = 50 tokens
   - Total: 100 tokens ✅ (under limit)

3. **Large Search** (200 products):
   - Discovery: 20 pages × 10 tokens = 200 tokens
   - Analysis: 200 products × 1 token = 200 tokens
   - Total: 400 tokens ❌ (exceeds limit)

## ASIN Deduplication

The `process_asins_with_deduplication` method ensures:

1. **No Duplicate Analysis** - Each ASIN analyzed only once
2. **Order Preservation** - First occurrence order maintained
3. **Limit Enforcement** - Respects MAX_PRODUCTS_PER_SEARCH

**Example**:
```python
Input:  ["ASIN1", "ASIN2", "ASIN1", "ASIN3", "ASIN2"]
Output: ["ASIN1", "ASIN2", "ASIN3"]  # Duplicates removed
```

## Testing

### Unit Tests

Run safeguard-specific tests:
```bash
cd backend
pytest tests/schemas/test_autosourcing_safeguards_schemas.py -v
pytest tests/services/test_autosourcing_cost_estimator.py -v
pytest tests/services/test_autosourcing_validator.py -v
pytest tests/services/test_autosourcing_deduplication.py -v
pytest tests/api/test_autosourcing_estimate.py -v
pytest tests/api/test_autosourcing_validation_enforcement.py -v
pytest tests/api/test_autosourcing_timeout.py -v
```

### E2E Tests

Run end-to-end safeguard tests:
```bash
cd backend/tests/e2e
npx playwright test tests/08-autosourcing-safeguards.spec.js
```

## Frontend Integration

### Cost Estimation UI (Planned)

The frontend should display cost estimates before job submission:

```tsx
// Components needed:
<CostEstimatePanel
  estimatedTokens={30}
  currentBalance={150}
  safeToProcceed={true}
/>

// With warning:
<TokenWarning
  message="This job will consume 180 tokens (90% of limit)"
  severity="warning"
/>
```

### Error Handling

Handle safeguard errors gracefully:

```typescript
if (error.response?.status === 400) {
  const detail = error.response.data.detail;
  if (detail.error === 'JOB_TOO_EXPENSIVE') {
    showError(`Job requires ${detail.estimated_tokens} tokens but limit is ${detail.max_allowed}`);
    showSuggestion(detail.suggestion);
  }
}

if (error.response?.status === 429) {
  const detail = error.response.data.detail;
  showError(`Insufficient tokens: ${detail.balance}/${detail.required}`);
}

if (error.response?.status === 408) {
  showError('Job timeout - try reducing search scope');
}
```

## Monitoring

### Key Metrics to Track

1. **Job Rejection Rate** - % of jobs rejected by safeguards
2. **Average Token Usage** - Tokens per successful job
3. **Timeout Frequency** - Jobs timing out per day
4. **Duplicate Removal Rate** - ASINs removed by deduplication

### Logs to Monitor

```python
# Successful validation
INFO: "AutoSourcing job starting with sufficient tokens: balance=150, required=30"

# Deduplication
INFO: "Deduplication: 45 unique ASINs from 60 input (15 duplicates removed)"

# Rejection
WARNING: "Job rejected - estimated cost 250 exceeds limit 200"
WARNING: "Insufficient tokens for AutoSourcing job: balance=30, required=50"

# Timeout
ERROR: "AutoSourcing job timeout after 120 seconds"
```

## Troubleshooting

### Common Issues

1. **"JOB_TOO_EXPENSIVE" Error**
   - Reduce `max_results` in discovery config
   - Narrow price or BSR ranges
   - Use more specific categories

2. **"INSUFFICIENT_TOKENS" Error**
   - Wait for token refill (50 tokens every 3 hours)
   - Check current balance: `GET /api/v1/keepa/health`
   - Reduce job frequency

3. **Timeout Errors**
   - Reduce `max_results` to process fewer products
   - Check Keepa API response times
   - Verify network connectivity

4. **Unexpected Token Usage**
   - Check for duplicate ASINs in input
   - Verify deduplication is working
   - Review actual vs estimated costs in logs

## Configuration Tuning

### Adjusting Limits

To modify safeguard limits, edit `autosourcing_safeguards.py`:

```python
# Conservative (save tokens)
MAX_TOKENS_PER_JOB = 100
MAX_PRODUCTS_PER_SEARCH = 5

# Balanced (default)
MAX_TOKENS_PER_JOB = 200
MAX_PRODUCTS_PER_SEARCH = 10

# Aggressive (more results)
MAX_TOKENS_PER_JOB = 500
MAX_PRODUCTS_PER_SEARCH = 50
```

### Performance Optimization

For better performance:
1. Enable result caching (24h TTL)
2. Use batch processing for multiple jobs
3. Implement job queuing for rate limiting
4. Monitor and adjust timeout values

## Future Enhancements

### Phase 7.1 - Frontend Polish
- [ ] Implement TokenErrorAlert component with visual badges
- [ ] Add cost estimation preview in job form
- [ ] Show real-time token balance in header
- [ ] Add retry mechanism with exponential backoff

### Phase 7.2 - Advanced Safeguards
- [ ] Implement job queuing system
- [ ] Add per-user token quotas
- [ ] Create admin override capabilities
- [ ] Implement progressive cost warnings

### Phase 7.3 - Analytics
- [ ] Token usage dashboard
- [ ] Cost prediction ML model
- [ ] Automatic limit adjustment based on usage patterns
- [ ] Alert system for abnormal consumption

---

**Authors**: Aziz Traore & Claude
**Last Updated**: 14 Novembre 2025