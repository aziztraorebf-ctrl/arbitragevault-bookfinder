# ArbitrageVault - Structure Complète du Projet

> **Vue d'ensemble visuelle** de l'organisation backend

**Dernière mise à jour** : 28 Novembre 2025

---

## 📁 Arborescence Complète

```
arbitragevault_bookfinder/
│
├── backend/                           # Backend FastAPI
│   ├── app/                           # Application principale
│   │   │
│   │   ├── api/                       # API Layer
│   │   │   └── v1/
│   │   │       ├── endpoints/         # Endpoints complexes
│   │   │       │   ├── analytics.py           # Analytics calculations
│   │   │       │   ├── asin_history.py        # ASIN tracking
│   │   │       │   ├── config.py              # Config preview
│   │   │       │   ├── niches.py              # Niche discovery
│   │   │       │   └── products.py            # Product discovery
│   │   │       │
│   │   │       └── routers/           # Main routers
│   │   │           ├── analyses.py            # Analysis CRUD
│   │   │           ├── auth.py                # JWT authentication
│   │   │           ├── autoscheduler.py       # AutoScheduler control
│   │   │           ├── autosourcing.py        # AutoSourcing jobs
│   │   │           ├── batches.py             # Batch CRUD
│   │   │           ├── config.py              # Business config
│   │   │           ├── health.py              # Health checks
│   │   │           ├── views.py               # Strategic views
│   │   │           │
│   │   │           ├── keepa.py               # Keepa router (FACADE) ⭐
│   │   │           ├── keepa_schemas.py       # Pydantic models
│   │   │           ├── keepa_utils.py         # Utility functions
│   │   │           └── keepa_debug.py         # Debug endpoints
│   │   │
│   │   ├── services/                  # Business Logic Layer
│   │   │   │
│   │   │   ├── Keepa Integration (10 modules) ⭐
│   │   │   ├── keepa_service.py               # Main service (FACADE)
│   │   │   ├── keepa_models.py                # Data classes & enums
│   │   │   ├── keepa_cache.py                 # Multi-tier caching
│   │   │   ├── keepa_throttle.py              # Token bucket rate limiter
│   │   │   ├── keepa_constants.py             # Constants & mappings
│   │   │   ├── keepa_extractors.py            # Data extraction
│   │   │   ├── keepa_parser_v2.py             # Response parsing
│   │   │   ├── keepa_product_finder.py        # Product discovery
│   │   │   └── keepa_service_factory.py       # DI factory
│   │   │   │
│   │   │   ├── Analytics Services
│   │   │   ├── advanced_analytics_service.py  # Comprehensive analytics
│   │   │   ├── risk_scoring_service.py        # 5-component risk score
│   │   │   ├── recommendation_engine_service.py  # 5-tier recommendations
│   │   │   ├── sales_velocity_service.py      # Velocity intelligence
│   │   │   └── pricing_service.py             # Price calculations
│   │   │   │
│   │   │   ├── AutoSourcing Services
│   │   │   ├── autosourcing_service.py        # Main orchestration
│   │   │   ├── autosourcing_validator.py      # Request validation
│   │   │   ├── autosourcing_cost_estimator.py # Cost prediction
│   │   │   └── autoscheduler_metrics.py       # Scheduler metrics
│   │   │   │
│   │   │   ├── Niche Discovery
│   │   │   ├── niche_discovery_service.py     # Niche analysis
│   │   │   ├── niche_scoring_service.py       # Niche scoring
│   │   │   ├── niche_templates.py             # Niche templates
│   │   │   └── category_analyzer.py           # Category analysis
│   │   │   │
│   │   │   ├── Other Services
│   │   │   ├── amazon_check_service.py        # Amazon presence detection
│   │   │   ├── amazon_filter_service.py       # Amazon filtering
│   │   │   ├── asin_tracking_service.py       # ASIN history tracking
│   │   │   ├── bookmark_service.py            # Saved niches
│   │   │   ├── business_config_service.py     # Config management
│   │   │   ├── cache_service.py               # Generic caching
│   │   │   ├── config_preview_service.py      # Config preview
│   │   │   ├── config_service.py              # Legacy config
│   │   │   ├── scoring_v2.py                  # Advanced scoring v2
│   │   │   ├── stock_estimate_service.py      # Stock availability
│   │   │   ├── strategic_views_service.py     # View calculations
│   │   │   └── unified_analysis.py            # Unified pipeline
│   │   │
│   │   ├── repositories/              # Data Access Layer
│   │   │   ├── base_repository.py             # Generic CRUD
│   │   │   ├── analysis_repository.py         # Analysis persistence
│   │   │   ├── batch_repository.py            # Batch persistence
│   │   │   ├── token_repo.py                  # Token tracking
│   │   │   └── user_repository.py             # User management
│   │   │
│   │   ├── models/                    # ORM Models (Database Schema)
│   │   │   ├── base.py                        # Base model
│   │   │   ├── analysis.py                    # Analysis table
│   │   │   ├── analytics.py                   # Analytics cache
│   │   │   ├── autosourcing.py                # AutoSourcing jobs/picks
│   │   │   ├── batch.py                       # Batch table
│   │   │   ├── bookmark.py                    # Saved niches
│   │   │   ├── business_config.py             # Business config
│   │   │   ├── config.py                      # Legacy config
│   │   │   ├── keepa_models.py                # Keepa cache models
│   │   │   ├── niche.py                       # Niche discovery
│   │   │   └── user.py                        # User table
│   │   │
│   │   ├── core/                      # Core Utilities (Cross-cutting)
│   │   │   ├── settings.py                    # Pydantic Settings
│   │   │   ├── db.py                          # Database connection
│   │   │   ├── exceptions.py                  # Custom exceptions
│   │   │   ├── logging.py                     # Logging config
│   │   │   ├── auth.py                        # JWT authentication
│   │   │   ├── security.py                    # Security utils
│   │   │   ├── cors.py                        # CORS config
│   │   │   ├── pagination.py                  # Pagination helper
│   │   │   ├── token_costs.py                 # Token tracking
│   │   │   ├── version.py                     # App version
│   │   │   │
│   │   │   ├── Business Calculations
│   │   │   ├── calculations.py                # Generic calculations
│   │   │   ├── roi_calculations.py            # ROI formulas
│   │   │   ├── velocity_calculations.py       # Velocity scoring
│   │   │   ├── advanced_scoring.py            # Combined scoring
│   │   │   └── fees_config.py                 # Fee configurations
│   │   │   │
│   │   │   └── guards/                # Request Guards
│   │   │       └── require_tokens.py          # Token validation
│   │   │
│   │   ├── routers/                   # Additional Routers
│   │   │   ├── stock_estimate.py              # Stock estimates
│   │   │   ├── strategic_views.py             # Strategic views
│   │   │   ├── niche_discovery.py             # Niche API
│   │   │   └── bookmarks.py                   # Bookmarks API
│   │   │
│   │   └── main.py                    # ⭐ Application Entry Point
│   │
│   ├── tests/                         # Test Suite
│   │   ├── api/                       # API tests
│   │   ├── services/                  # Service tests
│   │   ├── repositories/              # Repository tests
│   │   └── core/                      # Core tests
│   │
│   ├── alembic/                       # Database Migrations
│   │   ├── versions/                  # Migration scripts
│   │   └── env.py                     # Alembic config
│   │
│   ├── docs/                          # ⭐ Documentation
│   │   ├── README.md                  # Documentation index
│   │   ├── ARCHITECTURE.md            # Architecture complete
│   │   ├── PROJECT_STRUCTURE.md       # This file
│   │   ├── AUTOSOURCING_SAFEGUARDS.md # Safeguards Phase 7.0
│   │   └── audits/                    # Validation audits
│   │
│   ├── .env.example                   # Environment template
│   ├── requirements.txt               # Python dependencies
│   ├── pytest.ini                     # Pytest configuration
│   └── alembic.ini                    # Alembic configuration
│
├── frontend/                          # Frontend React (not covered here)
│
├── .claude/                           # Claude Code configuration
│   ├── CLAUDE.md                      # Project instructions
│   └── CODE_STYLE_RULES.md            # Code style enforcement
│
├── .github/                           # GitHub configuration
│   └── workflows/                     # CI/CD pipelines
│
├── .gitignore                         # Git ignore patterns
└── README.md                          # Project README
```

---

## 📊 Statistiques par Couche

### API Layer (Routers + Endpoints)

| Module | Type | LOC | Responsabilité |
|--------|------|-----|----------------|
| keepa.py | Router (Facade) | 379 | Orchestration Keepa endpoints |
| keepa_schemas.py | Pydantic | 156 | Request/Response validation |
| keepa_utils.py | Utils | 160 | Utility functions |
| keepa_debug.py | Debug | 380 | Health/Debug endpoints |
| analyses.py | Router | ~150 | Analysis CRUD |
| batches.py | Router | ~120 | Batch CRUD |
| autosourcing.py | Router | ~250 | AutoSourcing API |
| views.py | Router | ~180 | Strategic views scoring |
| **Total API** | - | **~1,775** | - |

### Service Layer

| Catégorie | Modules | LOC Total | Description |
|-----------|---------|-----------|-------------|
| **Keepa Integration** | 10 modules | ~1,800 | Keepa API client + utilities |
| **Analytics** | 5 modules | ~800 | ROI, velocity, risk, recommendations |
| **AutoSourcing** | 4 modules | ~600 | Product discovery automation |
| **Niche Discovery** | 4 modules | ~500 | Niche analysis & scoring |
| **Other Services** | 12 modules | ~1,500 | Config, cache, tracking, etc. |
| **Total Services** | **35 modules** | **~5,200** | - |

### Repository Layer

| Repository | LOC | Tables |
|------------|-----|--------|
| base_repository.py | ~80 | Generic CRUD |
| analysis_repository.py | ~120 | analyses |
| batch_repository.py | ~100 | batches |
| user_repository.py | ~90 | users |
| token_repo.py | ~60 | token_tracking |
| **Total Repositories** | **~450** | **5 tables** |

### Model Layer (ORM)

| Model | LOC | Relations |
|-------|-----|-----------|
| analysis.py | ~60 | → batch |
| batch.py | ~50 | → analyses |
| autosourcing.py | ~120 | jobs → picks |
| business_config.py | ~80 | - |
| bookmark.py | ~50 | - |
| user.py | ~70 | → batches, analyses |
| **Total Models** | **~430** | **Multiple** |

### Core Layer

| Module | LOC | Type |
|--------|-----|------|
| settings.py | ~150 | Pydantic Settings |
| db.py | ~100 | Database setup |
| exceptions.py | ~80 | Custom exceptions |
| roi_calculations.py | ~120 | ROI formulas |
| velocity_calculations.py | ~150 | Velocity scoring |
| advanced_scoring.py | ~250 | Combined scoring |
| **Total Core** | **~850** | **Utilities** |

---

## 🎯 Points d'Entrée Principaux

### 1. Application Startup

```
main.py (100 LOC)
├─ Settings (core/settings.py)
├─ Sentry initialization
├─ CORS configuration (core/cors.py)
├─ Database lifespan (core/db.py)
└─ Router registration
   ├─ /api/v1/health
   ├─ /api/v1/auth
   ├─ /api/v1/keepa      ⭐ Main Keepa integration
   ├─ /api/v1/autosourcing
   ├─ /api/v1/analyses
   └─ ... (12 routers total)
```

### 2. Keepa Integration Entrypoint

```
keepa.py (API Router)
├─ POST /ingest                # Batch ASIN ingestion
├─ GET /{asin}/metrics         # Product metrics
├─ GET /{asin}/raw             # Raw Keepa data
└─ Debug endpoints
   ├─ GET /health              # Health check
   ├─ GET /test                # Connection test
   └─ POST /debug/analyze      # Debug analysis

Dependencies:
├─ keepa_service.py (Service Facade)
│  ├─ keepa_cache.py (Multi-tier cache)
│  ├─ keepa_throttle.py (Rate limiter)
│  └─ keepa_models.py (Data classes)
└─ keepa_utils.py (Utilities)
   └─ analyze_product() → ROI, Velocity, Recommendation
```

### 3. AutoSourcing Entrypoint

```
autosourcing.py (API Router)
├─ POST /run_custom            # Run custom search
├─ GET /latest                 # Latest results
├─ GET /jobs                   # Recent jobs
├─ GET /jobs/{id}              # Job details
├─ PUT /picks/{id}/action      # Update pick action
└─ GET /to_buy                 # Shopping list

Pipeline:
autosourcing_service.py
├─ autosourcing_validator.py   # Validate request
├─ autosourcing_cost_estimator.py  # Estimate tokens
├─ keepa_product_finder.py     # Discover products
├─ keepa_service.py            # Fetch product data
├─ scoring_v2.py               # Score & filter
└─ autosourcing models         # Persist results
```

---

## 🔗 Dépendances Inter-Modules

### Keepa Integration Dependencies

```
keepa.py (Router)
  ├─→ keepa_schemas.py         # Pydantic validation
  ├─→ keepa_utils.py           # Utility functions
  ├─→ keepa_debug.py           # Debug endpoints
  └─→ keepa_service.py         # Main service
      ├─→ keepa_models.py      # Data classes
      ├─→ keepa_cache.py       # Caching
      ├─→ keepa_throttle.py    # Rate limiting
      ├─→ keepa_parser_v2.py   # Response parsing
      └─→ core.exceptions      # Custom errors
```

### AutoSourcing Dependencies

```
autosourcing.py (Router)
  └─→ autosourcing_service.py
      ├─→ autosourcing_validator.py
      ├─→ autosourcing_cost_estimator.py
      ├─→ keepa_product_finder.py
      │   └─→ keepa_service.py
      ├─→ scoring_v2.py
      │   ├─→ advanced_scoring.py (core)
      │   ├─→ roi_calculations.py (core)
      │   └─→ velocity_calculations.py (core)
      └─→ autosourcing models/repositories
```

### Analytics Dependencies

```
analytics.py (Endpoint)
  └─→ advanced_analytics_service.py
      ├─→ risk_scoring_service.py
      │   └─→ core calculations
      ├─→ recommendation_engine_service.py
      │   └─→ advanced_scoring.py (core)
      ├─→ sales_velocity_service.py
      │   └─→ velocity_calculations.py (core)
      └─→ pricing_service.py
          └─→ roi_calculations.py (core)
```

---

## 📈 Métriques Globales

### Code Coverage

| Couche | Modules | LOC Total | Test Coverage |
|--------|---------|-----------|---------------|
| API Layer | 17 | ~1,775 | ~75% |
| Service Layer | 35 | ~5,200 | ~80% |
| Repository Layer | 5 | ~450 | ~85% |
| Model Layer | 11 | ~430 | ~90% |
| Core Layer | 15 | ~850 | ~95% |
| **Total** | **83** | **~8,705** | **~82%** |

### Complexité par Module

**Top 5 modules les plus complexes** :

1. `keepa_service.py` - 668 LOC (Facade + HTTP client)
2. `autosourcing_service.py` - ~400 LOC (Orchestration pipeline)
3. `keepa_debug.py` - 380 LOC (Debug endpoints)
4. `keepa.py` - 379 LOC (API Facade)
5. `advanced_scoring.py` - 250 LOC (Scoring algorithms)

### Refactoring Impact (Keepa SRP)

**Avant refactoring** :
- `keepa.py` (monolithic) : ~1,500 LOC
- Responsabilités mélangées

**Après refactoring** (10 modules) :
- `keepa.py` (facade) : 379 LOC
- `keepa_service.py` (facade) : 668 LOC
- 8 modules spécialisés : ~1,137 LOC
- **Total** : ~2,184 LOC (+45% code mais -70% complexité)

**Bénéfices** :
- ✅ Single Responsibility Principle respecté
- ✅ Testabilité améliorée (modules isolés)
- ✅ Maintenance simplifiée (changements localisés)
- ✅ Réutilisabilité accrue (cache, throttle indépendants)

---

## 🚀 Évolutions Futures Prévues

### Phase 4 - Performance Optimization
- [ ] Async batch processing optimisé
- [ ] Connection pooling PostgreSQL
- [ ] Redis cache layer (complément cache mémoire)

### Phase 5 - Features Expansion
- [ ] Real-time price tracking (WebSocket)
- [ ] ML-based recommendation engine
- [ ] Multi-marketplace support (UK, DE, FR)

### Phase 6 - Scalability
- [ ] Microservices architecture (Keepa service séparé)
- [ ] Message queue (RabbitMQ/Celery) pour jobs longs
- [ ] Horizontal scaling avec load balancer

---

## 📚 Références

**Documentation détaillée** :
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture complète avec patterns
- [README.md](./README.md) - Index documentation

**Code source** :
- Backend : `backend/app/`
- Tests : `backend/tests/`
- Migrations : `backend/alembic/versions/`

**Configuration** :
- `.claude/CLAUDE.md` - Instructions projet
- `backend/.env.example` - Variables environnement
- `backend/alembic.ini` - Config migrations

---

**Dernière mise à jour** : 28 Novembre 2025
**Mainteneur** : Équipe ArbitrageVault + Claude Code
**License** : Proprietary
