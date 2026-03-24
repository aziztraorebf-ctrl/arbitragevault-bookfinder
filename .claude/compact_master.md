# ArbitrageVault BookFinder - Memoire Globale Projet

**Derniere mise a jour** : 24 Mars 2026
**Version** : 9.0
**Statut** : Phases 1-13 + Phase 3 + Phase C + Bugfixes 35+ completes, Production LIVE

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

---

## Architecture Technique

### Stack Backend
- **Framework** : FastAPI 0.115.0 (Python 3.11+)
- **Base de donnees** : PostgreSQL 17 (Neon serverless)
- **ORM** : SQLAlchemy 2.0 (async)
- **Migrations** : Alembic
- **API externe** : Keepa API (Product + Product Finder)
- **Authentification** : Firebase Admin SDK
- **Logging** : structlog + Sentry
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

### Phase 10 : Unified Product Table (1 Jan 2026)

**Objectif** : Unifier composants ViewResultsTable + ProductsTable

**Livrables** :
- Type `DisplayableProduct` unifie
- `UnifiedProductTable.tsx` reutilisable
- Suppression pages redundantes
- 7 tests E2E Playwright

### Phase 11 : Page Centrale Recherches (1 Jan 2026)

**Objectif** : Centraliser tous les resultats de recherches

**Livrables** :
- Table `search_results` PostgreSQL (retention 30 jours)
- Page `/recherches` ("Mes Recherches")
- `SaveSearchButton` integre dans modules
- Service + Hooks React Query

### Phase 12 : UX Audit + Mobile-First (3 Jan 2026)

**Objectif** : Optimiser UX mobile et onboarding

**Livrables** :
- Sidebar responsive hamburger menu
- Tables scroll horizontal + sticky headers
- Touch targets 44px minimum
- Wizard onboarding 3 etapes

### Phase 13 : Firebase Authentication (10 Jan 2026)

**Objectif** : Remplacer JWT interne par Firebase Auth

**Fichiers crees Frontend** :
- `config/firebase.ts` - Configuration resiliente
- `contexts/AuthContext.tsx` - Context + hooks
- `components/auth/*` - Login, Register, PasswordReset, ProtectedRoute
- `pages/Login.tsx`, `Register.tsx`

**Fichiers crees Backend** :
- `core/firebase.py` - Firebase Admin SDK init
- `services/firebase_auth_service.py` - Token verification
- `repositories/user_repository.py` - CRUD avec firebase_uid

**Fichiers modifies** :
- `core/auth.py` - JWT -> Firebase token verification
- `models/user.py` - Ajout `firebase_uid`
- `pyproject.toml` - firebase-admin, email-validator

**Bugs fixes production** :
1. White screen Netlify (Firebase init resilient)
2. ModuleNotFoundError firebase_admin
3. ImportError email-validator
4. Network Error (VITE_API_URL mauvaise URL)

---

## Modules Cles

### Authentication (`core/auth.py`)

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    auth_service = FirebaseAuthService(db)
    user, _ = await auth_service.verify_token_and_get_user(token)
    return CurrentUser(id=user.id, email=user.email, role=user.role, ...)
```

### Keepa Service (`keepa_service.py`)
- Cache intelligent 24h production
- Throttling 20 req/min + budget check
- Retry avec exponential backoff

### AutoSourcing Service (`autosourcing_service.py`)
- Cost estimation avant execution
- Timeout 120s avec DB propagation
- ASIN deduplication

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

### Phase 3 : Simplification Radicale (21 Fev 2026)

**Objectif** : Simplifier selon methodologie BookMine (43 videos analysees).
Focus workflow core : AutoSourcing -> Daily Review -> Decision d'achat.

**Methode** : Archivage dans `_archive/` (pas suppression) pour recovery facile.

**Frontend** : 45 fichiers archives, navigation de 10 items a 4 (Dashboard, Sourcing, Scheduler, Settings)
**Backend** : 30 fichiers archives, main.py de 20 routers a 11, ~60 routes
**Tests** : 32 fichiers archives, 785 tests restants passent
**Dependance resolue** : VIEW_WEIGHTS inlined dans unified_analysis.py

**Decisions strategiques (BookMine Feb 2026)** :
- Prime Bump mort depuis Nov 3 2025 (Buy Box change)
- Condition Bump : Amazon priorise condition > prix > shipping
- Intrinsic Value = seul pricing model qui compte
- 5 signaux Keepa : lowest used price, sales rank drops, Amazon price, offer count, stock qty

### Phase C : Condition Signals + Pydantic v2 Fix (24 Mars 2026)

**Objectif** : Integrer condition signals dans le pipeline unifie, corriger deprecations Pydantic.

**Condition Signals (unified_analysis.py)** :
- Step 5.5 : Derivation `condition_signal` (STRONG/MODERATE/WEAK) depuis ROI + total used offer count
- Confidence boost : +10 (STRONG), +5 (MODERATE) via config `condition_signals`
- `condition_breakdown` dans buying_guidance (labels FR, trie par ROI)
- Alignement avec logique autosourcing_service existante

**Pydantic v2 Fix (analytics.py)** :
- `decimal_places=2` deprecie -> `field_validator` + `round(v, 2)`
- Defaults `Decimal("...")` au lieu de float literals

**Bugfixes 35+ (Mars 2026)** :
- 25 critiques : pipeline AutoSourcing, dedup ASIN, scoring, classification, frontend
- 12 MEDIUM : dedup, scoring formulas, frontend composants
- 3 LOW : Keepa indices (RATING=16, COUNT_REVIEWS=17), webhook session, docs
- PRs : #14, #15, #17, #19

**Tests** : 24 nouveaux (test_phase_c_enhancements.py), 289/290 service tests passent

---

## Prochaines Etapes

| Priorite | Phase | Description | Status |
|----------|-------|-------------|--------|
| 1 | - | Tests pre-deploy + Deploy production | A FAIRE |
| 2 | 15 | Replenishable Watchlist | OPTIONNEL |
| 3 | - | Migration DB drop tables archivees | QUAND STABLE |
| 4 | 14 | Integration N8N | FUTUR |

---

## Documentation

| Document | Description |
|----------|-------------|
| CLAUDE.md | Instructions v5.2 + Senior Review Gate |
| compact_current.md | Memoire session active |
| compact_master.md | Memoire globale (ce fichier) |
| errors.md | Registre bugs catalogues avec codes domaine |
| `_archive/` | Code archive (frontend + backend) |

---

**Version** : 9.0
**Derniere revision** : 24 Mars 2026
**Statut** : Phases 1-13 + Phase 3 + Phase C + Bugfixes completes
