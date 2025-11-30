# Phase 6 Audit Plan - Niche Discovery Critical Fixes

**Date**: 30 Novembre 2025
**Phase**: 6 (Niche Discovery)
**Statut**: CRITIQUE - Bug token consumption identifie
**Auteur**: Claude Code avec Aziz Tsouli

---

## Executive Summary

Le module **Niche Discovery** presente un bug critique de **consommation de tokens sans resultats**.

**Probleme observe en production**:
- Utilisateur clique sur "Surprise Me"
- Balance: 830 tokens -> ~60 tokens (~770 tokens consommes)
- Resultat: Aucune niche affichee (timeout 30s)

**Root Cause**: Les tokens sont consommes AVANT le timeout. Le `asyncio.wait_for()` n'annule PAS les requetes Keepa en cours - il abandonne simplement l'attente.

---

## 1. Analyse Technique du Probleme

### 1.1 Flux de Consommation Actuel

```
[niches.py:92] asyncio.wait_for(discover_curated_niches(), timeout=30)
    |
    +-> [niche_templates.py:285] discover_with_scoring() pour chaque template (3x)
            |
            +-> [keepa_product_finder.py:103] _discover_via_bestsellers()
            |       Cost: 50 tokens par categorie
            |
            +-> [keepa_product_finder.py:173] _filter_asins_by_criteria()
                    Cost: 1 token par ASIN x 500 ASINs = ~500 tokens
```

**Estimation cout pour 3 niches**:
- 3 x bestsellers = 150 tokens
- 3 x ~500 ASINs filtrage = ~1500 tokens (si tous batch executes)
- **Total potentiel**: 1650+ tokens

### 1.2 Pourquoi le Timeout ne Protege Pas

```python
# niches.py:92-106 - Code actuel
try:
    niches = await asyncio.wait_for(
        discover_curated_niches(...),
        timeout=ENDPOINT_TIMEOUT  # 30s
    )
except asyncio.TimeoutError:
    await keepa.close()  # Ferme le client APRES les requetes
    raise HTTPException(status_code=408, ...)
```

**Probleme**:
- Les requetes Keepa sont fire-and-forget
- `asyncio.CancelledError` n'est pas propage aux sous-taches
- Les tokens sont debites cote Keepa au moment de l'appel API, pas de la reponse

### 1.3 Fichiers Impliques

| Fichier | Role | Lignes Critiques |
|---------|------|------------------|
| `backend/app/api/v1/endpoints/niches.py` | Endpoint API | 30-138 |
| `backend/app/services/niche_templates.py` | Templates curated | 191-339 |
| `backend/app/services/keepa_product_finder.py` | Discovery + filtering | 66-350 |
| `backend/app/core/guards/require_tokens.py` | Pre-check tokens | 10-70 |

---

## 2. Issues Identifiees (Par Priorite)

### CRITICAL-01: Tokens Consommes Sans Resultats

**Impact**: ~750 tokens perdus par tentative
**Fichier**: `niches.py`, `keepa_product_finder.py`

**Cause**:
1. Pre-check `@require_tokens("surprise_me")` estime mal le cout reel
2. Pas de budget cap pendant l'execution
3. Timeout n'annule pas requetes en cours

### CRITICAL-02: Estimation de Cout Incorrecte

**Impact**: Pre-check approve meme si budget insuffisant
**Fichier**: `require_tokens.py`, `keepa_service.py`

**Cause**:
- `can_perform_action("surprise_me")` utilise `TOKEN_COSTS` statique
- Cout reel depend du nombre de categories et ASINs (dynamique)

### HIGH-01: Pas de Cancellation Propre

**Impact**: Impossible d'interrompre proprement
**Fichier**: `niche_templates.py`

**Cause**:
- Pas de `asyncio.shield()` ni gestion `CancelledError`
- Sous-taches continuent meme apres timeout parent

### HIGH-02: Pas de Circuit Breaker par Endpoint

**Impact**: Un endpoint peut drainer tout le budget
**Fichier**: `keepa_service.py`

**Cause**:
- Circuit breaker global, pas par-action
- Pas de limite de depense par requete

---

## 3. Solutions Proposees (TDD Approach)

### Solution A: Budget Cap Pre-Execution (Recommandee)

**Principe**: Calculer le cout MAXIMAL avant execution, bloquer si insuffisant.

#### Etape A.1: Ajouter calcul cout dynamique

**Test First** (`tests/test_niche_budget.py`):
```python
@pytest.mark.asyncio
async def test_estimate_niche_discovery_cost():
    """Cost estimation should account for all Keepa calls."""
    # 3 niches = 3 bestsellers (150 tokens) + 3 filterings (~600 tokens)
    estimated = await estimate_niche_discovery_cost(count=3, max_asins_per_niche=200)

    assert estimated >= 600  # Minimum realiste
    assert estimated <= 1500  # Cap maximum
```

**Implementation** (`keepa_product_finder.py`):
```python
async def estimate_discovery_cost(
    count: int,
    max_asins_per_niche: int = 200
) -> int:
    """
    Estimate MAXIMUM token cost for niche discovery.

    Formula:
    - bestsellers: 50 tokens x count
    - filtering: 1 token x max_asins x count

    Returns conservative (high) estimate.
    """
    bestsellers_cost = 50 * count
    filtering_cost = max_asins_per_niche * count
    return bestsellers_cost + filtering_cost
```

#### Etape A.2: Budget Guard Dynamique

**Test First** (`tests/test_niche_budget.py`):
```python
@pytest.mark.asyncio
async def test_discover_rejects_if_budget_insufficient():
    """Discovery should fail fast if budget too low."""
    mock_keepa = AsyncMock()
    mock_keepa.check_api_balance.return_value = 100  # Only 100 tokens

    with pytest.raises(HTTPException) as exc:
        await discover_niches_auto(count=3, keepa=mock_keepa)

    assert exc.value.status_code == 429
    assert "estimated cost" in exc.value.detail.lower()
```

**Implementation** (`niches.py`):
```python
@router.get("/discover")
async def discover_niches_auto(
    count: int = Query(3, ge=1, le=5),
    keepa: KeepaService = Depends(get_keepa_service)
):
    # STEP 1: Estimate cost BEFORE any Keepa call
    estimated_cost = await estimate_discovery_cost(count)
    current_balance = await keepa.check_api_balance()

    if current_balance < estimated_cost:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Insufficient tokens for {count} niches",
                "estimated_cost": estimated_cost,
                "current_balance": current_balance,
                "deficit": estimated_cost - current_balance,
                "suggestion": f"Try count=1 (estimated: {estimated_cost // count} tokens)"
            }
        )

    # STEP 2: Proceed with budget-capped execution
    ...
```

### Solution B: Incremental Discovery avec Early Stop

**Principe**: Decouper en etapes, verifier budget apres chaque etape.

#### Etape B.1: Discovery par batch avec checkpoint

**Test First**:
```python
@pytest.mark.asyncio
async def test_discovery_stops_when_budget_depleted():
    """Should stop discovering niches when tokens run low."""
    mock_keepa = AsyncMock()
    mock_keepa.check_api_balance.side_effect = [500, 200, 50]  # Decreasing

    niches = await discover_with_budget_check(count=3, keepa=mock_keepa)

    # Should have stopped after 2 niches (50 tokens insufficient for 3rd)
    assert len(niches) == 2
```

**Implementation** (`niche_templates.py`):
```python
async def _discover_curated_niches_impl(...):
    validated = []
    MIN_TOKENS_PER_NICHE = 200  # Conservative buffer

    for tmpl in templates:
        # Check balance before each niche
        balance = await product_finder.keepa_service.check_api_balance()

        if balance < MIN_TOKENS_PER_NICHE:
            logger.warning(f"Budget low ({balance} tokens), stopping at {len(validated)} niches")
            break

        # Discover this niche
        try:
            products = await product_finder.discover_with_scoring(...)
            # ... validation logic
        except InsufficientTokensError:
            logger.warning("Tokens depleted mid-discovery")
            break

    return validated
```

### Solution C: Reduce Token Consumption (Optimisation)

**Principe**: Reduire le cout par niche en limitant le filtrage.

**Optimisations**:
1. Limiter ASINs filtres: 500 -> 50 par categorie
2. Utiliser cache agressif (TTL 1h au lieu de 24h)
3. Skip filtering si bestsellers list < 50 items

---

## 4. Plan d'Implementation (Sequence)

### Phase 6.1: Budget Guard (Jour 1)

| Tache | Fichier | Effort |
|-------|---------|--------|
| Test `test_estimate_niche_discovery_cost` | `tests/test_niche_budget.py` | 15min |
| Impl `estimate_discovery_cost()` | `keepa_product_finder.py` | 30min |
| Test `test_discover_rejects_if_budget_insufficient` | `tests/test_niche_budget.py` | 15min |
| Impl budget check in endpoint | `niches.py` | 30min |
| Validation locale | - | 15min |

**Total**: ~2h

### Phase 6.2: Incremental Discovery (Jour 1-2)

| Tache | Fichier | Effort |
|-------|---------|--------|
| Test `test_discovery_stops_when_budget_depleted` | `tests/test_niche_templates.py` | 15min |
| Impl budget checkpoint loop | `niche_templates.py` | 45min |
| Test early stop behavior | - | 15min |

**Total**: ~1h15

### Phase 6.3: Optimisation Consommation (Jour 2)

| Tache | Fichier | Effort |
|-------|---------|--------|
| Reduce max_asins 500 -> 50 | `keepa_product_finder.py:175` | 10min |
| Add balance logging after each Keepa call | `keepa_product_finder.py` | 20min |
| Test full flow with real Keepa (1 niche) | E2E | 30min |

**Total**: ~1h

---

## 5. Tests de Validation

### 5.1 Tests Unitaires (TDD)

```bash
# Nouveau fichier tests
cd backend
pytest tests/test_niche_budget.py -v
```

**Tests a creer**:
- `test_estimate_niche_discovery_cost` - Estimation correcte
- `test_discover_rejects_if_budget_insufficient` - Reject avec 429
- `test_discovery_stops_when_budget_depleted` - Early stop
- `test_budget_response_includes_suggestion` - Message actionable

### 5.2 Tests E2E

```bash
cd backend/tests/e2e
npx playwright test tests/03-niche-discovery.spec.js --workers=1
```

**Scenarios**:
1. Tokens suffisants -> Niches decouvertes
2. Tokens insuffisants -> HTTP 429 avec estimation
3. Tokens partiels -> 1-2 niches (pas 3)

### 5.3 Test Manuel Production

```bash
# Verifier avec tokens limites (~100)
curl -X GET "https://arbitragevault-backend-v2.onrender.com/api/v1/niches/discover?count=1" \
  -H "Accept: application/json" | jq

# Expected:
# - HTTP 200 avec 1 niche si balance > 200
# - HTTP 429 avec estimation si balance < 200
```

---

## 6. Criteres de Succes

| Metrique | Avant | Apres |
|----------|-------|-------|
| Tokens perdus sur timeout | ~750 | 0 |
| Reponse utilisateur | "Rien ne s'affiche" | Message clair avec deficit |
| E2E test success rate | ~85% | 95%+ |
| Temps decouverte 1 niche | 30s+ timeout | <15s |
| Predictabilite cout | Inconnue | Affichee avant execution |

---

## 7. Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Estimation trop haute | False rejects | Calibrer avec donnees reelles |
| Breaking change API | Frontend crash | Garder meme response structure |
| Cache invalide | Resultats stales | TTL raisonnable (1h) |

---

## 8. Prochaines Etapes (Apres Validation)

1. **User validates plan** - Attendre confirmation Aziz
2. **Implement Phase 6.1** - Budget Guard (priorite)
3. **Test locally** - pytest + manual curl
4. **Deploy to Render** - git push + auto-deploy
5. **E2E validation** - Playwright suite
6. **Document results** - Update PHASE6_VALIDATION_REPORT.md

---

## Annexe A: Call Stack Complet

```
GET /api/v1/niches/discover?count=3&shuffle=true
    |
    +-> niches.py:30 @require_tokens("surprise_me")
    |       -> guards/require_tokens.py:40 can_perform_action()
    |       -> Estime cout: ~200 tokens (SOUS-ESTIME)
    |
    +-> niches.py:92 asyncio.wait_for(discover_curated_niches(), 30s)
            |
            +-> niche_templates.py:242 _discover_curated_niches_impl()
                    |
                    +-> LOOP: pour chaque template (3x)
                            |
                            +-> keepa_product_finder.py:285 discover_with_scoring()
                                    |
                                    +-> 408: discover_products()
                                    |       |
                                    |       +-> 103: _discover_via_bestsellers()
                                    |               -> Keepa API /bestsellers (50 tokens)
                                    |               |
                                    |               +-> 173: _filter_asins_by_criteria()
                                    |                       -> Keepa API /product (1 token x 500)
                                    |
                                    +-> 444: Keepa API /product pour scoring
```

---

## Annexe B: TOKEN_COSTS Registry Actuel

```python
# keepa_service.py - A mettre a jour
TOKEN_COSTS = {
    "single_lookup": 2,
    "batch_lookup": 2,     # par ASIN
    "bestsellers": 50,
    "deals": 5,            # per 150 deals
    "surprise_me": 200,    # SOUS-ESTIME (devrait etre ~600 minimum)
}
```

**Recommandation**: Changer `"surprise_me": 600` minimum ou utiliser estimation dynamique.

---

**Document Version**: 1.0
**Prochaine Action**: Validation utilisateur requise
**Effort Total Estime**: ~4h15

Co-Authored-By: Claude <noreply@anthropic.com>
