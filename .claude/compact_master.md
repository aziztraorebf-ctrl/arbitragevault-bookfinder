# ArbitrageVault BookFinder - Mémoire Globale Projet

**Dernière mise à jour** : 23 Novembre 2025
**Version** : 3.1
**Statut** : Phase 1 Foundation Audit COMPLÉTÉ (100% tests), Phases 2-7 features deployed

---

## 📋 Vue d'Ensemble

**Objectif** : Plateforme d'analyse arbitrage Amazon via API Keepa pour identifier opportunités achat/revente rentables.

**Public Cible** : Revendeurs Amazon FBA (Fulfilled by Amazon)

**Proposition de Valeur** :
- Analyse ROI automatisée (marge profit %)
- Scoring vélocité vente (vitesse rotation stock)
- Discovery produits rentables via Product Finder Keepa
- Dashboard décisionnel temps réel
- AutoSourcing automation avec safeguards

---

## 🏗️ Architecture Technique

### Stack Backend
- **Framework** : FastAPI 0.115.0 (Python 3.14)
- **Base de données** : PostgreSQL 17 (Neon serverless)
- **ORM** : SQLAlchemy 2.0 (async)
- **Migrations** : Alembic
- **API externe** : Keepa API (Product + Product Finder)
- **Logging** : structlog + Sentry
- **Déploiement** : Render (Docker, auto-deploy activé)

### Stack Frontend
- **Framework** : React 18 + TypeScript 5.6
- **Build** : Vite 6.0
- **Styling** : Tailwind CSS 4.0
- **Data Fetching** : React Query (TanStack Query)
- **Validation** : Zod 3.23
- **Routing** : React Router v7
- **Charts** : Recharts
- **Déploiement** : Netlify

### Infrastructure
- **Base de données** : Neon PostgreSQL (pooler connection)
- **Backend** : Render Web Service (auto-deploy ON)
- **Frontend** : Netlify Static Site
- **MCP Servers** : GitHub, Context7, Render, Netlify, Neon, Keepa

---

## 📊 Phases Projet - Vue Globale

### ✅ Phase 1 : Foundation Audit (COMPLÉTÉ)
**Durée** : 3 heures (audit + fixes) | **Objectif** : Valider infrastructure core 100%

**Livrables majeurs** :
- Suite tests foundation (21 tests integration)
- Database constraints enforcement (CHECK, UNIQUE, FK)
- Migration UUID + velocity_score constraints
- CRUD operations User/Batch/Analysis validés
- Health checks + session management
- TDD methodology (RED-GREEN-REFACTOR)

**Résultats** :
- Tests passing : 21/21 (100%)
- Code quality : 10/10 (infrastructure solid)
- Migration créée : CHECK constraints velocity_score
- Documentation : Test suite + diagnostic scripts

**Tests Coverage** :
- User Model CRUD : 6/6 tests
- Batch Model CRUD : 4/4 tests
- Analysis Model CRUD : 6/6 tests
- Database Manager : 3/3 tests
- Health Endpoints : 2/2 tests

**Corrections Phase 1.5** :
1. Missing CHECK constraints (velocity_score 0-100)
2. Rollback test design flaw (auto-commit issue)

**Performance** :
- All CRUD operations : < 50ms
- Database health check : < 10ms
- Transaction rollback : validated

### ✅ Phase 2 : Config Service + Product Finder (COMPLÉTÉ)
**Durée** : ~2 semaines | **Objectif** : Configuration business dynamique + discovery produits

**Livrables majeurs** :
- Config Service hiérarchique (global → domain → category)
- Preview mode avant sauvegarde config
- Product Finder Service (Keepa bestsellers + deals)
- Cache 2 niveaux (discovery 24h, scoring 6h)
- Audit trail changements config

**Métriques** :
- Cache hit rate : ~70%
- Réduction coûts Keepa : 70% via cache
- Config changes trackés : 100%

### ✅ Phase 3 : Product Discovery MVP (COMPLÉTÉ)
**Durée** : 3.5 semaines | **Objectif** : Interface discovery produits avec templates niches

**Livrables** :
- PostgreSQL cache tables (discovery, scoring, search history)
- React Query hooks + Zod validation
- Endpoints `/api/v1/products/discover` et `discover-with-scoring`
- E2E testing avec vraies données Keepa
- Throttling Keepa (20 req/min, burst 200)
- Templates niches curées (tech-books-python, french-learning, etc.)

**Métriques** :
- Niches templates : 5 curées
- Cache TTL : 24h discovery, 6h scoring
- Protection throttling : ✅ Multi-niveaux

### ✅ Phase 4 : Backlog Cleanup (COMPLÉTÉ)
**Durée** : 1 journée | **Objectif** : Fixes critiques + protection budget Keepa

**Fixes critiques** :
- ✅ Fix BSR extraction (bug ~67% erreur)
- ✅ Budget protection (`_ensure_sufficient_balance()`)
- ✅ Windows ProactorEventLoop compatibility
- ✅ Frontend balance Keepa display

**Commit final** : `093692e` (1 Nov 2025)

### ✅ Phase 5 : Niche Bookmarks & Re-Run (COMPLÉTÉ)
**Durée** : ~6 heures | **Objectif** : Sauvegarder niches et relancer analyses

**Livrables** :
- Backend bookmarks endpoints (CRUD niches sauvegardées)
- Database migration (table `saved_niches`)
- Frontend React Query hooks pour bookmarks
- Bouton "Save Niche" + toast notifications
- Page "Mes Niches" avec gestion complète
- Re-run analysis avec `force_refresh` parameter
- Strategic views avec target pricing

**Commits** : 6 commits (`7b92832`..`00ff975`)
**Deployments** : 2 Render deployments LIVE

### ✅ Phase 7 : AutoSourcing Safeguards (COMPLÉTÉ)
**Durée** : 3 heures (code review + corrections) | **Objectif** : Protection token exhaustion

**Livrables majeurs** :
- Cost estimation avant exécution (`/estimate`)
- Token balance validation (`MIN_TOKEN_BALANCE_REQUIRED`)
- Timeout protection (120s avec DB propagation)
- ASIN deduplication
- Frontend error handling (HTTP 400/408/429)
- Settings-based configuration (no hardcoded values)
- Zod schemas pour validation errors

**Commits Phase 7** :
- `f0de72f`..`f91caf0` : 8 commits implémentation
- `49c3ce7` : Corrections (emojis removed + timeout DB propagation)
- `4f7f97b` : IMPORTANT-02 (settings migration) + IMPORTANT-03 (Zod schemas)
- `3c08593` : Hotfix (missing settings parameter in `/run-custom`)

**Code Quality** : 8.7/10 → 9.5/10 après corrections

**Production Ready** : ✅ 100%
- All endpoints validés production
- Auto-deploy enabled sur Render
- E2E tests : 5/5 PASSED

**Documentation** :
- `PHASE7_COMPREHENSIVE_AUDIT_REPORT.md`
- `PHASE7_CORRECTION_PLAN.md`
- `PHASE7_FINAL_REPORT.md`

---

## 🔑 Modules Clés

### 1. Keepa Service (`keepa_service.py`)
**Responsabilité** : Interface API Keepa avec cache + throttling

**Features** :
- Cache intelligent 10 min (tests) / 24h (production)
- Throttling rate (20 req/min) + budget (check balance)
- Retry logic avec exponential backoff
- Token tracking temps réel

**Méthodes clés** :
```python
async def get_product(asin: str) -> KeepaProduct
async def discover_products(criteria: dict) -> List[str]
async def check_api_balance() -> int
```

### 2. Keepa Parser V2 (`keepa_parser_v2.py`)
**Responsabilité** : Parse réponses Keepa API → structured data

**Features** :
- Extraction prix (Amazon, FBA, FBM)
- BSR current + historique
- Offres (nombre vendeurs, compétition)
- Gestion formats multiples Keepa

**Bug critique fixé (Phase 4)** :
```python
# AVANT : bsr = rank_data[1]  # Premier BSR (obsolète)
# APRÈS : bsr = rank_data[-1]  # Dernier BSR (current)
```

### 3. Analysis Service (`analysis_service.py`)
**Responsabilité** : Calcul ROI + vélocité + scoring

**Formules** :
```python
ROI% = ((sale_price - buy_price - fees) / buy_price) * 100
velocity_score = f(BSR, category) → 0-100
confidence = f(price_stability, data_quality) → 0-100
```

**Recommendations** :
- STRONG_BUY : ROI ≥50% + velocity ≥80
- BUY : ROI ≥30% + velocity ≥60
- CONSIDER : ROI ≥15%
- SKIP : ROI <15%

### 4. Config Service (`config_service.py`)
**Responsabilité** : Configuration business hiérarchique

**Scopes** : global → domain:{id} → category:{name}

**Features** :
- Preview mode (test avant apply)
- Audit trail (change history)
- Optimistic locking (version checking)

### 5. AutoSourcing Service (`autosourcing_service.py`)
**Responsabilité** : Jobs discovery automatisés avec safeguards (Phase 7)

**Safeguards** :
- Cost estimation avant exécution
- Balance validation (MIN_TOKEN_BALANCE_REQUIRED = 40)
- Timeout protection (TIMEOUT_PER_JOB = 120s)
- ASIN deduplication
- DB propagation sur timeout/erreur

**Endpoints** :
- `/api/v1/autosourcing/estimate` : Estimer coût job
- `/api/v1/autosourcing/run-custom` : Exécuter job avec validation
- `/api/v1/autosourcing/jobs` : Liste jobs récents
- `/api/v1/autosourcing/picks/{pick_id}/action` : Update action (to_buy, favorite, ignored)

---

## 🔐 Sécurité & Configuration

### Variables Environnement
```env
DATABASE_URL=postgresql://...@neon.tech/neondb
KEEPA_API_KEY=<secret>
SENTRY_DSN=<secret>
ENVIRONMENT=production
```

### Protection Clés API
- ❌ JAMAIS commit clés dans Git
- ✅ Variables env `.claude/settings.local.json`
- ✅ Référence via `os.environ["KEEPA_API_KEY"]`
- ✅ `.env` files dans `.gitignore`

### Rate Limiting Keepa
- **Rythme** : 20 requêtes/minute (token bucket)
- **Budget** : Check balance avant requête
- **Burst** : 200 tokens capacity
- **Seuils** : warning @80, critical @40

### Settings-Based Configuration (Phase 7)
- `keepa_product_finder_cost: int = 10` (tokens per page)
- `keepa_product_details_cost: int = 1` (tokens per ASIN)
- `keepa_results_per_page: int = 10`

---

## 📊 Métriques Production

### Performance Backend
- **Response time** : p50 = 180ms, p95 = 450ms
- **Keepa API** : p50 = 220ms, p95 = 680ms
- **Cache hit rate** : ~70% (target)
- **Database queries** : <50ms (p95)

### Fiabilité
- **Uptime** : 99.9% target
- **Error rate** : <0.1%
- **Token protection** : 100% (Phase 4.5 + Phase 7)
- **Rollback DB** : 100% sur exceptions
- **Auto-deploy** : ✅ Activé sur Render

### Coûts Keepa
- **Analyse 1 ASIN** : 1 token
- **Product Finder** : 10 tokens/page
- **Bestsellers** : 50 tokens
- **Discovery batch 100** : 100 tokens
- **Monthly budget** : ~10,000 tokens

---

## 🚫 Erreurs Évitées (Leçons Apprises)

### 1. BSR Extraction Obsolète
**Erreur** : Lire premier BSR au lieu du dernier
**Impact** : 67% erreur sur vélocité
**Fix** : `rank_data[-1]` (Phase 4)

### 2. Throttle Incomplet
**Erreur** : Rate limit OK, budget non protégé
**Impact** : Balance négative (-31 tokens)
**Fix** : `_ensure_sufficient_balance()` (Phase 4.5)

### 3. Timeout Sans DB Propagation (Phase 7)
**Erreur** : Timeout intercepté dans router AVANT job.status update
**Impact** : Jobs stuck RUNNING après timeout
**Fix** : Timeout wrapper dans service method avec DB commit

### 4. Emojis in Python Code (Phase 7)
**Erreur** : Emojis (✅❌) dans logger.info/error
**Impact** : Encoding failures, linting errors
**Fix** : ASCII-only logs (PASS/REJECT)

### 5. Incomplete Refactoring (Phase 7 Hotfix)
**Erreur** : Constructor signature change non propagé partout
**Impact** : HTTP 500 sur `/run-custom` endpoint
**Fix** : Add missing `settings` parameter

---

## 🎯 Prochaines Phases

### Phase 6-1 : Audit & Testing
**Objectif** : Répéter cycle audit-test-review-fix pour Phases 6-1

**Actions** :
1. Systematic audit (comme Phase 7)
2. Production testing
3. Code review via subagent
4. Apply corrections if needed

**Méthode** : SuperPower protocols (verification-before-completion, requesting-code-review, systematic-debugging)

---

## 📖 Documentation Référence

### Documentation Interne
- Architecture : [ARCHITECTURE.md](backend/doc/ARCHITECTURE.md)
- Known Issues : [KNOWN_ISSUES.md](backend/doc/KNOWN_ISSUES.md)
- Phase 7 Reports : [PHASE7_FINAL_REPORT.md](docs/PHASE7_FINAL_REPORT.md)

### Documentation Externe
- **Keepa API** : https://github.com/keepacom/api_backend
- **FastAPI** : https://fastapi.tiangolo.com
- **React Query** : https://tanstack.com/query/latest
- **Neon PostgreSQL** : https://neon.tech/docs
- **SQLAlchemy 2.0** : https://docs.sqlalchemy.org/en/20/

### MCP Servers
- **GitHub** : Repos, PRs, issues
- **Context7** : Documentation patterns officiels
- **Render** : Logs, déploiements backend
- **Netlify** : Déploiements frontend
- **Neon** : Database operations
- **Keepa** : Product data (via MCP wrapper)

---

## 📞 Contacts & Liens

**Repository** : https://github.com/aziztraorebf-ctrl/arbitragevault-bookfinder
**Backend Production** : https://arbitragevault-backend-v2.onrender.com
**Database** : Neon PostgreSQL `ep-damp-thunder-ado6n9o2`

**Développeur Principal** : Aziz Trabelsi
**Assistant IA** : Claude Code (Anthropic)
**Stack MCP** : GitHub + Context7 + Render + Netlify + Neon + Keepa

---

**Version** : 3.0
**Dernière révision** : 22 Novembre 2025
**Statut** : Phases 1-7 complétées, auto-deploy activé, prêt pour audit Phases 6-1
