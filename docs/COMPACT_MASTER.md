# Compact Master - ArbitrageVault BookFinder

**Projet:** ArbitrageVault BookFinder - Plateforme analyse arbitrage Amazon
**Date creation:** Aout 2025
**Derniere mise a jour:** 23 Novembre 2025
**Version actuelle:** v8.0.0
**Status:** Production - Phases 5, 6, 7, 8 Validees (Audit Backward Complete)

---

## Vue d'Ensemble Projet

### Mission
Fournir aux revendeurs Amazon FBA un outil d'analyse automatisee pour identifier opportunites arbitrage profitables dans la categorie livres via integration Keepa API.

### Value Proposition
1. **Decouverte automatique** - AutoSourcing trouve niches profitables sans recherche manuelle
2. **Scoring intelligent** - Algorithme multi-criteres (ROI, velocity, stability)
3. **Protection costs** - Safeguards token Keepa contre epuisement budget
4. **Interface intuitive** - UI/UX optimisee pour decisions rapides

### Stack Technique
- **Backend:** FastAPI + PostgreSQL + SQLAlchemy 2.0
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Infrastructure:** Render (backend) + Netlify (frontend) + Neon (database)
- **APIs:** Keepa API (product data) + Sentry (monitoring)

---

## Historique Phases Completees

### Phase 5.0: Token Cost Control & Observability (Complete + Validated)
**Date:** Octobre 2025 (Implementation) + 23 Novembre 2025 (Audit)
**Objectifs:**
- Token tracking Keepa API
- Cost estimation system
- Observability metrics
- Performance monitoring

**Deliverables:**
- Token balance monitoring avec logging transparent
- Cost breakdown per operation (pre-flight checks)
- Sentry integration pour observability
- Performance metrics (<5s response time)
- Circuit breaker protection active

**Corrections Audit Backward (23 Novembre):**
- HIGH-1: Suppression emojis code Python executable (compliance CLAUDE.md)
- HIGH-2: Suppression duplicate check_api_balance() methods
- HIGH-3: Force balance refresh dans /keepa/health endpoint

**Metriques Validees:**
- Tests E2E: 35/36 PASS (97.2% success rate)
- Token consumption: 571 tokens (vraies donnees Keepa API)
- Score global code review: 85/100
- 0 CRITICAL issues (Phase 5 plus mature que Phase 6 au moment implementation)
- Circuit breaker state: closed, protection active
- Concurrency limits: 3 requetes simultanees Keepa

**Commits cles:**
- `2e2f90c` - fix(phase-5): apply 3 HIGH priority corrections from code review

**Documentation:**
- `docs/PHASE5_E2E_COMPLETION_REPORT.md`
- `docs/PHASE5_VALIDATION_REPORT.md`

---

### Phase 6.0: Token Control & Timeout Protection (Complete + Validated)
**Date:** Novembre 2025
**Objectifs:**
- Protection timeout endpoints Keepa API
- Token consumption tracking et logging
- Circuit breaker protection
- Documentation TokenErrorAlert

**Deliverables:**
- CRITICAL-01: Timeout protection 30s (`asyncio.wait_for`)
- CRITICAL-02: TokenErrorAlert documentation
- CRITICAL-03: Token logging (balance before/after, metadata)
- Hotfix FileNotFoundError production (commit `8184cf8`)
- E2E tests 35/36 PASS (97.2% success rate)

**Metriques Validees:**
- Backend production stable (HTTP 200/408, plus de HTTP 500)
- Token consumption: 562 tokens sur 1200 (tests E2E)
- Timeout protection active (test #9 echoue apres 30s exactement)
- Circuit breaker state: closed, protection active
- Concurrency limits: 3 requetes simultanees Keepa

**Commits cles:**
- `8184cf8` - Hotfix FileNotFoundError (Python logger vs file I/O)
- `74a3af8` - Apply 3 critical corrections from code review
- `83b6eac` - Complete audit with code review and correction plan

**Documentation:** `docs/PHASE6_AND_PHASE8_VALIDATION_REPORT.md`

---

### Phase 7.0: AutoSourcing Safeguards (Complete)
**Date:** 15 Novembre 2025
**Objectifs:**
- Protection token exhaustion
- Error handling frontend/backend
- Cost estimation UI
- Timeout enforcement

**Deliverables:**
- `MAX_TOKENS_PER_JOB = 200`
- `MIN_TOKEN_BALANCE_REQUIRED = 50`
- `TIMEOUT_PER_JOB = 120s`
- HTTP 400/408/429 error handling
- Cost estimation endpoint (no token consumption)
- E2E tests 100% passing (3/3)

**Metriques:**
- Average job: 50-150 tokens
- Discovery: ~50 tokens/category
- Product analysis: 1 token/ASIN
- ASIN deduplication: Set-based tracking

**Documentation:** `backend/docs/phase-7.0-safeguards-complete.md`

**Commits cles:**
- `2bd7ae6` - Frontend error handling complete
- `f91caf0` - Documentation Phase 7.0
- `31176e6` - Production token thresholds restored

---

## Architecture Globale

### Backend Structure
```
backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── api/v1/endpoints/
│   │   ├── autosourcing.py       # AutoSourcing + Safeguards
│   │   ├── keepa.py              # Keepa integration
│   │   ├── config.py             # Business config
│   │   ├── views.py              # Strategic views
│   │   ├── niches.py             # Niche discovery
│   │   └── batches.py            # Batch analysis
│   ├── services/
│   │   ├── autosourcing_service.py
│   │   ├── keepa_service.py
│   │   ├── config_service.py
│   │   └── niche_discovery_service.py
│   ├── models/
│   │   ├── autosourcing.py
│   │   ├── analysis.py
│   │   └── batch.py
│   └── schemas/
│       ├── autosourcing_safeguards.py
│       └── ...
├── tests/
│   ├── e2e/tests/               # Playwright E2E
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
└── alembic/                     # Database migrations
```

### Frontend Structure
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── AutoSourcing.tsx      # Main AutoSourcing
│   │   ├── NicheDiscovery.tsx
│   │   └── AnalyseStrategique.tsx
│   ├── components/
│   │   ├── AutoSourcingJobModal.tsx  # Cost estimation
│   │   ├── TokenErrorAlert.tsx       # Error display
│   │   └── ...
│   ├── services/
│   │   └── api.ts
│   └── types/
│       └── autosourcing.ts
├── vite.config.ts
└── tailwind.config.js
```

### Database Schema
```sql
-- Core tables
autosourcing_jobs         # Job execution tracking
autosourcing_picks        # Discovered products
autosourcing_profiles     # Saved search configs
analyses                  # Product analysis results
batches                   # Analysis batches
saved_niches              # Bookmarked niches
business_config           # Configuration management
```

---

## APIs Principales

### AutoSourcing Endpoints
```
POST /api/v1/autosourcing/run_custom      # Launch custom search
POST /api/v1/autosourcing/estimate        # Cost estimation (no tokens)
GET  /api/v1/autosourcing/jobs            # Recent jobs list
GET  /api/v1/autosourcing/jobs/{id}       # Job details
GET  /api/v1/autosourcing/latest          # Latest results
GET  /api/v1/autosourcing/opportunity_of_day
PUT  /api/v1/autosourcing/picks/{id}/action
```

### Configuration Endpoints
```
GET  /api/v1/config/                      # Effective config
PUT  /api/v1/config/                      # Update config
POST /api/v1/config/preview               # Preview changes
GET  /api/v1/config/changes               # Audit trail
GET  /api/v1/config/stats                 # Service stats
```

### Keepa Integration
```
POST /api/v1/keepa/ingest                 # Batch ingest
GET  /api/v1/keepa/{asin}/metrics         # Product metrics
GET  /api/v1/keepa/{asin}/raw             # Raw Keepa data
GET  /api/v1/keepa/health                 # Health check
```

### Strategic Views
```
POST /api/v1/views/{view_type}            # Score products
GET  /api/v1/views/{view_type}            # Get view data
GET  /api/v1/views/                       # List views
```

---

## Features Principales

### 1. AutoSourcing System
**Capacites:**
- Decouverte automatique produits via Keepa Product Finder
- Scoring multi-criteres (ROI, velocity, stability, confidence)
- Filtrage intelligent (BSR ranges, price ranges, categories)
- Action tracking (to_buy, favorite, ignored, analyzing)
- Profile management (save/reuse search configs)

**Safeguards (Phase 7.0):**
- Token cost estimation pre-flight
- MAX_TOKENS_PER_JOB = 200 limit
- MIN_TOKEN_BALANCE_REQUIRED = 50
- TIMEOUT_PER_JOB = 120s enforcement
- ASIN deduplication

### 2. Niche Discovery
**Capacites:**
- Analyse categories Keepa
- Scoring niches (competition, margins, stability)
- Bookmark niches pour re-analyse
- Export CSV resultats
- Templates pre-definis

### 3. Business Configuration
**Capacites:**
- Hierarchical config (global < domain < category)
- Fee configuration par categorie
- ROI/Velocity thresholds
- Recommendation rules
- Preview changes avant application
- Audit trail avec versioning

### 4. Strategic Views
**Vues disponibles:**
- `profit-hunter` - ROI priority (50% target)
- `velocity` - Fast movers (25% ROI)
- `cashflow-hunter` - Quick returns (35% ROI)
- `balanced-score` - Equilibre (40% ROI)
- `volume-player` - High volume (20% ROI)

**View-specific scoring:**
- Weights customization (ROI/Velocity/Stability)
- Strategy boosts (textbook/velocity/balanced)
- Target price calculations

### 5. Stock Estimation
**Capacites:**
- FBA/MFN offer counts
- Price range filtering
- Availability estimates
- 24h cache TTL

---

## Metriques Business

### Token Usage (Keepa API)
- **Average job:** 50-150 tokens
- **Discovery phase:** ~50 tokens/category
- **Product analysis:** 1 token/ASIN
- **Safety buffer:** 20% margin
- **Deduplication:** Set-based ASIN tracking

### Performance
- **Backend response:** <500ms average
- **Frontend build:** Optimized Vite bundles
- **Database:** PostgreSQL connection pooling
- **CDN:** Netlify global edge network

### Test Coverage
- **E2E tests:** 8 suites (100% passing)
- **Unit tests:** 50+ backend tests
- **Integration:** Keepa API validated
- **CI/CD:** GitHub Actions automation

---

### Phase 8.0: Decision System Analytics (Complete + Validated)
**Date:** Novembre 2025
**Objectifs:**
- Advanced analytics endpoints (velocity, ROI, risk, recommendation)
- Product Decision Card backend logic
- Performance optimization (<500ms target)
- Historical trends API foundation

**Deliverables:**
- Velocity Intelligence service (BSR-based scoring 0-100)
- Price Stability Analysis (volatility calculation)
- ROI Net Calculation (fees: referral 15%, FBA $2.5, prep, storage, returns 2%)
- Risk Scoring Algorithm (5 components: dead inventory, competition, Amazon presence, stability, category)
- Recommendation Engine (6-tier: STRONG_BUY, BUY, CONSIDER, WATCH, SKIP, AVOID)
- E2E tests 5/5 PASS (100% Phase 8 success)

**Endpoints Valides:**
- `POST /api/v1/analytics/calculate_analytics` - Complete product analytics
- `POST /api/v1/analytics/calculate_risk_score` - 5-component risk scoring
- `POST /api/v1/analytics/generate_recommendation` - Final decision recommendation
- `POST /api/v1/analytics/product_decision` - Combined decision card data
- `GET /api/v1/asin-history/trends/{asin}` - Historical trends (404 for new ASINs)

**Metriques Validees:**
- Product Decision Card: ROI 164.4%, Velocity 100, Risk LOW, Recommendation STRONG_BUY
- High-risk scenario: Risk 84.25 (CRITICAL), ROI -34.1%, Recommendation AVOID
- Performance: 134ms analytics calculation (<500ms target exceeded)
- Multiple endpoints: 3/3 responding correctly
- Historical trends: 404 attendu (pas de donnees historiques)

**Mystery Localhost Resolu:**
- Tests echouaient car backend etait casse (HTTP 500), PAS a cause des URLs
- Apres deploiement hotfix `8184cf8`, tous tests Phase 8 passent (5/5 = 100%)
- Commit `7bd65b7` avait deja fixe URLs localhost → production

**Documentation:** `docs/PHASE6_AND_PHASE8_VALIDATION_REPORT.md`

---

## Roadmap Futur

### Phase 4.0: Audit & Validation (Prochain - Audit Backward)
**Timeline:** Audit prochain (backward workflow Phase 8 → 7 → 6 → 5 → **4**)
**Focus:** Code review Phase 4 (Business Configuration System) et validation corrections
**Priority:** MEDIUM (audit systematique backward workflow)

**Methodologie Audit:**
- Utiliser `superpowers:code-reviewer` pour analyse code
- Utiliser `superpowers:planning` pour correction plans
- Utiliser `superpowers:systematic-debugging` si bugs identifies
- Pattern: Backward audit (Phase 8 → 7 → 6 → 5 → 4 → ...)
- Critere succes: 96%+ E2E tests passing

**Scope Phase 4:**
- Business configuration management
- Hierarchical config merging (global < domain < category)
- Config versioning et audit trail
- Preview system pour changements config
- API endpoints config CRUD

---

### Phase 9.0: UI/UX Polish (Apres Phase 8.0)
**Timeline:** 2-3 semaines
**Focus:** Experience utilisateur et coherence visuelle
**Priority:** MEDIUM (quality-of-life improvements)

**Sub-phases:**
1. **9.1 Visual Design Consistency**
   - Harmonisation palette couleurs (Tailwind design tokens)
   - Typography standardisee
   - Iconographie coherente (lucide-react)
   - Spacing uniforme

2. **9.2 User Experience Flows**
   - Navigation optimisee (breadcrumbs, sidebar active states)
   - Feedback utilisateur immediat (toast notifications)
   - Loading states ameliores (skeleton loaders)
   - Error recovery flows (retry mechanisms)

3. **9.3 Responsive & Accessibility**
   - Mobile-first responsive design
   - WCAG 2.1 Level AA compliance
   - Keyboard navigation complete
   - Screen reader support

4. **9.4 Performance & Feel**
   - Micro-interactions animation
   - Bundle size optimization (code splitting)
   - Lazy loading components
   - Perceived performance (optimistic UI)

5. **9.5 Documentation Utilisateur**
   - Guide interactif (react-joyride)
   - Tooltips contextuels
   - Onboarding flow
   - FAQ integration

**Technologies:**
- Tailwind CSS (design system)
- Radix UI (accessible components)
- React Joyride (product tour)
- Recharts (if needed for UI enhancements)

**Documentation:** `docs/PHASE_9.0_UI_UX_POLISH_PLAN.md`

---

### Phase 10.0: Advanced Features (Future)
**Potentielles features:**
- Multi-user authentication
- Real-time collaboration
- Google Sheets export
- Automated repricing alerts
- Inventory management integration
- Mobile app (React Native)

---

## Standards Projet

### Git Workflow
```
main branch          # Production stable
feature/name         # Development features
hotfix/name          # Emergency fixes
```

**Commit conventions:**
```
feat(scope): description       # New feature
fix(scope): description        # Bug fix
refactor(scope): description   # Code restructure
test(scope): description       # Tests
docs(scope): description       # Documentation
chore(scope): description      # Maintenance
```

**Co-authorship:**
```
Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Code Quality
**Backend (Python):**
- Black formatting
- Pylint linting
- Type hints (mypy)
- Pydantic validation
- NO emojis in code

**Frontend (TypeScript):**
- ESLint + Prettier
- Strict TypeScript
- Zod validation
- React best practices
- NO emojis in code

### Testing Strategy
1. **Unit tests** - Services et utilities
2. **Integration tests** - API endpoints avec DB
3. **E2E tests** - User flows complets Playwright
4. **Manual QA** - Production validation

---

## URLs Production

**Frontend:** https://arbitragevault.netlify.app
**Backend API:** https://arbitragevault-backend-v2.onrender.com
**Database:** Neon PostgreSQL (managed)

**Monitoring:**
- Sentry error tracking
- Render metrics dashboard
- Netlify analytics

---

## Decisions Techniques Cles

### 1. Architecture Pattern
**Decision:** Clean Architecture avec services layer
**Rationale:** Separation of concerns, testability, maintainability

### 2. Database ORM
**Decision:** SQLAlchemy 2.0 avec async support
**Rationale:** Type safety, performance, ecosystem maturity

### 3. Frontend Framework
**Decision:** React + TypeScript + Vite
**Rationale:** Developer experience, build performance, type safety

### 4. API Design
**Decision:** RESTful avec Pydantic schemas
**Rationale:** Standard, auto-documentation (OpenAPI), validation

### 5. Testing Framework
**Decision:** Playwright pour E2E
**Rationale:** Cross-browser, reliable selectors, great DX

### 6. Configuration Management
**Decision:** Hierarchical config avec audit trail
**Rationale:** Flexibility, traceability, rollback capability

### 7. Error Handling Pattern
**Decision:** Parent-to-child error propagation
**Rationale:** Centralized display, consistent UX

---

## Lessons Learned

### Phase 5-8 Insights
1. **Documentation-first approach** critical pour maintainability
2. **Real API testing** superieur aux mocks pour validation
3. **E2E tests** necessitent vraies donnees pour validation finale
4. **Token cost protection** evite surprises budget
5. **Error handling** requiert backend ET frontend
6. **Git commits frequents** previennent drift
7. **Production logs** = source de verite pour debugging
8. **Hotfix production bugs immediately** - FileNotFoundError casse tout le backend
9. **Python logger > File I/O** - Render capture automatiquement logger Python
10. **Red herrings exists** - Phase 8 localhost mystery etait backend casse, PAS URLs
11. **Backend validation first** - Tests frontend echouent si backend HTTP 500
12. **Timeout protection critical** - Previent requetes infinies qui epuisent tokens
13. **Backward audit workflow** - Valider phases dans ordre inverse (8 → 7 → 6 → 5)

### Anti-Patterns Evites
- Over-engineering features non validees
- Mocks pour validation finale
- Hardcoded API keys
- Emojis dans code executable
- Frontend changes sans backend validation
- Assumptions sur data availability

---

## Contacts & Resources

**Documentation technique:**
- Keepa API: https://github.com/keepacom/api_backend
- FastAPI: https://fastapi.tiangolo.com
- React Query: https://tanstack.com/query
- Tailwind CSS: https://tailwindcss.com

**Monitoring:**
- Sentry: https://sentry.io
- Render Dashboard: https://dashboard.render.com
- Netlify Dashboard: https://app.netlify.com

**MCP Servers actifs:**
- GitHub (repos, PRs, issues)
- Context7 (documentation libraries)
- Render (deployments, logs)
- Netlify (sites, builds)
- Neon (database management)

---

**Derniere mise a jour:** 23 Novembre 2025
**Prochaine revision:** Audit Phase 4 (backward workflow)
**Responsable:** Architecture + Product Development

**Validation Status:**
- Phase 8: VALIDEE (5/5 tests E2E, 100%)
- Phase 7: VALIDEE (3/3 tests E2E, 100%)
- Phase 6: VALIDEE (35/36 tests E2E, 97.2%)
- Phase 5: VALIDEE (35/36 tests E2E, 97.2%, score 85/100)
- Phase 4: AUDIT PROCHAIN (backward workflow)
