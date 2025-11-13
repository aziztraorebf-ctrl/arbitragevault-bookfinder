# Phase 4 Day 1 - Critical Throttle Gap Discovered

**Date**: 31 Octobre 2025
**Statut**: 🔴 CRITIQUE - Tokens Keepa négatifs (-31)
**Impact**: Tests bloqués jusqu'à recharge tokens (Nov 3, 2025)

---

## 🚨 Incident : Tokens Keepa Négatifs

### État Actuel
```
Private API access key: rvd01p0nku3s8bsnbubeda6je1763vv5gc94jmg4eiakghlnv4bm3pmvd0sg7ru
Currently available tokens: -31
Current token flow reduction: 0 (0.0000)
```

**Balance négative** : -31 tokens
**Prochaine recharge** : Nov 3, 2025 at 14:38
**Tokens/minute** : 20 (plan actuel)

---

## 🔍 Root Cause Analysis

### Ce Qui A Causé Le Problème

**Tests consommateurs exécutés** :
1. `test_bestsellers_debug.py` → **50 tokens** (1 appel /bestsellers)
2. `/api/v1/products/discover` avec filtres → **~100 tokens** (batch de 100 ASINs)
3. Tests BSR multiples → **~100+ tokens** (requêtes /product répétées)

**Total estimé consommé** : ~250-300 tokens
**Balance initiale estimée** : ~220 tokens
**Résultat** : Balance négative de -31 tokens

---

## ⚠️ Faille Critique Identifiée

### Throttle Implémenté MAIS Incomplet

**Code existant** : `backend/app/services/keepa_throttle.py`
- ✅ **Token Bucket Algorithm** : Limite 20 requêtes/minute (RYTHME)
- ✅ **Throttle utilisé** : `await self.throttle.acquire(cost=1)` ligne 203
- ✅ **Warnings implémentés** : Logs quand tokens locaux < 50

**MAIS Faille critique** :
- ❌ **Ne vérifie PAS le budget total API** (`tokensLeft` Keepa)
- ❌ **Lit `tokensLeft` APRÈS la requête** (trop tard!)
- ❌ **Pas de blocage si balance Keepa < seuil critique**

### Différence Rythme vs Budget

| Concept | Définition | Notre Implémentation |
|---------|-----------|---------------------|
| **Rythme** | Requêtes par minute (20/min) | ✅ Protégé par `KeepaThrottle` |
| **Budget** | Tokens totaux restants API | ❌ **NON PROTÉGÉ** |

**Exemple problème** :
```python
# Throttle local dit OK (on respecte 20/min)
await self.throttle.acquire(cost=1)  # ✅ Acquiert token local

# Mais API Keepa dit NON (budget épuisé)
response = await self.client.get(...)  # ❌ -31 tokens!

# On découvre APRÈS coup
tokens_left = response.headers.get('tokens-left')  # Trop tard!
```

---

## 📊 Détails Techniques

### Code Actuel (Ligne 199-270 keepa_service.py)

```python
async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    # ✅ Vérifie throttle LOCAL (rythme)
    await self.throttle.acquire(cost=1)

    # ❌ NE vérifie PAS budget API tokensLeft

    # Fait la requête (peut dépasser budget!)
    response = await self.client.get(url, params=params_with_key)

    # Lit tokensLeft APRÈS (trop tard)
    tokens_left = response.headers.get('tokens-left')
    if tokens_left:
        self.metrics.add_usage(1, int(tokens_left))
```

### Ce Qui Aurait Dû Être Fait

```python
async def _make_request(self, endpoint: str, params: Dict[str, Any], estimated_cost: int = 1):
    # ✅ Vérifie throttle local (rythme)
    await self.throttle.acquire(cost=1)

    # ✅ NOUVEAU : Vérifie budget API AVANT requête
    api_balance = await self.check_api_balance()
    if api_balance < 10:  # Seuil critique
        raise InsufficientTokensError(
            f"Keepa API tokens too low: {api_balance} < 10 (required: {estimated_cost})"
        )

    # ✅ NOUVEAU : Warn si requête coûteuse
    if estimated_cost > 10 and api_balance < estimated_cost * 2:
        logger.warning(
            f"High-cost request ({estimated_cost} tokens) with low balance ({api_balance})"
        )

    # Maintenant on peut faire la requête en sécurité
    response = await self.client.get(url, params=params_with_key)
```

---

## 🎯 Endpoints Coûteux Identifiés

| Endpoint | Coût Tokens | Utilisé Par | Protégé? |
|----------|-------------|-------------|----------|
| `/product` | 1 par ASIN | analyze_product() | ❌ Non |
| `/product` (batch 100) | 100 tokens | discover filtering | ❌ Non |
| `/bestsellers` | **50 tokens** | discover_products() | ❌ Non |
| `/deals` | 5 par 150 | discover_products() | ❌ Non |

**Requêtes les plus dangereuses** :
- `discover_products()` avec filtres BSR/prix → Peut consommer **500+ tokens** (5 batches de 100)
- `test_bestsellers_debug.py` → **50 tokens** en un coup

---

## ✅ Solutions À Implémenter (Prochaine Session)

### 1. Vérification Budget AVANT Requête
**Fichier** : `backend/app/services/keepa_service.py`

```python
async def _ensure_sufficient_balance(self, estimated_cost: int):
    """
    Vérifie que le budget API est suffisant AVANT la requête.
    Raise InsufficientTokensError si balance trop basse.
    """
    balance = await self.check_api_balance()

    CRITICAL_THRESHOLD = 10
    SAFE_MARGIN = 2  # 2x le coût pour sécurité

    if balance < CRITICAL_THRESHOLD:
        raise InsufficientTokensError(
            f"Keepa tokens critically low: {balance} (threshold: {CRITICAL_THRESHOLD})"
        )

    if balance < estimated_cost * SAFE_MARGIN:
        logger.warning(
            f"⚠️ Low token balance for request: {balance} tokens "
            f"(cost: {estimated_cost}, recommended: {estimated_cost * SAFE_MARGIN})"
        )
```

### 2. Coût Estimé Par Endpoint

```python
ENDPOINT_COSTS = {
    "/product": 1,  # 1 token par ASIN
    "/bestsellers": 50,
    "/deals": 5,  # 5 tokens per 150 deals
    "/category": 1,
    "/seller": 1
}

async def _make_request(self, endpoint: str, params: Dict[str, Any]):
    # Estimer le coût
    cost = ENDPOINT_COSTS.get(endpoint, 1)

    # Si batch de produits, multiplier
    if endpoint == "/product" and "asin" in params:
        asin_count = len(params["asin"].split(","))
        cost = asin_count

    # Vérifier budget AVANT
    await self._ensure_sufficient_balance(cost)

    # Puis throttle rythme
    await self.throttle.acquire(cost=1)

    # Puis faire requête
    response = await self.client.get(...)
```

### 3. Exception Personnalisée

```python
class InsufficientTokensError(Exception):
    """Raised when Keepa API token balance is too low."""
    pass
```

### 4. Middleware Protection Endpoints

```python
# Dans products.py, niches.py, etc.
async def discover_products(...):
    # Check balance AVANT de commencer
    keepa_service = KeepaService(...)
    balance = await keepa_service.check_api_balance()

    if balance < 100:  # Estimation conservative
        raise HTTPException(
            status_code=503,
            detail=f"Keepa API tokens insufficient: {balance} (required: ~100)"
        )

    # Procéder avec découverte
    ...
```

---

## 📋 Action Items Phase 4.5

### Priorité CRITIQUE (Avant Tests)
1. ✅ Implémenter `_ensure_sufficient_balance()` dans `keepa_service.py`
2. ✅ Ajouter `InsufficientTokensError` exception
3. ✅ Mapper coûts endpoints dans `ENDPOINT_COSTS`
4. ✅ Ajouter check balance dans tous endpoints discovery

### Priorité HAUTE (Protection)
5. ⏳ Ajouter middleware FastAPI pour check global tokens
6. ⏳ Logger balance API dans health endpoint
7. ⏳ Alertes Sentry si balance < 50 tokens
8. ⏳ Tests unitaires pour protection tokens

### Priorité MOYENNE (Monitoring)
9. ⏳ Dashboard tokens restants dans frontend
10. ⏳ Notifications email si balance < 20 tokens
11. ⏳ Métriques Prometheus pour token usage

---

## 🧪 Tests À Éviter (Jusqu'à Recharge)

**INTERDIT jusqu'au Nov 3, 2025** :
- ❌ Tests `/bestsellers` endpoint (50 tokens chacun)
- ❌ Tests `/products/discover` avec filtres (100+ tokens)
- ❌ Tests batch `/product` > 10 ASINs
- ❌ Scripts debug avec vraies API calls

**PERMIS (cache ou mocks)** :
- ✅ Tests unitaires avec mocks
- ✅ Tests cache PostgreSQL
- ✅ Tests parsing avec données JSON statiques
- ✅ Validation frontend (sans backend calls)

---

## 📚 Références

- **Keepa API Pricing** : https://keepa.com/#!api (20 tokens/min, refill quotidien)
- **Phase 3 Day 10** : Throttle implémenté (rythme seulement)
- **Token Bucket Algorithm** : https://en.wikipedia.org/wiki/Token_bucket

---

## 🎓 Leçons Apprises

1. **Throttle != Budget Protection**
   - Throttle contrôle le RYTHME (requêtes/min)
   - Budget contrôle les TOKENS TOTAUX (balance API)
   - Les deux sont nécessaires!

2. **Vérifier AVANT, Pas APRÈS**
   - Lire `tokensLeft` dans réponse = trop tard
   - Check balance AVANT requête coûteuse

3. **Coûts Variables Par Endpoint**
   - `/bestsellers` = 50 tokens (très cher!)
   - `/product` batch = N tokens (variable)
   - Besoin de mapping coûts

4. **Tests E2E vs Budget**
   - Tests avec vraies APIs consomment budget
   - Utiliser cache + mocks pour CI/CD
   - Réserver tokens pour production

---

**Statut** : 🔴 BLOQUÉ jusqu'à recharge tokens
**Prochaine session** : Implémenter protection budget AVANT tout test
**ETA Fix** : Phase 4.5 (après recharge tokens Nov 3)

---

*Rapport généré le 31/10/2025 - Phase 4 Day 1 Throttle Gap*
