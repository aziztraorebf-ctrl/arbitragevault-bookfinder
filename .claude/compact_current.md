# ArbitrageVault BookFinder - Memoire Active Session

**Derniere mise a jour** : 27 Mars 2026 (session 3 — fin)
**Phase Actuelle** : Sourcing Strategy Calibration COMPLETE + Scoring Fix Deployed
**Statut Global** : Production LIVE, pipeline fonctionnel, CoWork pret

---

## QUICK REFERENCE

| Metrique | Status |
|----------|--------|
| **Phase Actuelle** | Calibration + Scoring Fix COMPLETE |
| **Prochaine Action** | Utiliser CoWork pour scans automatiques 3-4x/jour |
| **Production** | Backend Render + Frontend Netlify LIVE |
| **Tests Total** | 986 passed, 0 failed, 26 skipped |
| **Bloqueurs** | Aucun |

---

## CONTEXTE SESSION 3 — Resume complet

### Ce qui a ete fait

1. **Recherche marche approfondie** (5 recherches Perplexity Deep Research + Reddit/X)
   - Prime Bump elimine nov 2025 (85% -> 13% Buy Box FBA)
   - Modele online =/= modele thrift (seuils differents)
   - Max 5-8 vendeurs FBA pour petit vendeur
   - Textbook toujours viable dans les niches (nursing, engineering, CS, law)
   - FBA Prep Service supprime 1er jan 2026

2. **Plan de calibration execute** (PR #30, 7 taches + 50 tests fixes)
   - source_price_factor unifie a 0.40
   - BSR/ROI/profit floor/max_fba_sellers calibres par strategie
   - condition_signal WEAK = disqualificateur
   - 50 tests pre-existants casses corriges
   - DB prod seedee, endpoints CoWork valides

3. **CoWork Playbook cree** (`docs/COWORK_PLAYBOOK.md`)
   - Runbook operationnel pour automatisation 3-4x/jour
   - Routines, alertes SMS, dashboard, gestion erreurs
   - Categories corrigees (noms string, pas IDs numeriques)
   - Version GitHub sans token (placeholder), version locale avec token pour CoWork

4. **Bug scoring critique corrige** (commit 02598e6)
   - `compute_rating()` utilisait des defauts hardcodes (velocity_min=70) au lieu de lire la strategie active
   - Ajout filtre BSR manquant dans le pipeline scoring
   - Resultat : Books passe de 0 picks a 4, Medical de 20 a 4 (faux positifs elimines)

### Resultats des scans en production (apres tous les fix)

| Categorie | Picks trouves | Commentaire |
|-----------|---------------|-------------|
| Books (general) | 4 | Avant fix: 0 (tout bloque par defauts hardcodes) |
| Medical Books | 4 | Avant fix: 20 (faux positifs, pas de filtre BSR) |
| Computer Science | 2 | Filtrage correct |
| Daily Buy List | 0 STABLE | Normal — besoin 2+ sightings pour devenir STABLE |

---

## SEUILS ACTIFS EN PRODUCTION

| Strategie | BSR max | ROI min | Profit min | Max FBA | Velocity min | Stability min |
|-----------|---------|---------|------------|---------|-------------|---------------|
| VELOCITY | 75,000 | 30% | $8 | 5 | 60 | 40 |
| BALANCED | 100,000 | 30% | $10 | 6 | 40 | 50 |
| TEXTBOOK | 250,000 | 35% | $12 | 8 | 20 | 60 |

- `source_price_factor = 0.40` | `fba_fee_percentage = 0.22`
- `reject_weak = true` (threshold 20%)
- Scoring enrichi : velocity_min et stability_min lus depuis la strategie active

---

## COWORK — Pret a utiliser

**Fichiers a charger dans CoWork :**
- `docs/COWORK_PLAYBOOK.md` — quoi faire, quand, comment decider
- `docs/AGENT_CONTEXT.md` — reference technique API
- Note : la version locale du playbook contient le Bearer token, la version GitHub a un placeholder

**Projet Claude Desktop :** "arbitrage vault orchestration" configure

---

## PROCHAINES ACTIONS

### Immediat
1. [ ] Lancer CoWork pour les premiers scans automatiques
2. [ ] Attendre 2-3 scans pour que des picks deviennent STABLE
3. [ ] Verifier le premier daily-buy-list avec des STABLE picks

### Moyen terme
4. [ ] P3 Refactoring : Split keepa_product_finder.py (1413 LOC)
5. [ ] Niche Watchlist Sniping : Connecter ASIN tracking a SMS/email

---

## COMMITS SESSION 3

| Commit | Description |
|--------|-------------|
| b6d6aae | Calibration sourcing + 50 tests fixes (PR #30) |
| 39e692d | CoWork Playbook + memory files |
| 562cfa5 | Correction categories playbook (string names) |
| 02598e6 | Fix scoring enrichment + filtre BSR manquant |

---

**Derniere mise a jour** : 27 Mars 2026 (session 3 — fin)
