# ArbitrageVault API Documentation

## Base URL
```
Production: https://arbitragevault-backend-v2.onrender.com
Local Dev:  http://localhost:8000
```

## Interactive Documentation
- **Swagger UI**: `{BASE_URL}/docs`
- **ReDoc**: `{BASE_URL}/redoc`
- **OpenAPI Schema**: `{BASE_URL}/openapi.json`

---

## Authentication

### Human Users (Firebase)
All protected endpoints require a Firebase ID token:
```
Authorization: Bearer <firebase_id_token>
```

### Agent Users (API Key)
Agents (N8N, OpenClaw, etc.) use an API Key header:
```
X-API-Key: avk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
API keys are scoped. Available scopes: `autosourcing:read`, `autosourcing:write`, `autosourcing:job_read`, `daily_review:read`.
Create keys via `backend/scripts/create_api_key.py`.

### CoWork Agent (Bearer Token)
The CoWork AI agent uses a separate Bearer token (not Firebase):
```
Authorization: Bearer <COWORK_API_TOKEN>
```
This token is set via the `COWORK_API_TOKEN` environment variable on Render.

---

## Rate Limiting

CoWork endpoints are rate-limited per token:
- `GET /api/v1/cowork/*` : 30 requests/min
- `POST /api/v1/cowork/fetch-and-score` : 5 requests/min

On limit exceeded: `HTTP 429` with `Retry-After` header.

---

## Health & System

### GET /health
```bash
curl "https://arbitragevault-backend-v2.onrender.com/health"
```
**Response:**
```json
{"status": "ok", "service": "ArbitrageVault API", "version": "2.2.0"}
```

### HEAD /health
Lightweight health check for monitoring (no body).

---

## Authentication Endpoints

### GET /api/v1/auth/me
Get current authenticated user.
```bash
curl -H "Authorization: Bearer <token>" \
  "https://arbitragevault-backend-v2.onrender.com/api/v1/auth/me"
```
**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "sourcer",
  "is_active": true
}
```

### POST /api/v1/auth/sync
Sync user from Firebase to database (call after registration/login).

### GET /api/v1/auth/verify
Verify Firebase token validity.

### POST /api/v1/auth/logout
Logout placeholder (logout is handled client-side with Firebase).

---

## AutoSourcing

### POST /api/v1/autosourcing/run
Run discovery job with default parameters.
**Auth**: Firebase Bearer or API Key (`autosourcing:write`)

### POST /api/v1/autosourcing/run-custom
Run discovery with custom parameters.
**Auth**: Firebase Bearer or API Key (`autosourcing:write`)
```json
{
  "category_id": 283155,
  "max_products": 50,
  "min_roi": 30,
  "max_bsr": 500000
}
```

### GET /api/v1/autosourcing/latest
Get latest job results.
**Auth**: Firebase Bearer (public endpoint, no auth required)

### GET /api/v1/autosourcing/opportunity-of-day
Get daily top pick.

### GET /api/v1/autosourcing/jobs
List all jobs.
**Auth**: Firebase Bearer or API Key (`autosourcing:job_read`)

### GET /api/v1/autosourcing/jobs/{job_id}
Get specific job details and picks.
**Auth**: Firebase Bearer or API Key (`autosourcing:job_read`)

### GET /api/v1/autosourcing/jobs/{job_id}/tiers
Get tier breakdown for a job.

### GET /api/v1/autosourcing/profiles
List saved search profiles.

### POST /api/v1/autosourcing/profiles
Create new search profile.

### PUT /api/v1/autosourcing/picks/{pick_id}/action
Mark pick action (buy/favorite/skip).

### GET /api/v1/autosourcing/to-buy
Get buy list.
**Auth**: Firebase Bearer or API Key (`autosourcing:read`)

### GET /api/v1/autosourcing/favorites
Get favorites list.
**Auth**: Firebase Bearer or API Key (`autosourcing:read`)

### GET /api/v1/autosourcing/stats
Get AutoSourcing statistics.

---

## Daily Review

### GET /api/v1/daily-review/today
Full classified review with all 5 categories and counts.
**Auth**: Firebase Bearer or API Key (`daily_review:read`)

**Response:**
```json
{
  "date": "2026-03-26",
  "classified_products": {
    "STABLE": [...],
    "JACKPOT": [...],
    "REVENANT": [...],
    "FLUKE": [...],
    "REJECT": [...]
  },
  "counts": {"STABLE": 4, "JACKPOT": 1, "REVENANT": 2, "FLUKE": 8, "REJECT": 12}
}
```

### GET /api/v1/daily-review/actionable
STABLE-only pre-filtered buy list, sorted by stability then ROI.
**Auth**: Firebase Bearer or API Key (`daily_review:read`)

**Response:**
```json
{
  "items": [
    {
      "asin": "0134685997",
      "title": "The Pragmatic Programmer",
      "category": "Computers & Technology",
      "current_price": 45.00,
      "estimated_buy_price": 15.75,
      "roi_percentage": 28.5,
      "stability_score": 74,
      "confidence_score": 81,
      "velocity_score": 62,
      "condition_signal": "STRONG",
      "bsr": 12450,
      "classification": "STABLE",
      "action_recommendation": "BUY"
    }
  ],
  "total_found": 3,
  "filters_applied": {"min_roi": 15.0, "max_results": 10, "classification": "STABLE"},
  "generated_at": "2026-03-26T07:00:00+00:00"
}
```

---

## CoWork Agent API

Dedicated endpoints for AI agents. All require CoWork Bearer token.

### GET /api/v1/cowork/dashboard-summary
System health + 24h stats + top picks.
**Rate limit**: 30/min

**Response:**
```json
{
  "system_health": "ok",
  "last_job": {"id": "uuid", "status": "success", "picks_count": 18, "stable_count": 4},
  "stats_24h": {"total_jobs": 3, "total_picks": 52, "stable_picks": 11},
  "top_picks": [...],
  "data_quality": "full"
}
```
`data_quality` values: `full` (all data available), `degraded` (partial data), `unavailable` (no data).

### POST /api/v1/cowork/fetch-and-score
On-demand product analysis by ASIN or ISBN.
**Rate limit**: 5/min

```json
{"asins": ["0134685997", "0596517742"]}
```

### GET /api/v1/cowork/daily-buy-list
Curated list of STABLE picks above confidence threshold.
**Rate limit**: 30/min

Returns same structure as `/daily-review/actionable` plus `data_quality` field.

### GET /api/v1/cowork/last-job-stats
Stats from the most recent AutoSourcing job.
**Rate limit**: 30/min

### GET /api/v1/cowork/keepa-balance
Current Keepa token balance (cached 60 seconds).
**Rate limit**: 30/min

```json
{"tokens_remaining": 1250, "cached": true, "cache_age_seconds": 23}
```

### GET /api/v1/cowork/jobs
Paginated list of AutoSourcing jobs with optional status filter.
**Rate limit**: 30/min

```
GET /api/v1/cowork/jobs?limit=10&offset=0&status=success
```

```json
{
  "jobs": [
    {"id": "uuid", "status": "success", "picks_count": 18, "stable_count": 4, "started_at": "..."}
  ],
  "total": 47,
  "limit": 10,
  "offset": 0
}
```

---

## API Keys Management

### GET /api/v1/api-keys
List all API keys for current user.
**Auth**: Firebase Bearer

### POST /api/v1/api-keys
Create a new API key.
**Auth**: Firebase Bearer

```json
{
  "name": "N8N Workflow",
  "scopes": ["autosourcing:read", "daily_review:read"]
}
```

### PATCH /api/v1/api-keys/{key_id}
Update API key (name, scopes, active status).
**Auth**: Firebase Bearer

### DELETE /api/v1/api-keys/{key_id}
Revoke an API key.
**Auth**: Firebase Bearer

---

## Keepa Integration

### POST /api/v1/keepa/ingest
Ingest product data from Keepa API.

### GET /api/v1/keepa/{asin}/metrics
Get product metrics for an ASIN.

### GET /api/v1/keepa/{asin}/raw
Get raw Keepa data for an ASIN.

### GET /api/v1/keepa/health
Keepa service health check.

---

## Configuration

### GET /api/v1/config/
Get current business configuration (thresholds, scoring weights, etc.).

### PUT /api/v1/config/
Update configuration.

### POST /api/v1/config/preview
Preview configuration changes without applying.

### GET /api/v1/config/changes
Get configuration change history.

### GET /api/v1/config/stats
Get configuration statistics.

---

## ASIN History

### GET /api/v1/asin-history/trends/{asin}
Get price/BSR trends for an ASIN.

### GET /api/v1/asin-history/records/{asin}
Get historical records.

### GET /api/v1/asin-history/latest/{asin}
Get latest record.

---

## Products

### GET /api/v1/products/categories
List available categories.

---

## Webhooks

When an AutoSourcing job completes, the backend POSTs to all configured webhook URLs:

```json
{
  "event": "autosourcing.job.completed",
  "timestamp": "2026-03-26T07:04:32+00:00",
  "data": {
    "job_id": "uuid",
    "picks_count": 18,
    "stable_count": 4,
    "duration_seconds": 47.2
  }
}
```

Header: `X-Webhook-Signature: sha256=<hmac>` for payload verification.

If `stable_count > 0`, SMS (Textbelt) and/or email (Resend) notifications are also triggered.

---

## Common Patterns

### Pagination Parameters
List endpoints support:
- `limit`: Items per page (default: 20, max: 100)
- `offset`: Offset for pagination (default: 0)

### Pick Classification Values
```
STABLE    - Recommended buy (2+ sightings, ROI 15-80%, no Amazon on listing)
JACKPOT   - High ROI (>80%) — manual verification required before acting
REVENANT  - Reappeared after 24h+ absence — monitor
FLUKE     - First time seen — not enough data
REJECT    - Amazon on listing, ROI < 0, BSR invalid, or WEAK condition + ROI < 5%
```

### condition_signal Values
```
STRONG    - used ROI >= 25% AND <= 10 competing used sellers (+10 confidence)
MODERATE  - used ROI >= 10% AND <= 25 competing used sellers (+5 confidence)
WEAK      - low used ROI or too much competition
UNKNOWN   - no used price data available
```

### data_quality Values
```
full        - all data sources available, results reliable
degraded    - partial data (e.g. history unavailable), results approximate
unavailable - no data available (DB error or empty)
```

### Error Responses
```json
{"detail": "Human-readable error message"}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad request
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient scope)
- `404` - Not found
- `429` - Rate limited (CoWork endpoints or Keepa tokens exhausted)
- `500` - Internal error

---

**API Version**: 2.2.0
**Last Updated**: March 26, 2026
