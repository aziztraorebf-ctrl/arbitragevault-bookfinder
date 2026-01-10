# ArbitrageVault BookFinder - Memoire Globale Projet

**Derniere mise a jour** : 10 Janvier 2026
**Version** : 7.0
**Statut** : Phases 1-13 completes, Production LIVE avec Firebase Auth

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

---

## Prochaines Etapes

| Priorite | Phase | Description | Status |
|----------|-------|-------------|--------|
| 1 | - | Tests manuels 1-2 mois | A FAIRE |
| 2 | 14 | Integration N8N | FUTUR |
| 3 | 15 | ML predictions | FUTUR |

### Vision N8N (Phase 14)
- API webhooks pour automatisation
- Jobs planifies nuit/matin
- Resultats automatiques dans `/recherches`

### Vision ML (Phase 15+)
- Table `purchase_decisions` pour training
- A implementer apres 2-3 mois de donnees

---

## Documentation

| Document | Description |
|----------|-------------|
| CLAUDE.md | Instructions v3.3 + Senior Review Gate |
| compact_current.md | Memoire session active |
| compact_master.md | Memoire globale (ce fichier) |

---

**Version** : 7.0
**Derniere revision** : 10 Janvier 2026
**Statut** : Phases 1-13 completes, Firebase Auth LIVE
