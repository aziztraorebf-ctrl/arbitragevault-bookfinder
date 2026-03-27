# ArbitrageVault BookFinder - Memoire Globale Projet

**Derniere mise a jour** : 26 Mars 2026
**Version** : 11.0
**Statut** : Phases 1-13 + Phase 3 + Phase C + Bugfixes + Security + Agent API + Codebase Audit + P2 completes, Production LIVE

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
- Authentification securisee Firebase
- Integration agents externes (CoWork/N8N) avec API dedicee

---

## Architecture Technique

### Stack Backend
- **Framework** : FastAPI 0.111.0 (Python 3.11+)
- **Base de donnees** : PostgreSQL 17 (Neon serverless)
- **ORM** : SQLAlchemy 2.0 (async)
- **Migrations** : Alembic
- **API externe** : Keepa API (Product + Product Finder)
- **Authentification** : Firebase Admin SDK + API Keys + CoWork Bearer
- **Logging** : structlog + Sentry
- **Rate Limiting** : SlidingWindowLimiter in-memory (app/core/rate_limiter.py)
- **Deploiement** : Render (Docker, auto-deploy)

### Stack Frontend
- **Framework** : React 18 + TypeScript 5.6
- **Build** : Vite 6.0
- **Styling** : Tailwind CSS 4.0
- **Data Fetching** : React Query (TanStack Query)
- **Validation** : Zod 3.23
- **Routing** : React Router v7
- **Authentification** : Firebase SDK
- **Deploiement** : Netlify

### Infrastructure Production

| Service | URL |
|---------|-----|
| Backend | https://arbitragevault-backend-v2.onrender.com |
| Frontend | https://arbitragevault.netlify.app |
| Database | Neon PostgreSQL |
| Auth | Firebase Authentication |

---

## Phases Projet - Historique

### Phases 1-9 : Foundation -> UI (Nov-Dec 2025)

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| 1 | Foundation Audit | 21/21 | COMPLETE |
| 2 | Keepa Integration | 16/16 | COMPLETE |
| 3 | Product Discovery MVP | 32/32 | COMPLETE |
| 4 | Backlog Cleanup | 61/61 | COMPLETE |
| 5 | Niche Bookmarks | 42/42 | COMPLETE |
| 6 | Niche Discovery Optimization | 62/62 | COMPLETE |
| 7 | AutoSourcing Safeguards | 109/109 | COMPLETE |
| 8 | Advanced Analytics | 50+ | COMPLETE |
| 9 | UI Completion | 70+ | COMPLETE |

### Phases 10-13 : Polish + Auth (Jan 2026)
- Phase 10 : Unified Product Table
- Phase 11 : Page Centrale Recherches
- Phase 12 : UX Audit + Mobile-First
- Phase 13 : Firebase Authentication

### Refactoring 1A-2D (Jan-Fev 2026)
- 1A-1D : Architecture, dead code, SQLAlchemy 2.0
- 2A-2C : Validation, simplification, fees centralization
- 2D : Daily Review Dashboard

### Phase 3 : Simplification Radicale (21 Fev 2026)
- 45 fichiers frontend archives, 30 backend archives
- Navigation de 10 items a 4
- 785 tests restants passent

### Phase C : Condition Signals + Pydantic v2 Fix (24 Mars 2026)
- Condition signals dans pipeline unifie (STRONG/MODERATE/WEAK)
- Confidence boost +10/+5 via config
- Pydantic v2 field_validator

### Bugfixes 35+ (Mars 2026)
- 25 critiques + 12 MEDIUM + 3 LOW
- PRs #14, #15, #17, #19

### Security Audit + Agent API (24 Mars 2026)
- Rate limiting + security headers
- Script creation cle API agents
- Integration CoWork/N8N

### Codebase Audit + P2 Simplification (26 Mars 2026)

**Declencheur** : Bug `total_discovered` (attribut fantome avale par except Exception).

**Audit (PRs #27-30)** :
- 12 `except Exception` dangereux corriges (logging ajoute)
- 2 fichiers morts supprimes (-511 LOC)
- Pydantic response_model sur endpoints CoWork
- Timezone fix daily_review.py (aware -> naive)
- BSR standardise a -1 pour "unknown"
- `data_quality` flag (full/degraded/unavailable)
- /simplify : BSR bug, return types, data_quality gaps corriges

**P2 Endpoints** :
- `GET /cowork/keepa-balance` : balance tokens avec cache 60s
- `GET /cowork/jobs` : liste paginee avec filtre status

**P2 Rate Limiting** :
- `app/core/rate_limiter.py` : SlidingWindowLimiter in-memory
- GET 30 req/min, POST 5 req/min, HTTP 429 + Retry-After

**P2 ROI Consolidation** :
- `app/services/autosourcing_scoring.py` (212 LOC) : 8 fonctions extraites
- autosourcing_service.py reduit de 1244 a 1037 LOC
- Duplication ROI eliminee (etait copie-collee dans 2 methodes)

---

## Modules Cles

### Authentication (`core/auth.py`)
- Firebase token verification
- API Key auth pour agents (CoWork, N8N)
- CoWork Bearer token

### Keepa Service (`keepa_service.py`)
- Cache intelligent 24h production
- Throttling 20 req/min + budget check
- Circuit breaker + retry

### AutoSourcing Service (`autosourcing_service.py`, 1037 LOC)
- Cost estimation avant execution
- Timeout 120s avec DB propagation
- ASIN deduplication
- Scoring via `autosourcing_scoring.py` (module extrait)

### Rate Limiter (`core/rate_limiter.py`)
- Sliding window counter, zero dep externe
- Per-key tracking (token hash ou IP)
- Cleanup automatique des entrees perimees

### CoWork Router (`api/v1/routers/cowork.py`)
- 6 endpoints avec auth Bearer + rate limiting
- data_quality flag sur dashboard et buy-list
- Pydantic response models sur tous les endpoints

---

## Configuration Production

### Backend (Render)

```env
DATABASE_URL=postgresql://...@neon.tech/neondb
KEEPA_API_KEY=<secret>
FIREBASE_PROJECT_ID=<project>
FIREBASE_PRIVATE_KEY=<key>
FIREBASE_CLIENT_EMAIL=<email>
SENTRY_DSN=<dsn>
COWORK_API_TOKEN=<token>
```

### Frontend (Netlify)

```env
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
VITE_FIREBASE_API_KEY=<key>
VITE_FIREBASE_AUTH_DOMAIN=<domain>
VITE_FIREBASE_PROJECT_ID=<project>
VITE_FIREBASE_STORAGE_BUCKET=<bucket>
VITE_FIREBASE_MESSAGING_SENDER_ID=<id>
VITE_FIREBASE_APP_ID=<app_id>
```

---

## Erreurs Evitees (Lecons Apprises)

| Erreur | Impact | Fix |
|--------|--------|-----|
| Firebase init crash | White screen | Init resiliente try/catch |
| Mauvaise URL backend | Network Error | VITE_API_URL -> -v2 |
| BSR extraction obsolete | 67% erreur | `rank_data[-1]` |
| Throttle budget | Balance negative | `_ensure_sufficient_balance()` |
| `total_discovered` fantome | Donnees vides silencieuses | Attribut corrige + logging + test regression |
| `except Exception: pass` | Erreurs avalees | 12 cas corriges avec logging |
| `bsr or -1` avec bsr=0 | BSR valide converti en -1 | `if bsr is not None else -1` |
| datetime aware vs naive | Queries DB incorrectes | `datetime.utcnow()` partout |

---

## Sourcing Strategy Calibration (26 Mars 2026 - session 3)

**Contexte** : Recherche approfondie (Perplexity Deep Research + Reddit/X) a revele que les seuils de sourcing etaient calibres pour des thrift sellers ($1-2/livre), pas pour du online Amazon-to-Amazon ($8-20/livre). Prime Bump FBA elimine en nov 2025 (85% -> 13% Buy Box FBA).

**Plan** : `docs/plans/2026-03-26-sourcing-strategy-calibration.md` | Branche : `fix/sourcing-strategy-calibration`

| Changement | Avant | Apres | Raison |
|------------|-------|-------|--------|
| source_price_factor | 0.50/0.35/0.40 (3 valeurs!) | 0.40 unifie | ROI calcule correctement |
| BSR max velocity | 100,000 | 75,000 | >100K = 0.5-1.5 ventes/mois online |
| BSR max textbook | 300,000 | 250,000 | Saisonnier, avec check historique peak |
| ROI min textbook | 50% | 35% | 50% trop rare online |
| max_fba_sellers | Non actif | 5-8 par strategie | Filtre competition critique pour petit vendeur |
| min_profit_dollars | Non existant | $8-12 par strategie | ROI % seul insuffisant |
| condition_signal WEAK | Boost confiance seulement | Disqualificateur pour STABLE | Buy Box 2026 = condition-first |

---

## Prochaines Etapes

| Priorite | Description | Status |
|----------|-------------|--------|
| **0** | **Sourcing Strategy Calibration** (7 taches + 50 tests fixes) | COMPLETE (PR #30, commit b6d6aae, 27 mars) |
| 1 | **Configurer CoWork** dans Claude Desktop (automatisation 3-4x/jour) | A FAIRE |
| 2 | **P3 Refactoring** : Split keepa_product_finder.py (1413 LOC) | A FAIRE |
| 3 | **P3 Refactoring** : Extraire pick_to_dict() helper (4 duplications) | A FAIRE |
| 4 | **P3 Refactoring** : asyncio.gather pour dashboard queries | A FAIRE |
| 5 | **Niche Watchlist Sniping** : Connecter ASIN tracking a SMS/email | FUTURE PHASE |
| 6 | Migration DB drop tables archivees | QUAND STABLE |

---

## Documentation

| Document | Description |
|----------|-------------|
| CLAUDE.md | Instructions v3.3 + Senior Review Gate |
| compact_current.md | Memoire session active |
| compact_master.md | Memoire globale (ce fichier) |
| errors.md | Registre bugs catalogues avec codes domaine |
| AGENT_CONTEXT.md | Context file pour agents CoWork/N8N (v2.1, calibre mars 2026) |
| `_archive/` | Code archive (frontend + backend) |

---

**Version** : 13.0
**Derniere revision** : 27 Mars 2026 (session 3 — fin)
**Statut** : Phases 1-13 + Phase 3 + Phase C + Bugfixes + Security + Agent API + Codebase Audit + P2 + Sourcing Calibration completes
