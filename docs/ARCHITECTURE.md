# ArbitrageVault BookFinder - Architecture Documentation

**Version**: 1.0.0
**Last Updated**: 2025-11-25
**Status**: Production Alpha

---

## Overview

ArbitrageVault BookFinder is a web application for Amazon book arbitrage analysis. It integrates with the Keepa API to analyze product profitability, velocity, and market conditions.

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI 0.100+ (Python 3.11+) |
| **Database** | PostgreSQL 15+ via Neon |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Frontend** | React 18 + TypeScript + Vite |
| **Styling** | Tailwind CSS |
| **State** | React Query (TanStack Query) |
| **Validation** | Pydantic V2 (backend), Zod (frontend) |
| **Deployment** | Render (backend), Netlify (frontend) |

---

## Architecture Diagram

```
+------------------+     +------------------+     +------------------+
|    Frontend      |     |     Backend      |     |   External       |
|   (Netlify)      |     |    (Render)      |     |   Services       |
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  React 18        | --> |  FastAPI         | --> |  Keepa API       |
|  TypeScript      |     |  (async)         |     |  (Product Data)  |
|  React Query     |     |                  |     |                  |
|  Zod Validation  |     |  SQLAlchemy 2.0  | --> |  Neon PostgreSQL |
|                  |     |  (async ORM)     |     |  (Database)      |
+------------------+     +------------------+     +------------------+
```

---

## Backend Architecture

### Layer Structure (Clean Architecture)

```
backend/app/
+-- api/v1/           # API Layer (HTTP interface)
|   +-- routers/      # Route handlers
|   +-- endpoints/    # Additional endpoints
|
+-- services/         # Business Logic Layer
|   +-- keepa_service.py          # Keepa API integration
|   +-- autosourcing_service.py   # Product discovery
|   +-- unified_analysis.py       # Data transformation
|   +-- scoring_v2.py             # View-specific scoring
|
+-- repositories/     # Data Access Layer
|   +-- base_repository.py        # Generic CRUD + filtering
|   +-- user_repository.py        # User-specific queries
|   +-- analysis_repository.py    # Analysis queries
|
+-- models/           # Domain Models (SQLAlchemy)
|   +-- user.py
|   +-- batch.py
|   +-- analysis.py
|   +-- autosourcing.py
|
+-- schemas/          # Pydantic Schemas (API contracts)
|
+-- core/             # Cross-cutting concerns
    +-- settings.py   # Configuration
    +-- db.py         # Database setup
    +-- auth.py       # Authentication
    +-- calculations.py  # Business calculations
    +-- exceptions.py    # Custom exceptions
```

### Key Design Patterns

1. **Repository Pattern**: Generic `BaseRepository` with pagination, filtering, sorting
2. **Dependency Injection**: FastAPI `Depends()` for services and database sessions
3. **Service Layer**: Business logic isolated from HTTP concerns
4. **Factory Functions**: `get_*_service()` for service instantiation

### Data Flow

```
Request --> Router --> Service --> Repository --> Database
                          |
                          +--> External API (Keepa)
                          |
Response <-- Router <-- Service <-- Calculations
```

---

## Frontend Architecture

### Component Structure

```
frontend/src/
+-- components/       # Reusable UI components
|   +-- ViewResultsTable.tsx    # Main results display
|   +-- ViewResultsRow.tsx      # Expandable product row
|   +-- ProgressBar.tsx         # Analysis progress
|   +-- ScoreBreakdown.tsx      # Score visualization
|
+-- pages/            # Route-level components
|   +-- Dashboard.tsx
|   +-- AutoSourcing.tsx
|   +-- NicheDiscovery.tsx
|
+-- hooks/            # Custom React hooks
|   +-- useKeepaAnalysis.ts
|   +-- useAutoSourcing.ts
|
+-- services/         # API client layer
|   +-- api.ts        # Axios/fetch wrapper
|
+-- types/            # TypeScript definitions
|   +-- views.ts
|   +-- analysis.ts
|
+-- utils/            # Helper functions
```

### State Management

- **Server State**: React Query for API data caching
- **Local State**: React useState/useReducer for UI state
- **No Global Store**: Deliberately avoiding Redux complexity

---

## Database Schema

### Core Tables

```sql
-- Users
users (id, email, password_hash, role, created_at, updated_at)

-- Analysis Batches
batches (id, user_id, name, status, items_total, items_processed, ...)

-- Individual Analyses
analyses (id, batch_id, isbn_or_asin, buy_price, roi_percent, velocity_score, ...)

-- AutoSourcing Jobs
autosourcing_jobs (id, user_id, status, discovery_config, scoring_config, ...)

-- AutoSourcing Picks
autosourcing_picks (id, job_id, asin, score, roi_pct, velocity_score, ...)
```

### Relationships

- User 1:N Batches
- Batch 1:N Analyses
- User 1:N AutoSourcingJobs
- AutoSourcingJob 1:N AutoSourcingPicks

---

## API Design

### Versioning Strategy

All endpoints are prefixed with `/api/v1/`. Current structure:

| Prefix | Router | Purpose |
|--------|--------|---------|
| `/api/v1/keepa` | keepa.py | Keepa integration |
| `/api/v1/autosourcing` | autosourcing.py | Product discovery |
| `/api/v1/views` | views.py | View-specific scoring |
| `/api/v1/config` | config.py | Business configuration |
| `/api/v1/health` | health.py | Health checks |

### Authentication

- JWT tokens via `/api/v1/auth/login`
- Token refresh via `/api/v1/auth/refresh`
- Protected routes use `Depends(get_current_user)`

### Error Handling

Custom exceptions in `core/exceptions.py`:
- `InsufficientTokensError` - Keepa API quota
- `KeepaRateLimitError` - Rate limiting
- `InvalidFilterFieldError` - Query validation
- `BusinessValidationError` - Business rule violations

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Keepa API
KEEPA_API_KEY=xxx

# Auth
SECRET_KEY=xxx
JWT_ALGORITHM=HS256

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Business Configuration

Hierarchical config system with overrides:
- Global defaults
- Per-domain overrides (US, UK, etc.)
- Per-category overrides (books, electronics, etc.)

---

## Deployment

### Backend (Render)

- Web Service with auto-deploy from `main` branch
- Health check: `GET /health`
- Environment: Python 3.11

### Frontend (Netlify)

- Static site with CI/CD from `main` branch
- Build command: `npm run build`
- Publish directory: `dist`

### Database (Neon)

- PostgreSQL 15 serverless
- Connection pooling enabled
- SSL required

---

## Testing Strategy

### Test Types

| Type | Location | Purpose |
|------|----------|---------|
| Unit | `tests/unit/` | Isolated component testing |
| Integration | `tests/integration/` | Service + DB testing |
| E2E | `tests/e2e/` | Full flow testing (Playwright) |
| API | `tests/api/` | Endpoint contract testing |

### Running Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run build  # TypeScript validation
```

---

## Known Limitations

1. **Large Files**: Some service files exceed 800 LOC (planned refactor)
2. **Test Coverage**: Estimated ~33% (target: 70%)
3. **API Versioning**: No v2 deprecation plan yet

---

## Future Improvements (Roadmap to 9/10)

1. **Split large modules** (SRP violations)
2. **Implement proper DI** for all services
3. **Increase test coverage** to 70%+
4. **Add ADR documentation** for architecture decisions
5. **Create deployment runbooks**

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Keepa API Documentation](https://keepa.com/#!discuss/t/keepa-api-documentation/4)
- [React Query](https://tanstack.com/query/latest)
