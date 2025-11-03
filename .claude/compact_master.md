# ArbitrageVault BookFinder - Mémoire Globale Projet

**Dernière mise à jour** : 3 Novembre 2025
**Version** : 2.0
**Statut** : Phases 1-5 complétées, Phase 6 en cours (Tests E2E & Debugging)

---

## 📋 Vue d'Ensemble

**Objectif** : Plateforme d'analyse arbitrage Amazon via API Keepa pour identifier opportunités achat/revente rentables.

**Public Cible** : Revendeurs Amazon FBA (Fulfilled by Amazon)

**Proposition de Valeur** :
- Analyse ROI automatisée (marge profit %)
- Scoring vélocité vente (vitesse rotation stock)
- Discovery produits rentables via Product Finder Keepa
- Dashboard décisionnel temps réel

---

## 🏗️ Architecture Technique

### Stack Backend
- **Framework** : FastAPI 0.115.0 (Python 3.14)
- **Base de données** : PostgreSQL 17 (Neon serverless)
- **ORM** : SQLAlchemy 2.0 (async)
- **Migrations** : Alembic
- **API externe** : Keepa API (Product + Product Finder)
- **Logging** : structlog + Sentry
- **Déploiement** : Render (Docker)

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
- **Backend** : Render Web Service (Linux)
- **Frontend** : Netlify Static Site
- **MCP Servers** : GitHub, Context7, Render, Netlify, Neon, Keepa

---

## 📊 Phases Projet - Vue Globale

### ✅ Phase 1 : Core Analysis Engine (COMPLÉTÉ)
**Durée** : ~3 semaines
**Objectif** : Moteur analyse ROI/vélocité fonctionnel

**Livrables majeurs** :
- Parser Keepa API v2 (prix, BSR, offres)
- Calcul ROI avec fees Amazon
- Scoring vélocité (BSR → vitesse vente)
- Endpoints `/api/v1/keepa/{asin}/metrics`
- Tests unitaires + intégration (50+ tests)

**Métriques** :
- ROI : 30%+ = BUY, 50%+ = STRONG BUY
- Vélocité : 80+ = FAST, 60-80 = MEDIUM
- Performance : < 500ms analyse single ASIN

### ✅ Phase 2 : Config Service + Product Finder (COMPLÉTÉ)
**Durée** : ~2 semaines
**Objectif** : Configuration business dynamique + discovery produits

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
**Durée** : 3.5 semaines (28 Oct - 31 Oct 2025)
**Objectif** : Interface discovery produits avec templates niches

**Jours 1-8 : Backend Foundation**
- PostgreSQL cache tables (discovery, scoring, search history)
- React Query hooks + Zod validation
- Endpoints `/api/v1/products/discover` et `discover-with-scoring`
- E2E testing avec vraies données Keepa
- Throttling Keepa (20 req/min, burst 200)

**Jours 9-10 : Niche Discovery + Throttling**
- Templates niches curées (tech-books-python, french-learning, etc.)
- Validation multi-critères (BSR, offres, marge)
- Système throttling complet (rate + budget)
- E2E validation production

**Métriques Day 10** :
- Tokens Keepa disponibles : 670+
- Niches templates : 5 curées
- Cache TTL : 24h discovery, 6h scoring
- Protection throttling : ✅ Multi-niveaux

### ✅ Phase 4 : Backlog Cleanup (COMPLÉTÉ)
**Durée** : 1 journée (31 Oct 2025)
**Objectif** : Fixes critiques + protection budget Keepa

**Phase 4.0 : Backlog Original**
- ✅ Fix BSR extraction (bug critique ~67% erreur)
- ✅ Fix `hit_rate` key manquante
- ✅ Investigation `/products/discover` (0 ASINs)
- ✅ Windows ProactorEventLoop compatibility

**Phase 4.5 : Budget Protection**
- ✅ Détection gap throttling (rythme OK, budget non protégé)
- ✅ Implémentation `_ensure_sufficient_balance()`
- ✅ Mapping coûts endpoints (`ENDPOINT_COSTS`)
- ✅ Exception `InsufficientTokensError`
- ✅ Frontend display balance Keepa

**Phase 4.5.1 : Frontend Balance Display**
- ✅ Dashboard Keepa tokens restants
- ✅ Color coding (vert >200, orange 50-200, rouge <50)
- ✅ Integration avec backend `/api/v1/keepa/health`

**Commit final** : `093692e` (1 Nov 2025)
**Documentation** : KNOWN_ISSUES.md créé

### ✅ Phase 5 : Niche Bookmarks & Re-Run Feature (COMPLÉTÉ)
**Durée** : ~6 heures (2-3 Nov 2025)
**Objectif** : Sauvegarder niches découvertes et relancer analyses avec données fraîches

**Livrables majeurs** :
- Backend bookmarks endpoints (CRUD niches sauvegardées)
- Database migration (table `saved_niches`)
- Frontend React Query hooks pour bookmarks
- Bouton "Save Niche" avec toast notifications
- Page "Mes Niches" avec gestion complète (CREATE, READ, UPDATE, DELETE)
- Re-run analysis avec `force_refresh` parameter
- Strategic views avec target pricing

**6 Commits Phase 5** :
1. `7b92832` - Backend bookmarks endpoints + migration
2. `92b9e81` - TypeScript service layer + React Query
3. `1f010b1` - Save button + Toaster notifications
4. `17b8710` - Mes Niches page (CRUD)
5. `2f4aec2` - Frontend re-run implementation
6. `00ff975` - Backend force_refresh support

**2 Render Deployments (LIVE)** :
- `dep-d440g3gdl3ps73f9nivg` - Bookmarks endpoints
- `dep-d440qe2dbo4c73br2u3g` - force_refresh support

**Code Metrics** :
- Total lines : 1328
- Files created : 11
- Files modified : 6
- TypeScript errors : 0
- Database migrations : 1 applied

**Documentation créée** :
- `phase5_niche_bookmarks_completion_report.md` (508 lignes)
- `niche_bookmarks_e2e_test_plan.md` (296 lignes)

### 🟡 Phase 6 : Tests E2E & Debugging (EN COURS)
**Durée** : En cours (3 Nov 2025)
**Objectif** : Valider Phase 5 avec tests automatisés Playwright et corriger bugs

**Infrastructure nouvelle** :
- Playwright skill installée en standalone mode (`.claude/skills/playwright-skill/`)
- Headless browser automation pour E2E testing
- API response capturing et console error logging
- Screenshots pour debug visuel

**Tests E2E Plan** (5 scenarios) :
1. **Surprise Me Flow** : Button click → 3+ niches appear ⏱️ RUNNING (bug detected)
2. **Keepa Balance** : Display tokens with color coding ⏳ PENDING
3. **Save Niche** : Toast notification + DB insert ⏳ PENDING
4. **Mes Niches CRUD** : List, update, delete niches ⏳ PENDING
5. **Re-run with Force Refresh** : Fresh Keepa data ⏳ PENDING

**Bug #1 Identified** : "Surprise Me Returns 0 Niches
- **Detection** : Playwright test + API response capture
- **Symptom** : API returns `{niches: [], niches_count: 0}` (200 OK)
- **Root Cause** : `discover_curated_niches()` filters rejecting ALL templates
- **Suspected Filters** : ROI >= 10%, Velocity >= 20, Min 1 product
- **Status** : Under investigation (logging added to identify failing filters)
- **ETA Fix** : 30-60 minutes

**Playwright Tests Created** :
- `test-surprise-me.js` : Basic flow test
- `test-surprise-debug.js` : Advanced debugging with API capture

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
async def discover_products(criteria: dict) -> List[str]  # ASINs
async def check_api_balance() -> int  # Tokens left
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
# AVANT (ligne 458) :
bsr = rank_data[1]  # ❌ Premier BSR (obsolète)

# APRÈS (ligne 460) :
bsr = rank_data[-1]  # ✅ Dernier BSR (current)
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

**Scopes** :
- `global` : Paramètres par défaut
- `domain:{id}` : Paramètres par marketplace (US, UK, etc.)
- `category:{name}` : Paramètres par catégorie (books, media, etc.)

**Merge strategy** : global ← domain ← category

**Features** :
- Preview mode (test avant apply)
- Audit trail (change history)
- Optimistic locking (version checking)

### 5. Niche Templates (`niche_templates.py`)
**Responsabilité** : Templates niches marché curées

**Templates Phase 3** :
- `tech-books-python` : Livres Python débutants $20-50
- `french-learning` : Méthodes apprentissage français
- `kids-science-kits` : Kits scientifiques enfants
- `vintage-vinyl-records` : Vinyles vintage années 60-80
- `professional-cookbooks` : Livres cuisine professionnels

**Critères validation** :
- BSR range : 10,000 - 200,000
- Prix range : $15 - $80
- Max offres : ≤5 vendeurs
- Marge minimum : 25%

**Windows fix** : Wrapper ProactorEventLoop → SelectorEventLoop

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
- **Token protection** : 100% (post Phase 4.5)
- **Rollback DB** : 100% sur exceptions

### Coûts Keepa
- **Analyse 1 ASIN** : 1 token
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

### 3. Windows ProactorEventLoop
**Erreur** : psycopg3 async incompatible
**Impact** : Dev local Windows bloqué
**Fix** : Wrapper SelectorEventLoop (Phase 4)

### 4. Transaction Cascade
**Erreur** : Pas de rollback sur exception
**Impact** : InFailedSqlTransaction bloquant
**Fix** : `await db.rollback()` explicit

### 5. Validation Mock Data
**Erreur** : Tests avec mocks sans vraies données
**Impact** : Bugs passent inaperçus
**Fix** : E2E avec Keepa API réelle

---

## 📖 Documentation Référence

### Documentation Interne
- Architecture : [ARCHITECTURE.md](backend/doc/ARCHITECTURE.md)
- Known Issues : [KNOWN_ISSUES.md](backend/doc/KNOWN_ISSUES.md)
- Phase reports : [backend/doc/phase*.md](backend/doc/)

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

## 🎯 Objectifs Phases Futures

### Phase 6 : Tests E2E & Debugging (EN COURS)
Voir section Phase 6 ci-dessus pour détails en cours.

### Phase 7 : Netlify Frontend Deployment & Optimization (À VENIR)
**Durée estimée** : 1-2 jours

**Objectifs** :
- Deploy frontend sur Netlify production
- Environment switching (local, staging, production)
- Error boundary + error tracking (Sentry)
- Performance optimization (lazy loading, code splitting)

### Phase 8 : AutoSourcing Automation (À VENIR)
**Durée estimée** : 3-4 semaines

**Objectifs** :
- Jobs AutoSourcing programmés
- Profiles discovery réutilisables
- Notifications opportunités
- Export résultats CSV/PDF
- Scheduler module avec pause/resume

---

## 📞 Contacts & Liens

**Repository** : https://github.com/aziztraorebf-ctrl/arbitragevault-bookfinder
**Backend Production** : https://arbitragevault-backend-v2.onrender.com
**Frontend Staging** : (À déployer Phase 5)
**Database** : Neon PostgreSQL `ep-damp-thunder-ado6n9o2`

**Développeur Principal** : Aziz Trabelsi
**Assistant IA** : Claude Code (Anthropic)
**Stack MCP** : GitHub + Context7 + Render + Netlify + Neon

---

**Version** : 2.0
**Dernière révision** : 3 Novembre 2025
**Statut** : Phases 1-5 complétées, Phase 6 en cours (Tests E2E & Debugging)
