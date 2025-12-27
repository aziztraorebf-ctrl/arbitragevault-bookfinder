# ArbitrageVault BookFinder - Memoire Globale Projet

**Derniere mise a jour** : 27 Decembre 2025
**Version** : 6.0
**Statut** : Phases 1-8 auditees, Phase 9 complete, Phases 10-11 planifiees

---

## Vue d'Ensemble

**Objectif** : Plateforme d'analyse arbitrage Amazon via API Keepa pour identifier opportunites achat/revente rentables.

**Public Cible** : Revendeurs Amazon FBA (Fulfilled by Amazon)

**Proposition de Valeur** :
- Analyse ROI automatisee (marge profit %)
- Scoring velocite vente (vitesse rotation stock)
- Discovery produits rentables via Product Finder Keepa
- Dashboard decisionnel temps reel
- AutoSourcing automation avec safeguards

**Vision Long Terme** :
- Application majoritairement automatisee via N8N
- Machine Learning pour optimiser les decisions d'achat (futur)
- Integration multi-outils workflow automation

---

## Architecture Technique

### Stack Backend
- **Framework** : FastAPI 0.115.0 (Python 3.11+)
- **Base de donnees** : PostgreSQL 17 (Neon serverless)
- **ORM** : SQLAlchemy 2.0 (async)
- **Migrations** : Alembic
- **API externe** : Keepa API (Product + Product Finder)
- **Logging** : structlog + Sentry
- **Deploiement** : Render (Docker, auto-deploy active)

### Stack Frontend
- **Framework** : React 18 + TypeScript 5.6
- **Build** : Vite 6.0
- **Styling** : Tailwind CSS 4.0
- **Data Fetching** : React Query (TanStack Query)
- **Validation** : Zod 3.23
- **Routing** : React Router v7
- **Charts** : Recharts
- **Deploiement** : Netlify

### Infrastructure
- **Base de donnees** : Neon PostgreSQL (pooler connection)
- **Backend** : Render Web Service (auto-deploy ON)
- **Frontend** : Netlify Static Site
- **MCP Servers** : GitHub, Context7, Render, Netlify, Neon, Keepa

---

## Phases Projet - Vue Globale

### Phase 1 : Foundation Audit (COMPLETE)
**Duree** : 3 heures | **Tests** : 21/21 (100%)

**Livrables** :
- Suite tests foundation (21 tests integration)
- Database constraints enforcement (CHECK, UNIQUE, FK)
- Migration UUID + velocity_score constraints
- CRUD operations User/Batch/Analysis valides
- Health checks + session management

**Tests Coverage** :
- User Model CRUD : 6/6
- Batch Model CRUD : 4/4
- Analysis Model CRUD : 6/6
- Database Manager : 3/3
- Health Endpoints : 2/2

### Phase 2 : Keepa Integration Audit (COMPLETE)
**Duree** : 4 heures | **Tests** : 16/16 (100%)

**Livrables** :
- KeepaService Core : 5/5 tests
- Keepa Parser v2 : 3/3 tests
- ConfigService : 2/2 tests
- Product Finder : 2/2 tests
- Fee Calculation : 2/2 tests
- Full Pipeline : 1/1 test

**Fixes appliquees** : 19 corrections (signatures, return types, error handling)

### Phase 3 : Product Discovery MVP (COMPLETE)
**Duree** : 3.5 semaines | **Tests** : 32/32 (100%)

**Livrables** :
- PostgreSQL cache tables (discovery, scoring, search history)
- React Query hooks + Zod validation
- Endpoints `/api/v1/products/discover`
- Throttling Keepa (20 req/min, burst 200)
- Templates niches curees (5 templates)

**Audit** : 8 Decembre 2025 - 4 bugs fixes, 514 tests pass

### Phase 4 : Backlog Cleanup (DEPLOYE - AUDIT A FAIRE)
**Duree** : 1 journee | **Status** : En production, non audite

**Fixes critiques** :
- Fix BSR extraction (bug ~67% erreur)
- Budget protection (`_ensure_sufficient_balance()`)
- Windows ProactorEventLoop compatibility
- Frontend balance Keepa display

### Phase 5 : Niche Bookmarks (COMPLETE)
**Duree** : ~6 heures | **Tests** : 42/42 (36 backend + 6 E2E)

**Livrables** :
- Backend bookmarks endpoints (CRUD niches sauvegardees)
- Database migration (table `saved_niches`)
- Frontend React Query hooks pour bookmarks
- Re-run analysis avec `force_refresh` parameter
- Strategic views avec target pricing

**Audit** : 14 Decembre 2025 - 7 issues fixes (2 critical, 3 important, 2 minor)

**Tests Coverage** :
- Unit Tests BookmarkService : 12/12
- API Integration Tests : 14/14
- Hostile Review Tests : 10/10
- Playwright E2E Tests : 6/6

**Issues Fixes** :
- Critical: Empty string validation, None safety in get_bookmark
- Important: IntegrityError handling, duplicate slug validation
- Minor: Error messages clarity, type hints

### Phase 6 : Niche Discovery Optimization (COMPLETE - AUDITE)
**Duree** : ~4 heures | **Tests** : 62/62 (100%) | **Date audit** : 15 Dec 2025

**Livrables deployes** :
1. **Budget Guard** : Estimation cout tokens AVANT execution niche discovery
2. **ConditionBreakdown UI** : Affichage prix par condition
3. **Timeout Protection** : 30s sur endpoints Keepa avec HTTP 408
4. **E2E Tests Playwright** : Suite complete frontend (4/4 PASS)
5. **Smart Strategies** : FBA seller competition filter, Smart Velocity, Textbooks
6. **Product Finder Post-Filtering** : Pre-filter API + post-filter backend

**Tests crees** :
- `backend/tests/unit/test_niche_templates_hostile.py` (20 tests)
- `backend/tests/api/test_niches_api_edge_cases.py` (10 tests)
- `backend/tests/unit/test_budget_guard_stress.py` (14 tests)
- `backend/tests/e2e/tests/03-niche-discovery.spec.js` (4 tests)

### Phase 7 : AutoSourcing Safeguards (COMPLETE - AUDITE)
**Duree** : 3 heures | **Tests** : 109/109 (100%) | **Date audit** : 16 Dec 2025

**Livrables** :
- Cost estimation avant execution (`/estimate`)
- Token balance validation
- Timeout protection (120s avec DB propagation)
- ASIN deduplication
- Frontend error handling (HTTP 400/408/429)

**Tests crees** :
- `backend/tests/unit/test_autosourcing_deduplication_hostile.py` (7 tests)
- `backend/tests/unit/test_autosourcing_batch_failures.py` (6 tests)
- `backend/tests/unit/test_autosourcing_timeout_race.py` (6 tests)
- `backend/tests/integration/test_autosourcing_recent_duplicates.py` (6 tests)
- `backend/tests/integration/test_autosourcing_error_responses.py` (8 tests)
- `backend/tests/integration/test_autosourcing_job_states.py` (10 tests)
- `backend/tests/unit/test_autosourcing_hostile_review.py` (13 tests)

### Phase 8 : Advanced Analytics (COMPLETE - AUDITE)
**Duree** : ~2 heures | **Tests** : 50+ | **Date audit** : 25 Dec 2025

**Refactoring majeur** : `dead_inventory` -> `slow_velocity`

**Probleme identifie** :
Les seuils BSR hardcodes (50K/30K/100K) etaient incorrects. Donnees reelles Keepa montrent:
- BSR 200K = 15+ ventes/mois (PAS dead inventory)
- BSR 350K = 7+ ventes/mois (se vend regulierement)

**Solution implementee** :
- Supprime `detect_dead_inventory()` et seuils arbitraires
- Nouvelle fonction `_calculate_slow_velocity_risk()` utilisant Keepa salesDrops
- Source donnees: `KEEPA_REAL` (salesRankDrops30) avec fallback BSR

**Fichiers modifies** :
- `backend/app/api/v1/endpoints/analytics.py` - nouvelle fonction slow_velocity
- `backend/app/schemas/analytics.py` - ajout sales_drops_30/90, SlowVelocitySchema
- `backend/app/services/risk_scoring_service.py` - renomme dead_inventory -> slow_velocity
- `backend/app/services/advanced_analytics_service.py` - supprime detect_dead_inventory

**Tests crees** :
- `backend/tests/unit/test_slow_velocity_risk.py` (16 tests)

**Livrables existants** :
- Endpoints analytics (`/api/v1/analytics/*`)
- ASIN history tracking (`/api/v1/asin-history/*`)
- TokenErrorAlert component
- useProductDecision hook

**CLAUDE.md** : v3.2 -> v3.3 (ajout Senior Review Gate)
**Slash command** : `/senior-review` cree

### Phase 9 : UI Completion (COMPLETE)
**Date completion** : 27 Decembre 2025
**Duree reelle** : ~4 heures | **Tests** : 70+ frontend

**Livrables** :
- 4 pages frontend completees (Configuration, AnalyseStrategique, StockEstimates, AutoScheduler)
- Hooks React Query (useConfig, useStrategicViews, useStockEstimate)
- Unit tests pour pages et hooks
- E2E tests Playwright (26 PASS / 5 FAIL - issues API production)

**Senior Review** : Gaps 5, 6, 8, 9 identifies et corriges
- Gap 5: Tests unitaires pages manquants -> Ajoutes
- Gap 6: Tests hooks manquants -> Ajoutes
- Gap 8: Loading state submit button -> Ajoute
- Gap 9: Documentation hooks -> Ajoutee

**Decision Architecture (External Validation)** :
- Pages AnalyseStrategique et StockEstimates jugees **redundantes**
- Ces pages "cassent le flux naturel de decision"
- Signaux strategiques doivent etre integres dans les resultats de recherche
- **Action** : Unification planifiee en Phase 10

---

### Phase 10 : Unified Product Table (PLANIFIE)
**Date creation plan** : 27 Decembre 2025
**Duree estimee** : ~6.5 heures | **Plan** : `docs/plans/2025-12-27-unified-product-table.md`

**Objectif** : Unifier les composants `ViewResultsTable` et `ProductsTable` en un seul `UnifiedProductTable` reutilisable par tous les modules.

**Decisions Architecture** :
1. **Accordions Niche Discovery** : Desactives (donnees insuffisantes)
2. **Colonnes Niche Discovery** : Simples (7 colonnes vs 12 pour Analyse Manuelle)
3. **Verification data conflicts** : Afficher les deux + delta visuel
4. **Export CSV** : Format unifie avec colonnes fixes
5. **Pages supprimees** : Redirect automatique + banner explicatif

**Tasks** :
| Phase | Description | Duree |
|-------|-------------|-------|
| 1 | Type DisplayableProduct + UnifiedProductRow + UnifiedProductTable | 2h |
| 2 | Extraction VerificationPanel composant reutilisable | 1h |
| 3 | Integration dans NicheDiscovery, AnalyseManuelle, AutoSourcing | 2h |
| 4 | Nettoyage: suppression pages AnalyseStrategique/StockEstimates | 1h |
| 5 | Verification finale | 30min |

**Composants a creer** :
- `frontend/src/types/unified.ts` - Type DisplayableProduct
- `frontend/src/components/unified/UnifiedProductRow.tsx`
- `frontend/src/components/unified/UnifiedProductTable.tsx`
- `frontend/src/components/unified/VerificationPanel.tsx`
- `frontend/src/components/unified/useVerification.ts`

---

### Phase 11 : Page Centrale Recherches (PLANIFIE)
**Date creation plan** : 27 Decembre 2025
**Duree estimee** : ~4-5 heures

**Objectif** : Creer une page centrale `/recherches` ("Mes Recherches") qui centralise tous les resultats de recherches.

**Contexte** : Preparation pour automatisation N8N. Quand des recherches sont lancees automatiquement, l'utilisateur doit pouvoir voir tous les resultats en un seul endroit.

**Decisions Architecture** :
1. **Route** : `/recherches` avec titre "Mes Recherches"
2. **Persistance** : Backend PostgreSQL (table `search_results`)
3. **Retention** : 30 jours avec auto-cleanup
4. **AutoSourcing** : Devient declencheur, redirect vers `/recherches` apres completion

**Backend a creer** :
- Table `search_results` (id, created_at, source, filters_applied JSON, products JSON, expires_at)
- API: POST /searches, GET /searches, DELETE /searches/{id}

**Frontend** :
- Page `/recherches` avec liste des recherches
- Filtres par date/source
- Accordion expand vers UnifiedProductTable

**AutoSourcing Evolution** :
- Garde son UI pour configurer/lancer jobs
- Apres completion: redirect vers `/recherches`
- Resultats visibles dans page centrale

---

## Session 7 Decembre 2025 - Cleanup & Systeme

### Deep Cleanup

**Phase 1** : 68 fichiers documentation obsoletes supprimes
- Plans completes, notes de session, fichiers memex

**Phase 2** : 42 fichiers additionnels supprimes
- Total : 110+ fichiers obsoletes retires

**Documentation mise a jour** :
- README.md (root) : Phases 1-7, frontend deploye
- backend/CHANGELOG.md : Phases 5-7 ajoutees
- backend/API_DOCUMENTATION.md : 40+ endpoints documentes
- frontend/README.md : Remplace template Vite
- .claude/*.md : Structure, System Summary, README

### CLAUDE.md Evolution

**v2.0** (avant session) :
- Zero-Tolerance Engineering base
- Context7-First, BUILD-TEST-VALIDATE
- Gate System, Validation Croisee MCP

**v3.0** (cree cette session) :
- Hostile Code Review (Pre-Commit)
- Automated Quality Gates
- Observabilite (Logs Production First)
- Rollback Strategy
- Code Review Workflow

**v3.1** (finale cette session) :
- UX-First workflow
- Modes Test Keepa (REAL/REPLAY/MOCK)
- Niveaux de Tests (Smoke/Integration/Full E2E)
- Nuance approximatif (exact pour donnees, tolerance pour scoring)
- Migration DB conventions
- Section Ressources Existantes

---

## Systeme de Hooks v2 (Infrastructure Critique)

### Vue d'ensemble

Le systeme de hooks enforce automatiquement les regles CLAUDE.md via 3 points de controle bloquants.

### Hooks Actifs

| Hook | Fichier | Trigger | Action |
|------|---------|---------|--------|
| **Edit/Write Gate** | `edit_write_gate.py` | Modification `.py`/`.ts`/`.tsx`/`.js` | Bloque si pas de plan OU Context7 |
| **Git Commit Gate** | `pre_tool_validator.py` | `git commit`/`push` | Bloque avec rappel checkpoints |
| **Stop Hook** | `stop_checkpoint.py` | Fin de reponse | Rappel informatif |

### Fichiers Systeme

```
.claude/
  hooks/
    edit_write_gate.py      # Gate Edit/Write (bloquant)
    pre_tool_validator.py   # Gate Git commit (bloquant)
    stop_checkpoint.py      # Rappel fin de tour
    hook-debug.log          # Logs debug PreToolUse
    edit-gate-debug.log     # Logs debug Edit/Write
    stop-debug.log          # Logs debug Stop
  current_session.json      # Etat session (plan + context7)
  settings.local.json       # Configuration hooks
```

### Workflow Enforce

1. **Avant modification code** :
   - Verifier `current_session.json` existe
   - `plan_exists: true` requis
   - `context7_called: true` requis

2. **Avant commit** :
   - Checkpoint validation requis
   - 6 questions avec preuves

3. **Structure current_session.json** :
```json
{
  "plan_exists": true,
  "context7_called": true,
  "tasks_started": ["task_name"]
}
```

### Plans avec Checkpoints Explicites

Chaque plan doit inclure pour chaque tache :
- **Pre-Implementation** : Context7-First, TDD (tests avant code)
- **Post-Implementation** : Tests passent, Hostile Review, verification-before-completion

Exemple : `docs/plans/2025-12-13-phase4-backlog-cleanup-v3.md`

---

## Modules Cles

### 1. Keepa Service (`keepa_service.py`)
**Responsabilite** : Interface API Keepa avec cache + throttling

**Features** :
- Cache intelligent 10 min (tests) / 24h (production)
- Throttling rate (20 req/min) + budget (check balance)
- Retry logic avec exponential backoff
- Token tracking temps reel

### 2. Keepa Parser V2 (`keepa_parser_v2.py`)
**Responsabilite** : Parse reponses Keepa API -> structured data

**Bug critique fixe (Phase 4 + Dec 2025)** :
```python
# AVANT : bsr = rank_data[1]  # Premier BSR (obsolete)
# APRES : bsr = rank_data[-1]  # Dernier BSR (current)
# FIX Dec 2025 : Unpack tuple (timestamp, value)
```

### 3. Analysis Service (`analysis_service.py`)
**Responsabilite** : Calcul ROI + velocite + scoring

**Formules** :
```python
ROI% = ((sale_price - buy_price - fees) / buy_price) * 100
velocity_score = f(BSR, category) -> 0-100
confidence = f(price_stability, data_quality) -> 0-100
```

### 4. AutoSourcing Service (`autosourcing_service.py`)
**Responsabilite** : Jobs discovery automatises avec safeguards

**Safeguards** :
- Cost estimation avant execution
- Balance validation (MIN_TOKEN_BALANCE_REQUIRED = 40)
- Timeout protection (TIMEOUT_PER_JOB = 120s)
- ASIN deduplication
- DB propagation sur timeout/erreur

---

## Securite & Configuration

### Variables Environnement
```env
DATABASE_URL=postgresql://...@neon.tech/neondb
KEEPA_API_KEY=<secret>
SENTRY_DSN=<secret>
ENVIRONMENT=production
```

### Protection Cles API
- JAMAIS commit cles dans Git
- Variables env `.claude/settings.local.json`
- Reference via `os.environ["KEEPA_API_KEY"]`
- `.env` files dans `.gitignore`

### Rate Limiting Keepa
- **Rythme** : 20 requetes/minute (token bucket)
- **Budget** : Check balance avant requete
- **Burst** : 200 tokens capacity
- **Seuils** : warning @80, critical @40

---

## Erreurs Evitees (Lecons Apprises)

### 1. BSR Extraction Obsolete
**Erreur** : Lire premier BSR au lieu du dernier
**Impact** : 67% erreur sur velocite
**Fix** : `rank_data[-1]` (Phase 4)

### 2. BSR Tuple Unpacking (Dec 2025)
**Erreur** : BSR retourne comme tuple (timestamp, value)
**Impact** : TypeError en production
**Fix** : Unpack explicite `_, bsr_value = bsr_tuple`

### 3. Throttle Incomplet
**Erreur** : Rate limit OK, budget non protege
**Impact** : Balance negative (-31 tokens)
**Fix** : `_ensure_sufficient_balance()` (Phase 4.5)

### 4. Timeout Sans DB Propagation
**Erreur** : Timeout intercepte dans router AVANT job.status update
**Impact** : Jobs stuck RUNNING apres timeout
**Fix** : Timeout wrapper dans service method avec DB commit

### 5. Emojis in Python Code
**Erreur** : Emojis dans logger.info/error
**Impact** : Encoding failures, linting errors
**Fix** : ASCII-only logs (PASS/REJECT)

---

## Metriques Production

### Performance Backend
- **Response time** : p50 = 180ms, p95 = 450ms
- **Keepa API** : p50 = 220ms, p95 = 680ms
- **Cache hit rate** : ~70% (target)
- **Database queries** : <50ms (p95)

### Fiabilite
- **Uptime** : 99.9% target
- **Error rate** : <0.1%
- **Token protection** : 100%
- **Auto-deploy** : Active sur Render

### Couts Keepa
- **Analyse 1 ASIN** : 1 token
- **Product Finder** : 10 tokens/page
- **Bestsellers** : 50 tokens
- **Discovery batch 100** : 100 tokens
- **Monthly budget** : ~10,000 tokens

---

## Prochaines Etapes

### Ordre recommande

| Priorite | Phase | Description | Status | Effort |
|----------|-------|-------------|--------|--------|
| 1 | Phase 10 | Unified Product Table | PLAN PRET | ~6.5h |
| 2 | Phase 11 | Page Centrale Recherches | PLANIFIE | ~4-5h |
| 3 | Phase 12 | Integration N8N | FUTUR | TBD |

### Audit Systematique - Etat

| Phase | Description | Status | Date |
|-------|-------------|--------|------|
| Phase 1 | Foundation | COMPLETE | 23 Nov 2025 |
| Phase 2 | Keepa Integration | COMPLETE | 23 Nov 2025 |
| Phase 3 | Product Discovery MVP | COMPLETE | 8 Dec 2025 |
| Phase 4 | Backlog Cleanup | COMPLETE | 14 Dec 2025 |
| Phase 5 | Niche Bookmarks | COMPLETE | 14 Dec 2025 |
| Phase 6 | Niche Discovery Optimization | COMPLETE | 15 Dec 2025 |
| Phase 7 | AutoSourcing Safeguards | COMPLETE | 16 Dec 2025 |
| Phase 8 | Advanced Analytics | COMPLETE | 25 Dec 2025 |
| Phase 9 | UI Completion | COMPLETE | 27 Dec 2025 |
| Phase 10 | Unified Product Table | PLAN PRET | 27 Dec 2025 |
| Phase 11 | Page Centrale Recherches | PLANIFIE | 27 Dec 2025 |

### Infrastructure Tests

1. Implementer mode REPLAY Keepa (fixtures JSON)
2. Creer suite Smoke Tests (5 tests critiques)
3. Segmenter tests par niveau

---

## Vision Future - Automatisation & ML

### Phase 12 : Integration N8N (FUTUR - Non planifie)

**Objectif** : Automatiser les recherches via N8N pour sourcing continu.

**Pre-requis** :
- Phase 10 complete (composants unifies)
- Phase 11 complete (page centrale avec persistance)
- Tester manuellement l'app pendant 1-2 mois

**A implementer** :
- API webhooks pour N8N
- Authentification API keys
- Endpoints batch pour resultats automatises
- Documentation integration N8N

**Workflow cible** :
1. N8N lance recherches automatiques (nuit, matin)
2. Resultats sauvegardes en base
3. Utilisateur consulte `/recherches` pour voir opportunites
4. Decision d'achat manuelle ou semi-automatisee

### Machine Learning - Preparation (PLACEHOLDER)

**Objectif futur** : Utiliser ML pour predire quels produits se vendront bien.

**Decision actuelle** : NE PAS implementer maintenant (YAGNI)

**Quand implementer** :
- Apres 2-3 mois de donnees d'achat/vente reelles
- Quand pattern de decisions utilisateur est clair
- Quand ROI de l'automatisation est prouve

**Table future (non creee)** :
```sql
-- purchase_decisions (a creer quand necessaire)
-- Stocke les decisions d'achat et leurs resultats
-- Source de verite pour ML training
CREATE TABLE purchase_decisions (
  id UUID PRIMARY KEY,
  asin VARCHAR(20) NOT NULL,
  decision VARCHAR(20), -- bought, skipped, watchlist
  decided_at TIMESTAMP,
  buy_price DECIMAL,
  sell_price DECIMAL,
  actual_roi DECIMAL,
  days_to_sell INTEGER,
  outcome VARCHAR(20) -- success, break_even, loss
);
```

**Documentation** : `docs/future/ML_PREPARATION.md` (a creer si besoin)

---

## Documentation Reference

### Documentation Interne
- **CLAUDE.md** : Instructions Claude Code v3.3 (Senior Review Gate)
- **compact_current.md** : Memoire session active
- **compact_master.md** : Memoire globale (ce fichier)

### Documentation Externe
- **Keepa API** : https://github.com/keepacom/api_backend
- **FastAPI** : https://fastapi.tiangolo.com
- **React Query** : https://tanstack.com/query/latest

### MCP Servers
- **GitHub** : Repos, PRs, issues
- **Context7** : Documentation patterns officiels
- **Render** : Logs, deploiements backend
- **Netlify** : Deploiements frontend
- **Neon** : Database operations
- **Keepa** : Product data (via MCP wrapper)

---

## Contacts & Liens

**Repository** : https://github.com/aziztraorebf-ctrl/arbitragevault-bookfinder
**Backend Production** : https://arbitragevault-backend-v2.onrender.com
**Frontend Production** : https://arbitragevault.netlify.app
**Database** : Neon PostgreSQL

**Developpeur Principal** : Aziz
**Assistant IA** : Claude Code (Anthropic)

---

**Version** : 6.0
**Derniere revision** : 27 Decembre 2025
**Statut** : Phases 1-9 completes, Phases 10-11 planifiees, Phase 12 (N8N) future
