# ArbitrageVault BookFinder - Memoire Active Session

**Derniere mise a jour** : 27 Mars 2026 (session 3 — fin)
**Phase Actuelle** : Sourcing Strategy Calibration COMPLETE + Deployed
**Statut Global** : Phases 1-13 + Phase 3 + Phase C + Bugfixes + Security + Agent API + Codebase Audit + P2 + Sourcing Calibration completes, Production LIVE

---

## QUICK REFERENCE

| Metrique | Status |
|----------|--------|
| **Phase Actuelle** | Sourcing Calibration COMPLETE — PR #30 mergee, prod seedee |
| **Prochaine Action** | Configurer CoWork dans Claude Desktop pour automatisation 3-4x/jour |
| **CLAUDE.md** | v3.3 - Zero-Tolerance Engineering |
| **Production** | Backend Render + Frontend Netlify LIVE |
| **Authentification** | Firebase Auth (Email/Password) |
| **Tests Total** | 986 passed, 0 failed, 26 skipped |
| **Bloqueurs** | Aucun |
| **Environnement** | macOS (migration depuis Windows jan 2026) |

---

## CONTEXTE SESSION 3 — Ce qui a ete fait et pourquoi

### Recherche marche approfondie (Perplexity Deep Research + Reddit/X)

Avant d'ecrire du code, 5 recherches ont ete menees pour comprendre le marche FBA book arbitrage en 2026. Resultats cles :

1. **Prime Bump elimine (nov 2025)** : FBA ne gagne plus le Buy Box automatiquement. 85% -> 13% en 12 mois. L'algorithme favorise maintenant la condition (Very Good domine) et le prix. Notre `intrinsic_value` et `condition_signal` sont bien positionnes pour ce nouveau paradigme.

2. **Modele online =/= modele thrift** : Les guides generaux (BSR 500K, ROI 30%) s'appliquent aux vendeurs qui sourcent a $1-2 en magasin. Pour du Amazon-to-Amazon a $8-20 de cout source, il faut etre plus strict : BSR max 75K (velocity), profit minimum $8-12/livre.

3. **Competition vendeurs FBA** : Pour un petit vendeur (1-3 copies/titre), plus de 5-8 vendeurs FBA sur un listing = capital mort. Le "40 vendeurs max" est une regle pour les gros volumes.

4. **Textbook toujours viable** : Le marche physique tient (70% des etudiants achetent encore), mais les access codes et OpenStax (72% des colleges) grugent le marche. La strategie textbook fonctionne dans les niches specialisees (nursing, engineering, law, CS) ou les access codes sont moins frequents. Le BSR textbook est saisonnier — 250K hors-saison peut etre 15K en aout.

5. **FBA Prep Service supprime** (1er jan 2026, confirme). Pas d'impact sur l'app, mais impact operationnel pour le vendeur.

### Plan execute : 7 taches + 50 tests fixes

**PR #30** : `fix/sourcing-strategy-calibration` — squash-merged dans main le 27 mars 2026.
Commit : `b6d6aae`

| Tache | Description | Fichiers | Status |
|-------|-------------|----------|--------|
| 1 | Verifier source_price_factor en prod | Query Neon | source_price_factor existait deja |
| 2 | Unifier source_price_factor a 0.40 | autosourcing_service, daily_review, config, seed script | FAIT |
| 3 | Recalibrer seuils BSR/ROI/profit/sellers | business_rules.json | FAIT |
| 4 | Activer filtre max_fba_sellers dans pipeline | autosourcing_scoring, autosourcing_service | FAIT |
| 5 | Ajouter filtre profit absolu minimum | autosourcing_scoring, autosourcing_service | FAIT |
| 6 | Elever condition_signal WEAK disqualificateur | daily_review_service, business_rules.json | FAIT |
| 7 | Validation prod + doc CoWork | AGENT_CONTEXT.md, smoke tests | FAIT |
| +  | Corriger 50 tests pre-existants casses | 13 fichiers test | FAIT |

### Post-merge : prod seedee et validee

- `seed_source_price_factor.py` execute en prod Neon — version 5, valeur 0.40
- 4 endpoints CoWork testes en prod : dashboard-summary, daily-buy-list, keepa-balance, last-job-stats — tous OK
- 0 picks dans daily-buy-list (normal — pas de scan depuis le merge avec les nouveaux seuils)

---

## SEUILS ACTIFS EN PRODUCTION (post-calibration)

| Strategie | BSR max | ROI min | Profit min | Max FBA sellers | Holding |
|-----------|---------|---------|------------|-----------------|---------|
| VELOCITY | 75,000 | 30% | $8 | 5 | 7-30j |
| BALANCED | 100,000 | 30% | $10 | 6 | 14-60j |
| TEXTBOOK | 250,000 | 35% | $12 | 8 | 45-90j |

- `source_price_factor = 0.40` (unifie, DB prod = 0.40)
- `fba_fee_percentage = 0.22`
- `reject_weak = true` (condition WEAK + ROI < 20% = REJECT)

---

## COWORK AGENT ENDPOINTS (6 endpoints — tous valides en prod)

| Endpoint | Methode | Limite | Status prod |
|----------|---------|--------|-------------|
| `/cowork/dashboard-summary` | GET | 30/min | OK |
| `/cowork/fetch-and-score` | POST | 5/min | Non teste (a lancer) |
| `/cowork/daily-buy-list` | GET | 30/min | OK (0 items — normal) |
| `/cowork/last-job-stats` | GET | 30/min | OK |
| `/cowork/keepa-balance` | GET | 30/min | OK (486 tokens) |
| `/cowork/jobs` | GET | 30/min | Non teste |

---

## PRODUCTION

| Service | URL |
|---------|-----|
| Backend | https://arbitragevault-backend-v2.onrender.com |
| Frontend | https://arbitragevault.netlify.app |

---

## DECISIONS ARCHITECTURALES — SESSION 3

| Date | Decision | Pourquoi | Impact |
|------|----------|----------|--------|
| 26 mars | source_price_factor unifie a 0.40 | 3 valeurs differentes (0.50/0.35/0.40) dans le code. 0.40 = realiste pour sourcing online $8-20 | Tous les calculs ROI du pipeline |
| 26 mars | BSR max textbook elargi a 250K | BSR saisonnier — BSR 250K hors-saison peut etre BSR 15K en aout. Avec guard : seasonal_bsr_check | Recherche Perplexity confirme |
| 26 mars | BSR max velocity reduit a 75K | BSR >100K = 0.5-1.5 ventes/mois, holding 150-300j. Inviable online | Moins de picks mais plus fiables |
| 26 mars | Max FBA sellers par strategie (5-8) | Petit vendeur (1-3 copies) ne compete pas avec 40+ FBA | Nouveau filtre dans pipeline scoring |
| 26 mars | condition_signal WEAK = disqualificateur | Post-Prime-Bump : condition Very Good domine Buy Box | reject_weak=true, threshold 20% |
| 26 mars | Profit absolu minimum par strategie | ROI % seul ne suffit pas — besoin $8-12 minimum | min_profit_dollars dans business_rules |
| 27 mars | Niche Watchlist = phase future | Keepa Product Finder ne filtre pas par sous-categorie. La vraie strategie niche = ASIN tracking + SMS alertes. Pas un besoin immediat | Documente dans memoire, pas implemente |
| 27 mars | Access codes non filtrables | Pas de donnee Keepa sur les access codes. Le BSR saisonnier filtre naturellement les livres morts | Aucun filtre a ajouter |

---

## PROCHAINES ACTIONS

### Immediat
1. [ ] **Configurer CoWork dans Claude Desktop** pour automatisation 3-4x/jour
   - CoWork appelle `/cowork/fetch-and-score` avec Bearer token
   - SMS via Textbelt pour les picks STABLE
   - Dashboard HTML sur tiiny.host ou Cloudflare Pages

### Court terme
2. [ ] **Lancer un premier scan prod** via `/cowork/fetch-and-score` pour valider les nouveaux seuils
3. [ ] **Deploy Render** si auto-deploy n'est pas actif (verifier que le merge a declenche un deploy)

### Moyen terme
4. [ ] P3 Refactoring : Split keepa_product_finder.py (1413 LOC)
5. [ ] P3 Refactoring : Extraire pick_to_dict() helper (4 duplications)
6. [ ] P3 Refactoring : asyncio.gather pour dashboard queries

### Future phase : Niche Watchlist Sniping
7. [ ] Connecter asin_tracking_service a notification_service (SMS/email sur price drop)
8. [ ] Constituer watchlist de 50-100 ASINs textbook (nursing, engineering, CS, law)
9. [ ] Alerte SMS quand prix drop >25% sur un ASIN watchlist

---

## INFRASTRUCTURE

### MCP servers (scope user, global)
context7, github, netlify, render, neon, vercel, supabase, sentry, playwright, sequential-thinking

### Cles API configurees
- `~/.config/last30days/.env` : OPENAI_API_KEY + XAI_API_KEY + OPENROUTER_API_KEY
- `backend/.env` : OPENROUTER_API_KEY, KEEPA_API_KEY, DATABASE_URL, etc.
- Render prod : RESEND_API_KEY + TEXTBELT_API_KEY configures

---

**Derniere mise a jour** : 27 Mars 2026 (session 3 — fin)
