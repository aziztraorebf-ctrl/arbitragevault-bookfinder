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

## Health & System

### GET /health
System health check with version info.
```bash
curl "https://arbitragevault-backend-v2.onrender.com/health"
```
**Response:**
```json
{"status": "ready", "service": "ArbitrageVault API", "version": "1.7.0"}
```

---

## Authentication (Firebase)

All protected endpoints require a Firebase ID token in the Authorization header:
```
Authorization: Bearer <firebase_id_token>
```

### GET /api/v1/auth/me
Get current authenticated user information.
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
Sync user from Firebase to database (called after registration/login).
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  "https://arbitragevault-backend-v2.onrender.com/api/v1/auth/sync"
```

### GET /api/v1/auth/verify
Verify Firebase token validity.

### POST /api/v1/auth/logout
Logout endpoint (placeholder - logout handled client-side).

---

## Batch Management

### GET /api/v1/batches
List analysis batches with pagination.
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches?page=1&per_page=20"
```

### POST /api/v1/batches
Create new analysis batch.

### GET /api/v1/batches/{batch_id}
Get specific batch details.

### PATCH /api/v1/batches/{batch_id}/status
Update batch status.

---

## Analysis Results

### GET /api/v1/analyses
List analysis results with pagination.

### GET /api/v1/analyses/{analysis_id}
Get specific analysis.

### POST /api/v1/analyses
Create analysis result.

---

## Keepa Integration

### POST /api/v1/keepa/ingest
Ingest product data from Keepa API.

### GET /api/v1/keepa/{asin}/metrics
Get product metrics for an ASIN.
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/B08N5WRWNW/metrics"
```

### GET /api/v1/keepa/{asin}/raw
Get raw Keepa data for an ASIN.

### GET /api/v1/keepa/health
Keepa service health check.

### POST /api/v1/keepa/debug-analyze
Debug analysis endpoint.

---

## AutoSourcing (Phase 7)

### POST /api/v1/autosourcing/run
Run discovery job with default parameters.

### POST /api/v1/autosourcing/run-custom
Run discovery with custom parameters.
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

### GET /api/v1/autosourcing/opportunity-of-day
Get daily top pick.

### GET /api/v1/autosourcing/jobs
List all jobs.

### GET /api/v1/autosourcing/jobs/{job_id}
Get specific job details.

### GET /api/v1/autosourcing/jobs/{job_id}/tiers
Get tier breakdown for a job.

### GET /api/v1/autosourcing/profiles
List saved search profiles.

### POST /api/v1/autosourcing/profiles
Create new profile.

### PUT /api/v1/autosourcing/picks/{pick_id}/action
Mark pick action (buy/favorite/skip).

### GET /api/v1/autosourcing/to-buy
Get buy list.

### GET /api/v1/autosourcing/favorites
Get favorites list.

### GET /api/v1/autosourcing/my-actions/{action}
Get picks by action type.

### GET /api/v1/autosourcing/stats
Get AutoSourcing statistics.

### GET /api/v1/autosourcing/health
AutoSourcing service health.

---

## Analytics

### POST /api/v1/analytics/calculate-analytics
Calculate analytics for a product.

### POST /api/v1/analytics/calculate-risk-score
Calculate risk score.

### POST /api/v1/analytics/generate-recommendation
Generate buy/skip recommendation.

### POST /api/v1/analytics/product-decision
Full product decision analysis.

---

## Niche Discovery

### GET /api/v1/niches/discover
Discover niches with scoring.
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/niches/discover?category_id=283155&limit=20"
```

### GET /api/v1/niches/health
Niche service health.

---

## Bookmarks

### GET /api/v1/bookmarks/niches
List saved niche bookmarks.

### POST /api/v1/bookmarks/niches
Save a niche bookmark.

### DELETE /api/v1/bookmarks/niches/{id}
Delete a niche bookmark.

---

## Searches (Mes Recherches)

### GET /api/v1/searches
List saved searches with 30-day retention.

### POST /api/v1/searches
Save search results.

### GET /api/v1/searches/{id}
Get specific search details.

### DELETE /api/v1/searches/{id}
Delete a saved search.

---

## Views

### POST /api/v1/views/{view_type}
Calculate view scores.

### GET /api/v1/views
List available views.

---

## Configuration

### GET /api/v1/config/
Get current business configuration.

### PUT /api/v1/config/
Update configuration.

### POST /api/v1/config/preview
Preview configuration changes.

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

### GET /api/v1/products/health
Products service health.

---

## Common Patterns

### Authentication
Protected endpoints require Firebase ID token:
```
Authorization: Bearer <firebase_id_token>
```

### Pagination Parameters
All list endpoints support:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

### Batch Status Values
```
PENDING    - Newly created, not started
PROCESSING - Currently being analyzed
COMPLETED  - Successfully finished
FAILED     - Terminated with errors
CANCELLED  - Manually stopped
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
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `429` - Rate limited (Keepa tokens)
- `500` - Internal error

---

**API Version**: 1.7.0
**Last Updated**: January 2026
