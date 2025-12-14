# ArbitrageVault BookFinder - Memoire Globale Projet

**Derniere mise a jour** : 14 Decembre 2025
**Version** : 5.1
**Statut** : Phases 1-7 deployees, Phase 5 auditee, Hooks v2 actifs

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

### Phase 6 : Niche Discovery Optimization & E2E Testing (DEPLOYE - AUDIT INCOMPLET)
**Duree** : ~4 heures | **Status** : Deploye, audit a completer

**Contexte** : Phase 6 a eu plusieurs definitions au fil du temps. Cette section consolide le scope final.

**Livrables deployes** :
1. **Budget Guard** : Estimation cout tokens AVANT execution niche discovery
   - Fichier: `backend/app/api/v1/endpoints/niches.py`
   - Commits: `66ed3d8`, `b2b0702`
2. **ConditionBreakdown UI** : Affichage prix par condition (new, very_good, good, acceptable)
   - Fichier: `frontend/src/components/accordions/ConditionBreakdown.tsx`
   - Commit: `c32169d`
3. **Timeout Protection** : 30s sur endpoints Keepa avec HTTP 408
   - Fichier: `backend/app/api/v1/endpoints/niches.py`
   - Commit: `74a3af8`
4. **E2E Tests Playwright** : Suite complete frontend
   - Fichiers: `backend/tests/e2e/tests/*.spec.js`
   - Resultat: 23/28 -> 27/28 (96%)
5. **Smart Strategies** : FBA seller competition filter, Smart Velocity, Textbooks
   - Fichier: `backend/app/services/niche_templates.py`
   - Commit: `b2b0702`

**Documentation existante** :
- `docs/plans/2025-11-30-phase-6-niche-discovery-audit.md` - Plan Budget Guard
- `docs/plans/PHASE6_CORRECTION_PLAN.md` - Plan corrections E2E
- `.claude/archives/PHASE_5_6_COMPLETE.md` - Rapport ConditionBreakdown

**Ce qui reste a auditer** :
1. [ ] Tests unitaires pour `estimate_discovery_cost()`
2. [ ] Validation Budget Guard avec vraies donnees
3. [ ] Hostile review de `niche_templates.py` (Smart Strategies)
4. [ ] Tests API pour endpoint `/niches/discover` avec edge cases
5. [ ] Verification E2E 100% (actuellement 96%)

**Bugs connus (a verifier)** :
- Token consumption silencieux (~750 tokens sans resultats si timeout)
- TokenErrorAlert component non implemente (generic errors acceptables pour MVP)

### Phase 7 : AutoSourcing Safeguards (DEPLOYE - PARTIELLEMENT AUDITE)
**Duree** : 3 heures | **Status** : E2E tests 5/5, code quality 9.5/10

**Livrables** :
- Cost estimation avant execution (`/estimate`)
- Token balance validation
- Timeout protection (120s avec DB propagation)
- ASIN deduplication
- Frontend error handling (HTTP 400/408/429)

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

### Audit Systematique (Option A)

| Phase | Description | Status | Date |
|-------|-------------|--------|------|
| Phase 3 | Product Discovery MVP | COMPLETE | 8 Dec 2025 |
| Phase 5 | Niche Bookmarks | COMPLETE | 14 Dec 2025 |
| Phase 4 | Backlog Cleanup | A FAIRE | - |
| Phase 6 | Niche Discovery Optimization | A COMPLETER | Deploye, audit incomplet |

### Infrastructure Tests

1. Implementer mode REPLAY Keepa (fixtures JSON)
2. Creer suite Smoke Tests (5 tests critiques)
3. Segmenter tests par niveau

---

## Documentation Reference

### Documentation Interne
- **CLAUDE.md** : Instructions Claude Code v3.1
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

**Version** : 5.1
**Derniere revision** : 14 Decembre 2025
**Statut** : Phases 1-3 & 5 auditees, Phase 4 en attente, CLAUDE.md v3.2 actif
