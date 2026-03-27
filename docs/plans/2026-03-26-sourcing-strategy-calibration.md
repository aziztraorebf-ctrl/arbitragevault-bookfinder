# Sourcing Strategy Calibration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recalibrer les seuils de sourcing d'ArbitrageVault pour refléter la réalité du marché 2026 : modèle 100% online, suppression du Prime Bump Buy Box, et activer le filtre compétition FBA qui existe dans le code mais n'est jamais utilisé.

**Architecture:** 3 changements principaux — (1) `business_rules.json` pour les seuils, (2) branchement du filtre `max_fba_sellers` dans le pipeline réel, (3) unification de `source_price_factor` qui a 3 valeurs différentes dans le codebase. Aucun nouveau endpoint, aucun nouveau modèle DB.

**Tech Stack:** Python/FastAPI backend, `business_rules.json` config, `autosourcing_service.py`, `autosourcing_scoring.py`, `keepa_product_finder.py`, Neon PostgreSQL (vérification prod).

---

## Contexte — Pourquoi ces changements

### Le problème Buy Box (novembre 2025)
Amazon a éliminé le "Prime Bump" — avant, FBA gagnait le Buy Box même 20-30% plus cher que FBM.
Données mesurées : 85% des Buy Box FBA en jan 2025 → 13% en jan 2026.
**Conséquence :** Les prix cibles basés sur l'avantage Prime sont surestimés. `source_price_factor` à 0.50 assume qu'on achète à 50% du prix de vente — mais sans prime bump, il faut être plus compétitif en prix.

### Le problème du modèle online vs thrift
Les guides "40 vendeurs max OK" s'appliquent aux revendeurs thrift qui sourcent à $1-2/livre.
Nous sourceons en ligne à $8-20/livre. Avec 10+ vendeurs FBA, le capital dort trop longtemps.

### Seuils BSR selon type de livre (recherche Perplexity Deep Research, mars 2026)
- **Livres généraux** : BSR max 75,000 (ventes 1-3/mois au-delà → holding 80-150 jours)
- **Textbooks** : BSR max 250,000 MAIS seulement si historique saisonnier Keepa confirme BSR < 50,000 en août-octobre. Le BSR textbook est trompeur hors-saison.

### Nouveau facteur : Condition > Prime pour le Buy Box
L'algorithme 2026 favorise désormais la condition "Very Good" comme signal principal.
Notre `condition_signal` STRONG/MODERATE/WEAK est parfaitement positionné — il faut juste l'élever de "boost confiance" à "filtre requis" pour les picks STABLE.

---

## Task 1 : Vérifier `source_price_factor` en production

**But :** Savoir si la DB prod utilise 0.35, 0.40 ou 0.50. Le code a 3 valeurs différentes.

**Files:**
- Read: `backend/scripts/seed_source_price_factor.py`
- Read: `backend/app/services/daily_review_service.py:236`

**Step 1 : Lire le seed script**
```bash
cat backend/scripts/seed_source_price_factor.py
```
Chercher la valeur seedée et si elle a été exécutée.

**Step 2 : Query Neon production**
```bash
cd backend
python3 -c "
import asyncio
from app.core.database import get_async_session
from sqlalchemy import text

async def check():
    async for session in get_async_session():
        result = await session.execute(
            text(\"SELECT key, value FROM business_config WHERE key = 'source_price_factor'\")
        )
        row = result.fetchone()
        print(f'source_price_factor in prod DB: {row}')

asyncio.run(check())
"
```
Expected : une ligne avec la valeur active.

**Step 3 : Documenter le résultat**
Noter la valeur trouvée — elle détermine le Task 2.

---

## Task 2 : Unifier `source_price_factor` à 0.40

**Contexte :** 3 valeurs actuelles dans le code :
- `autosourcing_service.py:541,669` → défaut `0.50`
- `daily_review_service.py:236` → défaut `0.35`
- `keepa_product_finder.py:1001` → `Decimal("0.4")`

La valeur correcte pour notre modèle online est **0.40** :
- 0.50 = trop optimiste (assume achat à 50% = marges fictives)
- 0.35 = trop agressif (sous-estime le coût source réel online)
- 0.40 = réaliste pour sourcing online à $8-20 avec vente $18-40

**Files:**
- Modify: `backend/config/business_rules.json`
- Modify: `backend/app/services/autosourcing_service.py:541,669`
- Modify: `backend/app/services/daily_review_service.py:236`

**Step 1 : Ajouter `source_price_factor` dans business_rules.json**

Dans `business_rules.json`, après la section `"meta"`, ajouter :
```json
"source_price_factor": 0.40,
"fba_fee_percentage": 0.22
```
Note : `fba_fee_percentage` remplace le `fees_estimate_pct: 22.0` déjà dans les stratégies — unification.

**Step 2 : Corriger le défaut dans autosourcing_service.py**

Ligne 541 et 669, changer :
```python
# AVANT
source_price_factor = business_config.get("source_price_factor", 0.50)

# APRÈS
source_price_factor = business_config.get("source_price_factor", 0.40)
```

**Step 3 : Corriger le défaut dans daily_review_service.py**
```python
# AVANT (ligne ~236)
source_price_factor = business_config.get("source_price_factor", 0.35)

# APRÈS
source_price_factor = business_config.get("source_price_factor", 0.40)
```

**Step 4 : Écrire test de régression**

Fichier : `backend/tests/unit/test_source_price_factor_unified.py`
```python
def test_source_price_factor_default_is_040():
    """source_price_factor doit être 0.40 partout - jamais 0.35 ou 0.50"""
    import ast, pathlib

    files_to_check = [
        "app/services/autosourcing_service.py",
        "app/services/daily_review_service.py",
    ]
    for fpath in files_to_check:
        content = pathlib.Path(fpath).read_text()
        assert "0.50)" not in content or "source_price_factor" not in content.split("0.50)")[0].split("\n")[-1], \
            f"Défaut 0.50 trouvé dans {fpath}"
        assert 'get("source_price_factor", 0.35)' not in content, \
            f"Défaut 0.35 trouvé dans {fpath}"
```

**Step 5 : Run test**
```bash
cd backend
pytest tests/unit/test_source_price_factor_unified.py -v
```
Expected : PASS

**Step 6 : Seeder la DB production**
```bash
cd backend
python3 scripts/seed_source_price_factor.py
```
Si le script n'accepte pas de paramètre, modifier temporairement la valeur à `0.40` avant d'exécuter.

**Step 7 : Commit**
```bash
git add backend/config/business_rules.json \
        backend/app/services/autosourcing_service.py \
        backend/app/services/daily_review_service.py \
        backend/tests/unit/test_source_price_factor_unified.py
git commit -m "fix: unify source_price_factor to 0.40 across all services"
```

---

## Task 3 : Recalibrer les seuils stratégiques dans business_rules.json

**But :** Aligner les seuils avec la réalité du marché online 2026 (recherche Perplexity Deep Research).

**Files:**
- Modify: `backend/config/business_rules.json`

**Step 1 : Écrire test de validation des nouveaux seuils**

Fichier : `backend/tests/unit/test_business_rules_calibration.py`
```python
import json, pathlib

def load_rules():
    path = pathlib.Path("config/business_rules.json")
    return json.loads(path.read_text())

def test_textbook_bsr_max_is_250k():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["max_bsr"] == 250000

def test_velocity_bsr_max_is_75k():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["max_bsr"] == 75000

def test_balanced_bsr_max_is_100k():
    rules = load_rules()
    assert rules["strategies"]["balanced"]["max_bsr"] == 100000

def test_textbook_roi_min_is_35():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["roi_min"] == 35.0

def test_velocity_roi_min_is_30():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["roi_min"] == 30.0

def test_textbook_min_profit_dollars():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["min_profit_dollars"] == 12.0

def test_velocity_min_profit_dollars():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["min_profit_dollars"] == 8.0

def test_textbook_max_fba_sellers():
    rules = load_rules()
    assert rules["strategies"]["textbook"]["max_fba_sellers"] == 8

def test_velocity_max_fba_sellers():
    rules = load_rules()
    assert rules["strategies"]["velocity"]["max_fba_sellers"] == 5
```

**Step 2 : Run test — vérifier qu'ils échouent (TDD)**
```bash
cd backend
pytest tests/unit/test_business_rules_calibration.py -v
```
Expected : FAIL (valeurs actuelles différentes)

**Step 3 : Mettre à jour business_rules.json**

Modifier la section `"strategies"` :

```json
"textbook": {
  "description": "Textbook arbitrage - high margin, seasonal, intrinsic value based",
  "roi_min": 35.0,
  "velocity_min": 20.0,
  "stability_min": 60.0,
  "min_sell_price": 30.0,
  "min_intrinsic_value": 35.0,
  "min_profit_dollars": 12.0,
  "max_bsr": 250000,
  "max_fba_sellers": 8,
  "seasonal_bsr_check": true,
  "seasonal_bsr_peak_max": 50000,
  "holding_period_days": [45, 90],
  "buy_price_source": "current_fba_price",
  "sell_price_source": "intrinsic_median",
  "use_intrinsic_value": true,
  "intrinsic_window_days": 365,
  "fees_estimate_pct": 22.0,
  "weights": {
    "roi": 0.6,
    "velocity": 0.2,
    "stability": 0.2
  },
  "enabled": true,
  "priority": 1,
  "development_focus": true
},
"velocity": {
  "description": "Fast rotation books - moderate margin, quick turnover, online sourcing",
  "roi_min": 30.0,
  "velocity_min": 60.0,
  "stability_min": 40.0,
  "min_sell_price": 18.0,
  "min_intrinsic_value": 20.0,
  "min_profit_dollars": 8.0,
  "max_bsr": 75000,
  "max_fba_sellers": 5,
  "seasonal_bsr_check": false,
  "holding_period_days": [7, 30],
  "buy_price_source": "current_fba_price",
  "sell_price_source": "intrinsic_median",
  "use_intrinsic_value": true,
  "intrinsic_window_days": 90,
  "fees_estimate_pct": 22.0,
  "weights": {
    "roi": 0.3,
    "velocity": 0.5,
    "stability": 0.2
  },
  "enabled": true,
  "priority": 2,
  "development_focus": false
},
"balanced": {
  "description": "Balanced approach - moderate everything, online sourcing",
  "roi_min": 30.0,
  "velocity_min": 40.0,
  "stability_min": 50.0,
  "min_sell_price": 20.0,
  "min_intrinsic_value": 22.0,
  "min_profit_dollars": 10.0,
  "max_bsr": 100000,
  "max_fba_sellers": 6,
  "seasonal_bsr_check": false,
  "holding_period_days": [14, 60],
  "buy_price_source": "current_fba_price",
  "sell_price_source": "intrinsic_median",
  "use_intrinsic_value": true,
  "intrinsic_window_days": 90,
  "fees_estimate_pct": 22.0,
  "weights": {
    "roi": 0.4,
    "velocity": 0.35,
    "stability": 0.25
  },
  "enabled": true,
  "priority": 3,
  "development_focus": false
}
```

**Step 4 : Run tests — vérifier qu'ils passent**
```bash
cd backend
pytest tests/unit/test_business_rules_calibration.py -v
```
Expected : PASS (tous les 9 tests)

**Step 5 : Commit**
```bash
git add backend/config/business_rules.json \
        backend/tests/unit/test_business_rules_calibration.py
git commit -m "fix: recalibrate sourcing thresholds for online model 2026 (BSR, ROI, profit floor, max sellers)"
```

---

## Task 4 : Activer le filtre `max_fba_sellers` dans le pipeline

**Contexte :** Le code `keepa_product_finder.py` accepte déjà `max_fba_sellers` mais dans `autosourcing_service.py:292`, un commentaire dit *"intentionally None at discovery stage"*. C'est correct pour la phase discovery (Keepa scan), mais le filtre doit s'appliquer **après** en scoring.

**Approche :** Ajouter le filtrage dans `autosourcing_service.py` dans la boucle de scoring, en lisant `max_fba_sellers` depuis la stratégie active dans `business_rules.json`.

**Files:**
- Modify: `backend/app/services/autosourcing_service.py`
- Modify: `backend/app/services/autosourcing_scoring.py`
- Test: `backend/tests/services/test_fba_seller_filter.py`

**Step 1 : Écrire les tests**

Fichier : `backend/tests/services/test_fba_seller_filter.py`
```python
import pytest
from unittest.mock import MagicMock
from app.services.autosourcing_scoring import should_reject_by_competition

def test_reject_when_fba_sellers_exceeds_max():
    result = should_reject_by_competition(
        fba_seller_count=10,
        max_fba_sellers=5
    )
    assert result is True

def test_accept_when_fba_sellers_within_max():
    result = should_reject_by_competition(
        fba_seller_count=4,
        max_fba_sellers=5
    )
    assert result is False

def test_accept_when_fba_count_is_none():
    """Si Keepa ne retourne pas le count, ne pas rejeter (data incomplète)"""
    result = should_reject_by_competition(
        fba_seller_count=None,
        max_fba_sellers=5
    )
    assert result is False

def test_accept_when_max_fba_sellers_is_none():
    """Si pas de max configuré, pas de filtre"""
    result = should_reject_by_competition(
        fba_seller_count=100,
        max_fba_sellers=None
    )
    assert result is False

def test_reject_at_exact_boundary():
    """max=5 : 5 vendeurs = OK, 6 = rejeté"""
    assert should_reject_by_competition(5, 5) is False
    assert should_reject_by_competition(6, 5) is True
```

**Step 2 : Run tests — vérifier qu'ils échouent**
```bash
cd backend
pytest tests/services/test_fba_seller_filter.py -v
```
Expected : FAIL avec `ImportError: cannot import name 'should_reject_by_competition'`

**Step 3 : Ajouter la fonction dans autosourcing_scoring.py**

À la fin de `backend/app/services/autosourcing_scoring.py`, ajouter :
```python
def should_reject_by_competition(
    fba_seller_count: int | None,
    max_fba_sellers: int | None,
) -> bool:
    """Retourne True si le produit doit être rejeté à cause de trop de vendeurs FBA.

    Règle : si fba_seller_count > max_fba_sellers -> rejeter.
    Si l'un ou l'autre est None -> ne pas rejeter (données incomplètes ou pas de max configuré).
    """
    if fba_seller_count is None or max_fba_sellers is None:
        return False
    return fba_seller_count > max_fba_sellers
```

**Step 4 : Run tests — vérifier qu'ils passent**
```bash
cd backend
pytest tests/services/test_fba_seller_filter.py -v
```
Expected : PASS (5/5)

**Step 5 : Intégrer dans autosourcing_service.py**

Dans `autosourcing_service.py`, dans la méthode de scoring (autour de la ligne 530 et 660), après avoir récupéré `fba_seller_count`, ajouter le filtre :

Chercher le pattern suivant (présent ~ligne 532 et ~660) :
```python
fba_seller_count = product_data.get("fba_seller_count")
```

Après cette ligne, dans les deux occurrences, ajouter :
```python
# Filtre compétition FBA — lu depuis la stratégie active
strategy_config = business_config.get("strategies", {}).get(
    business_config.get("active_strategy", "balanced"), {}
)
max_fba_sellers = strategy_config.get("max_fba_sellers", None)

from app.services.autosourcing_scoring import should_reject_by_competition
if should_reject_by_competition(fba_seller_count, max_fba_sellers):
    logger.info(
        "Skipping ASIN: too many FBA sellers",
        extra={
            "asin": asin,
            "fba_seller_count": fba_seller_count,
            "max_fba_sellers": max_fba_sellers,
        },
    )
    continue
```

Note : l'import `should_reject_by_competition` doit être déplacé en haut du fichier avec les autres imports.

**Step 6 : Run les tests existants pour vérifier pas de régression**
```bash
cd backend
pytest tests/services/ -v --tb=short -x
```
Expected : tous les tests services passent

**Step 7 : Commit**
```bash
git add backend/app/services/autosourcing_scoring.py \
        backend/app/services/autosourcing_service.py \
        backend/tests/services/test_fba_seller_filter.py
git commit -m "feat: activate FBA seller count filter in scoring pipeline"
```

---

## Task 5 : Appliquer filtre profit absolu minimum

**Contexte :** Des filtres de profit existent dans `classify_product_tier()` ($5-$15) mais aucun filtre global en amont dans le pipeline scoring. Un livre à ROI 35% mais prix de $12 donne ~$1.50 de profit net — non viable pour notre modèle.

**Files:**
- Modify: `backend/app/services/autosourcing_scoring.py`
- Test: `backend/tests/services/test_profit_floor_filter.py`

**Step 1 : Écrire les tests**

Fichier : `backend/tests/services/test_profit_floor_filter.py`
```python
from app.services.autosourcing_scoring import should_reject_by_profit_floor

def test_reject_when_profit_below_floor():
    assert should_reject_by_profit_floor(profit_net=5.0, min_profit_dollars=8.0) is True

def test_accept_when_profit_above_floor():
    assert should_reject_by_profit_floor(profit_net=10.0, min_profit_dollars=8.0) is False

def test_accept_at_exact_floor():
    assert should_reject_by_profit_floor(profit_net=8.0, min_profit_dollars=8.0) is False

def test_accept_when_no_floor_configured():
    assert should_reject_by_profit_floor(profit_net=1.0, min_profit_dollars=None) is False

def test_accept_when_profit_is_none():
    """Données incomplètes -> ne pas rejeter"""
    assert should_reject_by_profit_floor(profit_net=None, min_profit_dollars=8.0) is False
```

**Step 2 : Run — vérifier échec**
```bash
pytest tests/services/test_profit_floor_filter.py -v
```
Expected : FAIL

**Step 3 : Ajouter la fonction dans autosourcing_scoring.py**
```python
def should_reject_by_profit_floor(
    profit_net: float | None,
    min_profit_dollars: float | None,
) -> bool:
    """Retourne True si le profit net est inférieur au minimum absolu configuré.

    Règle : si profit_net < min_profit_dollars -> rejeter.
    Si l'un ou l'autre est None -> ne pas rejeter.
    """
    if profit_net is None or min_profit_dollars is None:
        return False
    return profit_net < min_profit_dollars
```

**Step 4 : Run — vérifier succès**
```bash
pytest tests/services/test_profit_floor_filter.py -v
```
Expected : PASS (5/5)

**Step 5 : Intégrer dans autosourcing_service.py**

Après le filtre FBA sellers (ajouté en Task 4), ajouter :
```python
# Filtre profit absolu minimum
min_profit_dollars = strategy_config.get("min_profit_dollars", None)
from app.services.autosourcing_scoring import should_reject_by_profit_floor
if should_reject_by_profit_floor(profit_net, min_profit_dollars):
    logger.info(
        "Skipping ASIN: profit below minimum floor",
        extra={
            "asin": asin,
            "profit_net": profit_net,
            "min_profit_dollars": min_profit_dollars,
        },
    )
    continue
```

Note : `profit_net` est calculé par `calculate_product_roi()` quelques lignes plus haut. Vérifier que la variable est accessible à ce point.

**Step 6 : Run suite complète**
```bash
cd backend
pytest tests/ -v --tb=short -x -q
```
Expected : tous les tests passent

**Step 7 : Commit**
```bash
git add backend/app/services/autosourcing_scoring.py \
        backend/app/services/autosourcing_service.py \
        backend/tests/services/test_profit_floor_filter.py
git commit -m "feat: add profit floor filter per strategy (min_profit_dollars)"
```

---

## Task 6 : Élever condition_signal STRONG comme filtre pour picks STABLE

**Contexte :** Depuis novembre 2025, Amazon favorise "Very Good" condition pour le Buy Box.
Notre `condition_signal` STRONG = peu de vendeurs occasion de qualité = opportunité réelle.
Actuellement c'est juste un boost de confiance +10. Il faut en faire un signal prioritaire.

**Approche :** Dans `daily_review_service.py`, les picks STABLE avec `condition_signal = WEAK` et ROI < seuil devraient être déclassés en WATCH plutôt qu'acceptés comme achat recommandé.

**Files:**
- Read: `backend/app/services/daily_review_service.py` (chercher la logique STABLE classification)
- Modify: `backend/config/business_rules.json`
- Modify: `backend/app/services/daily_review_service.py`
- Test: `backend/tests/services/test_condition_signal_filter.py`

**Step 1 : Lire la logique actuelle STABLE**
```bash
grep -n "STABLE\|condition_signal\|WEAK\|WATCH" backend/app/services/daily_review_service.py | head -30
```

**Step 2 : Activer `reject_weak` dans business_rules.json**

Dans `condition_signals`, changer :
```json
"condition_signals": {
  "strong_roi_min": 25.0,
  "moderate_roi_min": 10.0,
  "max_used_offers_strong": 10,
  "max_used_offers_moderate": 25,
  "confidence_boost_strong": 10,
  "confidence_boost_moderate": 5,
  "reject_weak": true,
  "reject_weak_roi_threshold": 20.0
}
```

Note : `reject_weak_roi_threshold: 20.0` = si condition WEAK ET ROI < 20% → ne pas classer STABLE.

**Step 3 : Écrire test**

Fichier : `backend/tests/services/test_condition_signal_filter.py`
```python
def test_weak_condition_low_roi_not_stable():
    """Un pick WEAK condition + ROI < 20% ne doit pas être STABLE"""
    from app.services.daily_review_service import _classify_pick_status
    # Mock pick avec condition WEAK et ROI faible
    pick = MagicMock()
    pick.condition_signal = "WEAK"
    pick.roi_percentage = 15.0
    pick.sighting_count = 3
    pick.bsr = 50000

    result = _classify_pick_status(pick, config={"reject_weak": True, "reject_weak_roi_threshold": 20.0})
    assert result != "STABLE"

def test_strong_condition_is_stable():
    """Un pick STRONG condition + ROI correct doit être STABLE"""
    # ... adapter selon signature réelle de _classify_pick_status
```

Note : adapter ce test selon la signature réelle de la fonction après l'avoir lue au Step 1.

**Step 4 : Implémenter la vérification dans daily_review_service.py**

Après avoir lu la logique au Step 1, ajouter dans la condition STABLE :
```python
# Vérification condition_signal si reject_weak est activé
condition_cfg = business_config.get("condition_signals", {})
if condition_cfg.get("reject_weak", False):
    reject_threshold = condition_cfg.get("reject_weak_roi_threshold", 20.0)
    if (pick.condition_signal == "WEAK" and
            (pick.roi_percentage or 0) < reject_threshold):
        classification = "WATCH"  # Déclasser de STABLE à WATCH
        action = "Surveiller — condition faible"
```

**Step 5 : Run tests**
```bash
pytest tests/services/test_condition_signal_filter.py -v
pytest tests/services/ -v --tb=short -q
```

**Step 6 : Commit**
```bash
git add backend/config/business_rules.json \
        backend/app/services/daily_review_service.py \
        backend/tests/services/test_condition_signal_filter.py
git commit -m "feat: elevate condition_signal WEAK as disqualifier for STABLE picks (post-prime-bump)"
```

---

## Task 7 : Validation en production

**But :** Vérifier que les changements donnent des résultats cohérents en prod.

**Step 1 : Vérifier source_price_factor actif en DB**
```bash
cd backend
python3 -c "
import asyncio
from app.core.database import get_async_session
from sqlalchemy import text
async def check():
    async for session in get_async_session():
        r = await session.execute(text(\"SELECT key, value FROM business_config WHERE key = 'source_price_factor'\"))
        print(r.fetchone())
asyncio.run(check())
"
```
Expected : `('source_price_factor', '0.40')`

**Step 2 : Run suite de tests complète**
```bash
cd backend
pytest tests/ -v --tb=short -q
```
Expected : tous les tests passent (769+ existants + nouveaux)

**Step 3 : Push branche et créer PR**
```bash
git push origin fix/sourcing-strategy-calibration
```
Créer PR sur GitHub avec titre : `fix: calibrate sourcing strategy for online model 2026`

**Step 4 : Deploy et smoke test CoWork**

Après merge, tester les endpoints CoWork en production :
```bash
# Remplacer TOKEN par le CoWork bearer token
curl -H "Authorization: Bearer TOKEN" \
  https://arbitragevault-backend-v2.onrender.com/api/v1/cowork/dashboard-summary

curl -H "Authorization: Bearer TOKEN" \
  https://arbitragevault-backend-v2.onrender.com/api/v1/cowork/daily-buy-list
```

Vérifier dans la réponse `daily-buy-list` :
- `fba_seller_count <= 8` sur tous les picks
- `profit_net >= 8.0` sur tous les picks
- `bsr <= 250000` (textbook) ou `<= 75000` (velocity)
- `condition_signal` présent (STRONG/MODERATE/WEAK/UNKNOWN)

**Step 5 : Mettre à jour AGENT_CONTEXT.md**

Fichier : `docs/AGENT_CONTEXT.md`

Ajouter section :
```markdown
## Stratégies de sourcing (calibrées mars 2026)

| Stratégie | BSR max | ROI min | Profit min | Max vendeurs FBA |
|-----------|---------|---------|------------|-----------------|
| textbook  | 250,000 | 35%     | $12        | 8               |
| velocity  | 75,000  | 30%     | $8         | 5               |
| balanced  | 100,000 | 30%     | $10        | 6               |

**Note Buy Box 2026 :** Le Prime Bump FBA a été éliminé (nov 2025).
Prix cible = intrinsic_median (médiane historique Keepa).
Condition signal STRONG = priorité pour le Buy Box actuel.
```

**Step 6 : Commit final**
```bash
git add docs/AGENT_CONTEXT.md
git commit -m "docs: update AGENT_CONTEXT with 2026 calibrated sourcing strategy"
```

---

## Résumé des changements

| Fichier | Type | Changement |
|---------|------|------------|
| `config/business_rules.json` | Config | BSR, ROI, profit floor, max_fba_sellers par stratégie |
| `config/business_rules.json` | Config | source_price_factor unifié à 0.40 |
| `config/business_rules.json` | Config | reject_weak activé avec threshold 20% |
| `autosourcing_service.py` | Fix | Défaut source_price_factor 0.50 → 0.40 |
| `daily_review_service.py` | Fix | Défaut source_price_factor 0.35 → 0.40 |
| `autosourcing_scoring.py` | Feat | `should_reject_by_competition()` |
| `autosourcing_scoring.py` | Feat | `should_reject_by_profit_floor()` |
| `autosourcing_service.py` | Feat | Filtres FBA + profit floor activés dans pipeline |
| `daily_review_service.py` | Feat | condition_signal WEAK déclasse STABLE → WATCH |
| `docs/AGENT_CONTEXT.md` | Docs | Stratégies calibrées documentées pour CoWork |

**Tests ajoutés :** 19+ nouveaux tests unitaires et services.

**Branche :** `fix/sourcing-strategy-calibration`
