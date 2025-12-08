# ArbitrageVault BookFinder - Reference Master

**Stack** : FastAPI + React 18 + PostgreSQL + Keepa API
**Status** : Production Ready (6 Dec 2025)
**Tests** : 483 total (349+ unit + 56 E2E)

---

## Phases Completees

| Phase | Description | Tests |
|-------|-------------|-------|
| 1 | Database Foundation | 21/21 |
| 2 | Keepa Integration | 16/16 |
| 3 | Product Discovery + Velocity | 32/32 + 7 E2E |
| 4 | Production Readiness | Deployed |
| 5 | Token Control System | 12/12 E2E |
| 6 | Frontend E2E + Filters | 39/39 |
| 7 | AutoSourcing | 17/17 |

---

## Architecture

```
backend/app/
  services/
    keepa_service.py      # API client (api.query)
    keepa_product_finder.py  # Bestsellers/Deals
    autosourcing_service.py  # Job orchestration
    scoring_service.py    # ROI/Velocity scoring
  api/v1/               # FastAPI routes
  models/               # SQLAlchemy models
  schemas/              # Pydantic schemas

frontend/src/
  components/           # React components
  pages/               # Route pages
  utils/               # Helpers
```

---

## Keepa API Reference

### stats.current[] Indices
| Index | Nom | Usage |
|-------|-----|-------|
| 0 | AMAZON | Si > 0, Amazon vend |
| 1 | NEW | Prix 3rd party |
| 3 | SALES_RANK | BSR actuel |
| 11 | COUNT_NEW | Nombre FBA sellers |

### Token Costs
- `/product` : 1/ASIN
- `/bestsellers` : 50 flat
- `/deals` : 5/150 deals

### Rate Limits
- 20 tokens/minute
- Circuit breaker: 3 fails = 60s pause

---

## AutoSourcing Safeguards

| Limite | Valeur |
|--------|--------|
| MAX_TOKENS_PER_JOB | 200 |
| MIN_TOKEN_BALANCE | 50 |
| TIMEOUT | 120s |

### Strategies
| Nom | BSR Range | Max FBA |
|-----|-----------|---------|
| Smart Velocity | 10K-80K | 5 |
| Textbooks | 30K-250K | 3 |

---

## Endpoints Cles

**Backend** : `https://arbitragevault-backend-v2.onrender.com`

| Route | Description |
|-------|-------------|
| GET /api/v1/health/ready | Health check |
| GET /api/v1/keepa/health | Keepa status + tokens |
| POST /api/v1/autosourcing/run-custom | Job AutoSourcing |
| GET /api/v1/niches/discover | Niche discovery |

**Frontend** : `https://arbitragevault.netlify.app`

---

## Regles Critiques

1. **NO EMOJIS** dans .py, .ts, .js, .json
2. **Vraies donnees** : Pas de random/simulation en prod
3. **Tokens** : Toujours verifier balance avant operations
4. **Git** : Commits frequents, jamais de cles API

---

## Bugs Corriges (Reference)

| Bug | Fix | Commit |
|-----|-----|--------|
| BSR tuple unpacking | Unpack `Tuple[int,str]` correctly | ac002ee |
| velocity_min filtering | Direct check in `_meets_criteria()` | 507d0a6 |
| AutoSourcing simulation | Real Keepa API | d76ac25 |
| ZeroDivisionError velocity | Guard mean > 0 | 79b8bbd |
| Price extraction | current[1] not [0] | 7c2f28c |

---

## API Cache Bypass

Pour tests E2E avec vraies donnees Keepa :
```
GET /api/v1/keepa/{asin}/metrics?force_refresh=true
```
Consomme tokens Keepa (bypass PostgreSQL cache).

---

**Derniere MAJ** : 2025-12-08
