# ArbitrageVault Backend - Changelog

All notable changes to the ArbitrageVault Backend project are documented in this file.

## [1.7.0] - 2026-01-10 - Firebase Authentication

### Added
- **Firebase Authentication**: Complete auth system with Firebase Admin SDK
  - POST /api/v1/auth/sync - Sync user from Firebase
  - GET /api/v1/auth/me - Get current user
  - GET /api/v1/auth/verify - Verify token
  - POST /api/v1/auth/logout - Logout placeholder
- **Firebase Admin SDK** integration for token verification
- **User model** with firebase_uid field for linking accounts
- **Auth exceptions**: InvalidTokenError, AccountInactiveError, WeakPasswordError
- **get_current_user dependency** for protected endpoints

### Changed
- All protected endpoints now use Firebase token verification
- User repository updated with Firebase-specific methods

### Fixed
- Production white screen issue (wrong VITE_API_URL on Netlify)

---

## [1.6.4] - 2026-01-03 - UX Mobile-First (Phase 12)

### Added
- **Mobile-First UX**: Responsive design with touch-friendly UI
- **Mes Recherches**: Centralized search results page with 30-day retention
- **Unified Product Table**: Consistent product display across features

---

## [1.6.3] - 2025-12-07 - Documentation Cleanup

### Changed
- Removed 110+ obsolete documentation files
- Consolidated essential docs (README, CHANGELOG, API_DOCUMENTATION, ARCHITECTURE, DEPLOYMENT)
- Cleaned up worktrees and branches

---

## [1.6.2] - 2025-12-07 - AutoSourcing Production Ready

### Fixed
- BSR tuple unpacking in keepa_parser_v2 to prevent TypeError
- Keepa category IDs updated to valid /bestsellers IDs
- Centralized category configuration with MCP validation

### Changed
- AutoSourcing now uses KeepaProductFinderService REST API
- Data extraction aligned with REST API format

---

## [1.6.0] - 2025-11 - Phase 7: AutoSourcing Module

### Added
- **AutoSourcing endpoints**: /api/v1/autosourcing/*
  - POST /run - Run discovery job
  - POST /run-custom - Custom parameters
  - GET /latest - Latest job results
  - GET /opportunity-of-day - Daily top pick
  - GET /jobs - List all jobs
  - GET /jobs/{job_id} - Job details
  - GET /jobs/{job_id}/tiers - Tier breakdown
  - GET /profiles - Saved search profiles
  - POST /profiles - Create profile
  - PUT /picks/{pick_id}/action - Mark picks (buy/favorite/skip)
  - GET /to-buy - Buy list
  - GET /favorites - Favorites list
  - GET /stats - AutoSourcing statistics

### Changed
- Real Keepa API integration replacing simulation data
- Batch REST API for efficient queries

---

## [1.5.0] - 2025-11 - Phase 6: Frontend E2E Tests

### Added
- 56 E2E tests with Playwright
- FBA seller competition filter
- Smart Velocity and Textbooks strategies
- Budget Guard for token waste prevention

### Fixed
- Niche discovery price extraction
- BSR ranges for bestsellers
- ProductScoringCache model sync with production schema

---

## [1.4.0] - 2025-10 - Phase 5: Token Control

### Added
- **AutoScheduler**: Automated job scheduling
- **Token safeguards**: Prevent API waste
- @require_tokens decorator for endpoint protection

### Fixed
- Keepa tokensLeft read from JSON body (not HTTP headers)
- HTTP 429 rate limit handling with retry
- Numpy array sanitization for Pydantic

---

## [1.3.0] - 2025-10 - Phase 4: Architecture Improvements

### Added
- Keepa Parser v2 with improved data extraction
- SRP-compliant module splitting
- Comprehensive integration tests

### Changed
- Split keepa_extractors.py into focused modules
- Error handling improvements

### Fixed
- ROI calculation: source_price_factor unified to 0.50
- Sales velocity ZeroDivisionError guard

---

## [1.2.0] - 2025-10 - Phase 3: Keepa Integration

### Added
- Real Keepa API integration
- BSR history tracking
- Price volatility analysis
- Velocity scoring system

### Fixed
- Pydantic V2 validators migration
- ~40 pre-existing failing tests

---

## [1.1.0] - 2025-10 - Phase 2: Business Logic

### Added
- **Analytics endpoints**: /api/v1/analytics/*
  - POST /calculate-analytics
  - POST /calculate-risk-score
  - POST /generate-recommendation
  - POST /product-decision
- **Niche Discovery**: /api/v1/niches/discover
- **Views system**: /api/v1/views/*

---

## [2.0.0] - 2025-09-29 - Database Migration

### Added
- Hybrid Architecture: Backend Render + Database Neon PostgreSQL
- MCP Tools Integration for automated database operations
- Schema Synchronization: 100% SQLAlchemy-Database alignment
- Pagination System with complete metadata

### Changed
- Database Migration: Render PostgreSQL to Neon PostgreSQL
- Connection Pool: 20 to 300-500 concurrent connections (15x improvement)
- BatchStatus Enum: RUNNING to PROCESSING, DONE to COMPLETED
- Pydantic Integration: model_validate() with from_attributes

### Fixed
- Connection Pool Exhaustion eliminated
- Schema Mismatches: all models aligned
- Enum Value Errors fixed
- Missing columns added (started_at, finished_at, strategy_snapshot)

### Performance
- 99.9% Uptime achieved
- <200ms average response time
- Zero connection timeouts since migration
- Scalable to 100+ concurrent users

---

## [1.0.0] - 2025-09 - Initial Release

### Added
- FastAPI backend with SQLAlchemy ORM
- Batch management system
- Analysis results storage
- Health monitoring endpoints
- Render deployment configuration
