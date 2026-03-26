# Known Issues - ArbitrageVault BookFinder

Document des bugs et limitations connus.

## Status: Post-P2 Simplification - March 26, 2026

---

## Limitations Actives

### Rate Limiter in-memory (single process)
- Le `SlidingWindowLimiter` est stocke en memoire dans le processus Render.
- Si Render relance le service, les compteurs sont remis a zero.
- Acceptable pour single-instance deployment, pas pour multi-instance scale-out.

### Velocity Score (approximation BSR)
- La velocity est derivee des drops BSR (chaque drop = une vente probable).
- Ce n'est pas une donnee de vente reelle Amazon — c'est une approximation.
- Keepa ne fournit pas le nombre de ventes directement.

### Keepa Off-Category Books
- Keepa retourne parfois des livres hors-categorie dans une plage BSR donnee.
- Comportement Keepa API, pas un bug de notre code.
- Mitigation : filtrage par `category` dans le scoring.

### BaseRepository.update() — Issue #5
- Ne peut pas setter un champ a `None` (filtre `v is not None`).
- Workaround documente dans le code, core business logic non impacte.

### Keepa Token Budget
- Environ 50 tokens consommes par produit avec offers.
- Un scan de 50 produits = ~2500 tokens.
- Surveiller via `GET /cowork/keepa-balance`.

---

## Bugs Corriges (26 Mars 2026 — Audit P2)

- `bsr or -1` traitait `bsr=0` (BSR valide) comme inconnu -> `if bsr is not None else -1`
- 12 `except Exception: pass` silencieux -> logging ajoute
- `data_quality` non propagee quand `history_map` echouait
- Return types incorrects sur endpoints CoWork (`dict` au lieu de `CoworkDashboardResponse`)
- Timezone mismatch dans `daily_review.py` (aware -> naive UTC)
- BSR standardise a `-1` pour "unknown" (etait inconsistant entre `0`, `None`, `-1`)

---

## Bugs Corriges (24 Mars 2026 — PRs #14, #15, #17)

### CRITICAL (8) — PR #14
- CoWork router: mauvaises cles dict (`total_picks` -> `total`/`classified_products`)
- CoWork router: `history_map={}` classait tous les produits FLUKE
- Pipeline: `JobStatus.FAILED` inexistant -> `JobStatus.ERROR`
- Pipeline: `except Exception` attrapait `HTTPException` du timeout
- Pipeline: double timeout (router + service)
- Scoring: BSR `elif` ordering avec code mort pour `bsr > 1M`
- Scoring: velocity calculee avec BuyBox price au lieu du BSR rank
- Frontend: `/recherches/stats` endpoint inexistant (404)

### HIGH (12) — PR #14
- Schema `DailyReviewResponse`: champ `classified_products` manquant
- `ActionableBuyItem.overall_rating`: type `float` -> `Optional[str]`
- Daily review: `stability_score` et `condition_signal` non passes
- Daily review: table `asin_history` inexistante -> `AutoSourcingPick`
- Classification: naive/aware datetime mismatch pour REVENANT
- `breakeven_price`: formule inversee
- `fba_count=0`: bug falsy-zero
- Velocity trend: comparaison incorrecte pour 7-13 points de donnees
- ROI clampe a 100% supprimait la differenciation
- Frontend AutoSourcing: `fetch()` sans auth Firebase
- Frontend: env var `VITE_API_BASE_URL` incorrecte

### MEDIUM (12) — PR #15
- Deduplication ASINs dans daily review et CoWork
- `engagement_rate`: formule corrigee (`total_actions/total_picks`)
- `job_id`: type `str` -> `UUID` dans endpoint tiers
- Category extraction: `categoryTree[-1]` au lieu de `[0]`
- `source_price_factor` default aligne a `0.35`
- `target_buy_price`: guard `max(0, ...)` contre negatifs
- velocity/confidence scores passes aux buy items
- `amazon_on_listing` NULL: `None` traite correctement (pas comme `False`)
- BSR null: `0` -> `-1`
- Frontend: throw quand 4/5+ fetches echouent
- Dead code: `_build_keepa_search_params` supprime
- `is_purchased`: plus set sur `TO_BUY` intent

### LOW (3) — PR #17
- Keepa constants: indices `RATING` (15->16), `COUNT_REVIEWS` (16->17)
- `_extract_rating()` lisait `array[15]` au lieu de `array[16]`
- `dispatch_webhook`: session DB expirée dans `asyncio.create_task` -> session fraiche

---

## Bugs Corriges (Mars 2026 — Phase C, PR #19)

- `decimal_places=2` deprecie Pydantic v2 -> `field_validator` + `round(v, 2)`
- Defaults Pydantic migres de `float` vers `Decimal("...")`

---

## Bugs Corriges (Dec 2025)

- Ecran blanc apres clic "Verifier" (`!== undefined` -> `!= null`, commit `25ea9d8`)
- Null checks inconsistants Smart Velocity standardises (`value != null`, commit `128813f`)

---

*Derniere mise a jour: 2026-03-26*
