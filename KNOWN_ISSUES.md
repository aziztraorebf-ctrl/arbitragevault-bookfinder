# Known Issues - ArbitrageVault BookFinder

Document des bugs et limitations connus.

## Status: Post-Phase 3 - Simplification Radicale Complete

---

## Bugs Corriges (Mars 2026 - Audit Complet)

### CRITICAL (8) - PR #14
- Cowork router: mauvaises cles dict (total_picks -> total/classified_products)
- Cowork router: history_map={} - tous les produits classes FLUKE
- Pipeline: JobStatus.FAILED n'existe pas -> JobStatus.ERROR
- Pipeline: except Exception attrapait HTTPException du timeout
- Pipeline: double timeout router + service
- Scoring: BSR elif ordering (bsr > 1M code mort)
- Scoring: velocity calculee avec BuyBox price au lieu du BSR rank
- Frontend: /recherches/stats endpoint inexistant (404)

### HIGH (12) - PR #14
- Schema DailyReviewResponse: champ classified_products manquant
- Schema ActionableBuyItem.overall_rating: float -> Optional[str]
- Daily review: stability_score et condition_signal non passes
- Daily review: table asin_history inexistante -> AutoSourcingPick
- Classification: naive/aware datetime mismatch REVENANT
- breakeven_price: formule inversee
- fba_count=0: bug falsy-zero
- Velocity trend: older_avg == recent_avg pour 7-13 points
- ROI clamping a 100% supprimait la differenciation
- Frontend AutoSourcing: fetch() sans auth Firebase -> api axios
- Frontend: variable VITE_API_BASE_URL incorrecte

### MEDIUM (12) - PR #15
- Deduplication ASINs daily review et cowork par ASIN
- engagement_rate: formule corrigee total_actions/total_picks
- job_id: str -> UUID dans tier endpoint
- category extraction: categoryTree[-1] au lieu de [0]
- source_price_factor: default aligne a 0.35
- target_buy_price: guard max(0, ...) contre negatifs
- velocity/confidence scores passes aux buy items
- amazon_on_listing NULL: None traite comme False
- BSR null: 0 au lieu de -1
- Frontend: throw quand 4/5+ fetches echouent
- Dead code: _build_keepa_search_params supprime
- is_purchased: plus set sur TO_BUY intent

### LOW (3) - PR #17
- Keepa constants: indices RATING(15->16), COUNT_REVIEWS(16->17), EXTRA_INFO_UPDATES=15 ajoute
- keepa_parser_v2: _extract_rating() lisait array[15] au lieu de array[16]
- dispatch_webhook: session DB potentiellement expiree dans asyncio.create_task (session fraiche creee)

---

## Bugs Corriges (Dec 2025)

### Ecran blanc apres clic "Verifier" (CORRIGE)
- **Commit**: `25ea9d8`
- **Fix**: `!== undefined` -> `!= null` dans ProductsTable.tsx

### Null check inconsistants Smart Velocity (CORRIGE)
- **Commit**: `128813f`
- **Fix**: Standardise `value != null`

---

## Limitations Connues

### API Keepa
- **Rate limiting**: 10 requetes/seconde
- **Tokens**: ~50 tokens par produit avec offers
- **Cache**: 1 heure par defaut

### BaseRepository.update() - Issue #5
- Ne peut pas set des champs a None (filtrage v is not None)
- Workaround documente, core business logic non impacte

---

*Derniere mise a jour: 2026-03-24*
