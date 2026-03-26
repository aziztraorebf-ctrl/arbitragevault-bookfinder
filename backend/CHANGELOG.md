# ArbitrageVault Backend - Changelog

All notable changes to the ArbitrageVault Backend project are documented in this file.

---

## [2.2.0] - 2026-03-26 - P2 Simplification + Codebase Audit

### Added
- **CoWork endpoints** (2 new): `GET /cowork/keepa-balance` (token balance with 60s cache), `GET /cowork/jobs` (paginated job list with status filter)
- **Rate limiting**: `app/core/rate_limiter.py` — SlidingWindowLimiter in-memory, zero external dep
  - GET /cowork/* : 30 req/min
  - POST /cowork/fetch-and-score : 5 req/min
  - HTTP 429 + Retry-After header on limit exceeded
- **`autosourcing_scoring.py`**: 8 ROI/scoring functions extracted from autosourcing_service.py (212 LOC new module)
- **`data_quality` flag**: on dashboard-summary and daily-buy-list to distinguish missing data vs DB error

### Changed
- `autosourcing_service.py` reduced from 1244 to 1037 LOC (ROI duplication eliminated)
- BSR standardized to `-1` for unknown (was inconsistently `0` or `None`)
- Pydantic `response_model` added to all CoWork endpoints (was missing)
- Timezone handling in `daily_review.py` fixed (aware -> naive UTC)

### Fixed
- `bsr or -1` bug: BSR value of `0` was incorrectly converted to `-1`
- 12 `except Exception: pass` silent failures replaced with proper logging
- `data_quality` not propagated when `history_map` query failed

### Removed
- `app/services/amazon_filter_service.py` (dead code, 255 LOC)
- `app/services/async_job_service.py` (dead code, 243 LOC)
- 50+ debug scripts and temporary JSON files from `backend/` root

---

## [2.1.0] - 2026-03-24 - Security Audit + Agent API Integration

### Added
- **Security headers middleware**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- **Rate limiting on public endpoints**: 30 req/min public, 10 req/min health
- **`backend/scripts/create_api_key.py`**: CLI script to create API keys for agents (CoWork, N8N) with configurable scopes
- **`COWORK_API_TOKEN`**: Separate Bearer token auth for CoWork agent, independent from Firebase and avk_ API keys
- **CoWork router** (`/api/v1/cowork`): 4 initial endpoints for AI agent access
  - `GET /dashboard-summary`: system metrics + top picks + data_quality
  - `POST /fetch-and-score`: on-demand ASIN scoring
  - `GET /daily-buy-list`: STABLE picks filtered by confidence threshold
  - `GET /last-job-stats`: latest job statistics
- **`test_security_audit.py`**: 12 security tests
- **`test_cowork_router.py`**: 431 lines covering all CoWork endpoints

### Changed
- `app/core/settings.py`: added `COWORK_API_TOKEN` field

---

## [2.0.0] - 2026-03-24 - ROI Fix + Notification Service

### Added
- **`notification_service.py`**: dual-channel alerting (SMS via Textbelt + Email via Resend)
  - `send_sms()`: Textbelt API integration
  - `send_email()`: Resend API integration
  - `notify_picks_found()`: orchestrates both channels when stable_count > 0
- **`seed_source_price_factor.py`**: upserts `source_price_factor=0.35` into `business_config` table
- **Webhook integration**: notifications triggered after webhook delivery in `webhook_service.py`
- **New env vars**: `TEXTBELT_API_KEY`, `NOTIFICATION_PHONE`, `RESEND_API_KEY`, `NOTIFICATION_EMAIL` (all optional)

### Fixed
- **ROI fictif**: `source_price_factor` was hardcoded to `0.50` fallback even when DB config missing. Now seeded at `0.35` with documented fallback behavior.

### Changed
- `autosourcing_service.py`: fallback locations for `source_price_factor` documented with comments

---

## [1.9.0] - 2026-03-24 - Bugfixes 35+ (Critical + Medium + Low)

### Fixed — Critical (PR #14)
- CoWork router: wrong dict keys (`total_picks` -> `total`/`classified_products`)
- CoWork router: `history_map={}` caused all products to be classified FLUKE
- Pipeline: `JobStatus.FAILED` did not exist, use `JobStatus.ERROR`
- Pipeline: `except Exception` was catching `HTTPException` from timeout
- Pipeline: double timeout (router + service)
- Scoring: BSR `elif` ordering had dead code for `bsr > 1M`
- Scoring: velocity calculated using BuyBox price instead of BSR rank
- Frontend: `/recherches/stats` endpoint did not exist (404)

### Fixed — High (PR #14)
- Schema `DailyReviewResponse`: missing `classified_products` field
- `ActionableBuyItem.overall_rating`: wrong type `float` -> `Optional[str]`
- Daily review: `stability_score` and `condition_signal` not passed
- Daily review: queried nonexistent `asin_history` table instead of `AutoSourcingPick`
- Classification: naive/aware datetime mismatch for REVENANT detection
- `breakeven_price`: formula was inverted
- `fba_count=0`: falsy-zero bug
- Velocity trend: wrong comparison for 7-13 data points
- ROI clamped at 100% suppressed differentiation
- Frontend AutoSourcing: plain `fetch()` without Firebase auth
- Frontend: wrong env var `VITE_API_BASE_URL`

### Fixed — Medium (PR #15)
- ASIN deduplication in daily review and CoWork by ASIN
- `engagement_rate` formula corrected to `total_actions/total_picks`
- `job_id`: `str` -> `UUID` in tier endpoint
- Category extraction: `categoryTree[-1]` instead of `[0]`
- `source_price_factor` default aligned to `0.35`
- `target_buy_price`: guard `max(0, ...)` against negatives
- `velocity`/`confidence` scores passed to buy items
- `amazon_on_listing` NULL treated correctly as `None` (not `False`)
- BSR null: `0` instead of `-1`
- Frontend: throw when 4/5+ fetches fail
- Dead code: `_build_keepa_search_params` removed
- `is_purchased`: no longer set on `TO_BUY` intent

### Fixed — Low (PR #17)
- Keepa constants: `RATING` index 15->16, `COUNT_REVIEWS` 16->17, `EXTRA_INFO_UPDATES=15` added
- `_extract_rating()` was reading `array[15]` instead of `array[16]`
- `dispatch_webhook`: fresh DB session created in `asyncio.create_task` to avoid expired session

---

## [1.8.0] - 2026-03-21 - Phase C: Condition Signals + Pydantic v2

### Added
- **Condition signals** in unified analysis pipeline (`unified_analysis.py`):
  - Step 5.5: derives `condition_signal` (STRONG/MODERATE/WEAK/UNKNOWN) from used ROI + used offer count
  - STRONG: used ROI >= 25% AND <= 10 competing used sellers
  - MODERATE: used ROI >= 10% AND <= 25 competing used sellers
  - Confidence boost: +10 (STRONG), +5 (MODERATE) via `business_rules.json` config
- **`condition_breakdown`** in buying guidance: sorted by ROI desc with French labels (Neuf, Tres bon, Bon, Acceptable)
- **`recommended_condition`** and **`condition_signal`** in buying_guidance response
- `test_phase_c_enhancements.py`: 24 new tests

### Fixed
- Pydantic v2: `decimal_places=2` deprecated field replaced with `field_validator` + `round(v, 2)`
- Pydantic v2: defaults migrated to `Decimal("...")` instead of float/int literals

---

## [1.7.1] - 2026-02-21 - Phase 3: Radical Simplification

### Changed
- Navigation reduced from 10 items to 4 (Dashboard, AutoSourcing, AutoScheduler, Configuration)
- Backend: 20 routers reduced to 11 in `main.py`
- Frontend: 45 files archived to `_archive/frontend/`
- Backend: 30+ files archived to `_archive/backend/`
- Tests: 32 test files archived, 785 remaining tests pass

### Decisions (BookMine methodology, Feb 2026)
- Prime Bump strategy dead since Nov 3 2025 (Amazon Buy Box algorithm change)
- Condition Bump: Amazon prioritizes Condition > Price > Shipping
- Intrinsic Value is the only viable pricing model
- 5 Keepa signals that matter: lowest used price, BSR drops, Amazon price, offer count, stock qty

---

## [1.7.0] - 2026-01-10 - Firebase Authentication (Phase 13)

### Added
- **Firebase Authentication**: Complete auth system with Firebase Admin SDK
  - `POST /api/v1/auth/sync` - Sync user from Firebase
  - `GET /api/v1/auth/me` - Get current user
  - `GET /api/v1/auth/verify` - Verify token
  - `POST /api/v1/auth/logout` - Logout placeholder
- **Firebase Admin SDK** integration for token verification
- **User model** with `firebase_uid` field
- `get_current_user` dependency for all protected endpoints

### Fixed
- Production white screen (wrong `VITE_API_URL` on Netlify)

---

## [1.6.4] - 2026-01-03 - UX Mobile-First (Phase 12)

### Added
- Mobile-First UX: responsive design with touch-friendly UI
- Mes Recherches: centralized search results page with 30-day retention
- Unified Product Table: consistent product display across features

---

## [1.6.2] - 2025-12-07 - AutoSourcing Production Ready

### Fixed
- BSR tuple unpacking in keepa_parser_v2
- Keepa category IDs updated to valid /bestsellers IDs
- Centralized category configuration with MCP validation

### Changed
- AutoSourcing now uses KeepaProductFinderService REST API

---

## [1.6.0] - 2025-11 - Phase 7: AutoSourcing Module

### Added
- **AutoSourcing endpoints**: `/api/v1/autosourcing/*`
  - POST /run, POST /run-custom, GET /latest, GET /opportunity-of-day
  - GET /jobs, GET /jobs/{id}, GET /jobs/{id}/tiers
  - GET /profiles, POST /profiles
  - PUT /picks/{id}/action, GET /to-buy, GET /favorites
  - GET /stats, GET /health

---

## [1.5.0] - 2025-11 - Phase 6: Frontend E2E Tests

### Added
- 56 E2E tests with Playwright
- FBA seller competition filter
- Smart Velocity and Textbooks strategies
- Budget Guard for token waste prevention

---

## [1.4.0] - 2025-10 - Phase 5: Token Control

### Added
- AutoScheduler: automated job scheduling
- Token safeguards: `@require_tokens` decorator
- HTTP 429 rate limit handling with retry

---

## [1.3.0] - 2025-10 - Phase 4: Architecture Improvements

### Added
- Keepa Parser v2 with improved data extraction
- SRP-compliant module splitting

### Fixed
- ROI calculation: `source_price_factor` unified
- Sales velocity `ZeroDivisionError` guard

---

## [1.2.0] - 2025-10 - Phase 3: Keepa Integration

### Added
- Real Keepa API integration
- BSR history tracking
- Price volatility analysis
- Velocity scoring system

---

## [1.1.0] - 2025-10 - Phase 2: Business Logic

### Added
- Analytics endpoints: `/api/v1/analytics/*`
- Niche Discovery: `/api/v1/niches/discover`
- Views system: `/api/v1/views/*`

---

## [2.0.0-db] - 2025-09-29 - Database Migration

### Changed
- Database: Render PostgreSQL -> Neon PostgreSQL
- Connection pool: 20 -> 300-500 concurrent connections

---

## [1.0.0] - 2025-09 - Initial Release

### Added
- FastAPI backend with SQLAlchemy ORM
- Batch management system
- Health monitoring endpoints
- Render deployment configuration
