# 🎯 PLAN D'UNIFICATION COMPLÈTE - Analyse Manuelle + Mes Niches + AutoSourcing

**Objectif :** Consolider les 3 endpoints pour utiliser UNE SEULE source de vérité pour le parsing Keepa et les calculs.

**Validation :** MCP Keepa à chaque phase pour garantir la bonne voie.

---

## 📋 État Actuel (PHASE 0)

### Endpoints Actuels
```
1. Analyse Manuelle (/api/v1/keepa/ingest)
   └─ keepa.py
   └─ Utilise: parse_keepa_product() ✅

2. Mes Niches (/api/v1/views/mes_niches)
   └─ views.py
   └─ Utilise: build_unified_product() ❌ (mauvaise logique)

3. AutoSourcing (/api/v1/views/autosourcing)
   └─ views.py
   └─ Utilise: build_unified_product() ❌ (même mauvaise logique)
```

### Problème
- Analyse Manuelle = Correct ($7.69) ✅
- Mes Niches/AutoSourcing = Faux ($16.90) ❌
- Raison = Logique de parsing différente

### Solution
- Créer UNE SEULE fonction de parsing
- Tous les 3 endpoints l'utilisent
- Valider avec MCP Keepa à chaque étape

---

## 🚀 PHASE 1: Unifier le Parser Keepa

### Objectif
Créer une fonction `parse_keepa_product_unified()` qui extrait TOUTES les données correctement :
- Prices (Amazon, New, Used, FBA)
- BSR (Sales Rank)
- Offers détaillés (condition, prix, FBA, etc.)
- Velocity/History

### Fichiers à Modifier
- `backend/app/services/keepa_parser_v2.py` → Améliorer `parse_keepa_product()`

### Code à Créer

```python
def parse_keepa_product_unified(raw_keepa: Dict[str, Any]) -> Dict[str, Any]:
    """
    UNIFIED parser - Utilisé par TOUS les endpoints.

    Extrait:
    - Prices (stats.current)
    - BSR (stats.current[3])
    - Offers détaillés (offers[])
    - History (csv[])
    - Conditions (condition field in offers)

    Returns: Dict avec ALL data structurée
    """
    asin = raw_keepa.get('asin', 'unknown')
    parsed = {}

    # 1. Extract current prices from stats.current
    stats = raw_keepa.get('stats', {})
    current_array = stats.get('current', [])

    if current_array and len(current_array) > 10:
        parsed['current_amazon_price'] = current_array[0]
        parsed['current_new_price'] = current_array[1]
        parsed['current_used_price'] = current_array[2]
        parsed['current_bsr'] = current_array[3]
        parsed['current_fba_price'] = current_array[10]

    # 2. Extract offers with conditions
    offers = raw_keepa.get('offers', [])
    offers_by_condition = group_offers_by_condition(offers)
    parsed['offers_by_condition'] = offers_by_condition

    # 3. Extract price history from csv
    csv = raw_keepa.get('csv', [])
    if len(csv) > 10:
        parsed['history_new'] = csv[1]  # NEW price history
        parsed['history_used'] = csv[2]  # USED price history
        parsed['history_fba'] = csv[10]  # FBA price history

    return parsed

def group_offers_by_condition(offers: List[Dict]) -> Dict[str, Any]:
    """
    Group offers by condition (NEW, VG, GOOD, ACCEPTABLE).
    Extract minimum price per condition.
    """
    conditions = {
        1: 'new',
        3: 'very_good',
        4: 'good',
        5: 'acceptable'
    }

    grouped = {}
    for condition_id, condition_name in conditions.items():
        offers_for_condition = [
            o for o in offers
            if o.get('condition') == condition_id
        ]

        if offers_for_condition:
            # Find minimum price
            min_offer = min(
                offers_for_condition,
                key=lambda x: x.get('offerCSV', [[999999]])[0][1]
            )

            grouped[condition_name] = {
                'condition_id': condition_id,
                'minimum_price': extract_price(min_offer),
                'seller_count': len(offers_for_condition),
                'fba_count': sum(1 for o in offers_for_condition if o.get('isFBA')),
                'sample_offer': {
                    'seller_id': min_offer.get('sellerId'),
                    'is_fba': min_offer.get('isFBA'),
                    'is_prime': min_offer.get('isPrime'),
                    'shipping': extract_shipping(min_offer)
                }
            }

    return grouped
```

### Tests avec MCP Keepa
```bash
# Test 1: Validate parse_keepa_product_unified()
asin = "0593655036"
response = mcp_keepa.get_product(asin, domain=1, days=7, offers=20)

# Verify:
✓ current_prices extracted correctly
✓ current_bsr = 66 (not -1)
✓ offers_by_condition['good']['minimum_price'] = 800 (not 1690)
✓ offers_by_condition['new']['minimum_price'] = 1698

# Expected output structure:
{
  'current_amazon_price': 1698,
  'current_new_price': 1400,
  'current_used_price': 971,
  'current_bsr': 66,
  'current_fba_price': 1888,
  'offers_by_condition': {
    'new': {'minimum_price': 1698, 'seller_count': 4, ...},
    'very_good': {'minimum_price': 1094, 'seller_count': 8, ...},
    'good': {'minimum_price': 800, 'seller_count': 12, ...},
    'acceptable': {'minimum_price': 994, 'seller_count': 25, ...}
  }
}
```

### Validation Criteria ✓
- [ ] parse_keepa_product_unified() retourne la structure complète
- [ ] current_bsr n'est jamais -1
- [ ] offers_by_condition['good']['minimum_price'] < offers_by_condition['new']['minimum_price']
- [ ] Tous les offres groupées correctement par condition

---

## 🎯 PHASE 2: Créer pricing_service_unified()

### Objectif
Consolider TOUS les calculs de pricing en UNE SEULE fonction :
- ROI calculation (par condition)
- Velocity scoring
- Max buy price
- Profitability analysis

### Fichiers à Modifier
- `backend/app/services/pricing_service.py` → Refactoriser complètement

### Code à Créer

```python
async def calculate_pricing_metrics_unified(
    parsed_data: Dict[str, Any],
    source_price: float,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    UNIFIED pricing calculation - Utilisé par TOUS les endpoints.

    Calcule:
    - ROI pour CHAQUE condition (new, very_good, good, acceptable)
    - Prix de vente recommandé
    - Velocity score
    - Max buy price (35% rule)
    """
    results = {}

    # Get offers by condition
    offers_by_condition = parsed_data.get('offers_by_condition', {})

    for condition_name, condition_data in offers_by_condition.items():
        market_price = condition_data.get('minimum_price', 0) / 100  # Convert from cents

        # Calculate ROI for this condition
        roi = calculate_roi(
            market_price=market_price,
            source_price=source_price,
            config=config
        )

        results[condition_name] = {
            'market_price': market_price,
            'roi_pct': roi['roi_pct'],
            'roi_value': roi['roi_value'],
            'profit_margin': roi['margin'],
            'seller_count': condition_data.get('seller_count'),
            'is_fba': condition_data.get('fba_count', 0) > 0
        }

    # Determine recommended condition (best ROI)
    best_condition = max(
        results.items(),
        key=lambda x: x[1]['roi_pct']
    )

    for condition_name in results:
        results[condition_name]['is_recommended'] = (
            condition_name == best_condition[0]
        )

    return results

def calculate_roi(market_price: float, source_price: float, config: Dict) -> Dict:
    """
    Calculate ROI with Amazon fees.

    net_revenue = market_price - amazon_fees - shipping - handling
    roi_value = net_revenue - source_price
    roi_pct = (roi_value / source_price) * 100
    """
    amazon_fee_pct = config.get('amazon_fee_pct', 0.15)
    shipping_cost = config.get('shipping_cost', 2.50)

    amazon_fees = market_price * amazon_fee_pct
    net_revenue = market_price - amazon_fees - shipping_cost

    roi_value = net_revenue - source_price
    roi_pct = (roi_value / source_price * 100) if source_price > 0 else 0
    margin = (roi_value / market_price * 100) if market_price > 0 else 0

    return {
        'roi_value': roi_value,
        'roi_pct': roi_pct,
        'margin': margin,
        'net_revenue': net_revenue
    }
```

### Tests avec MCP Keepa
```bash
# Test 2: Validate calculate_pricing_metrics_unified()
parsed_data = parse_keepa_product_unified(response)
source_price = 2.50  # Cost to acquire

metrics = calculate_pricing_metrics_unified(parsed_data, source_price, config)

# Verify:
✓ metrics['good']['roi_pct'] > metrics['new']['roi_pct']
✓ metrics['good']['is_recommended'] = true
✓ All ROI values are reasonable (between -100% and +1000%)
✓ metrics['good']['roi_pct'] ≈ 67.3%

# Expected output:
{
  'new': {'market_price': 16.98, 'roi_pct': -5.2, 'is_recommended': false, ...},
  'very_good': {'market_price': 10.94, 'roi_pct': 42.5, 'is_recommended': false, ...},
  'good': {'market_price': 8.00, 'roi_pct': 67.3, 'is_recommended': true, ...},
  'acceptable': {'market_price': 9.94, 'roi_pct': 57.8, 'is_recommended': false, ...}
}
```

### Validation Criteria ✓
- [ ] ROI calculated correctly for each condition
- [ ] Best condition marked as recommended
- [ ] ROI values are realistic
- [ ] Good condition ROI > New condition ROI

---

## 📦 PHASE 3: Créer build_unified_product_v2()

### Objectif
Créer UNE SEULE fonction que TOUS les endpoints utilisent pour build la réponse API.

### Fichiers à Modifier
- `backend/app/services/unified_analysis.py` → Refactoriser complètement

### Code à Créer

```python
async def build_unified_product_v2(
    raw_keepa: Dict[str, Any],
    keepa_service: KeepaService,
    config: Dict[str, Any],
    view_type: str = "analyse_manuelle",  # analyse_manuelle | mes_niches | autosourcing
    strategy: Optional[str] = None,
    compute_score: bool = True,
    source_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    UNIFIED product builder - Utilisé par TOUS les endpoints.

    Logic flow:
    1. Parse with parse_keepa_product_unified()
    2. Calculate pricing with calculate_pricing_metrics_unified()
    3. Calculate velocity
    4. Compute score (if applicable)
    5. Assemble response

    Returns: Unified product dict
    """
    asin = raw_keepa.get('asin', 'unknown')

    # Step 1: Parse with unified parser
    parsed = parse_keepa_product_unified(raw_keepa)

    # Step 2: Get Amazon presence
    amazon_result = check_amazon_presence(raw_keepa)

    # Step 3: Calculate pricing metrics
    pricing_metrics = await calculate_pricing_metrics_unified(
        parsed,
        source_price or config.get('default_source_price', 5.0),
        config
    )

    # Step 4: Calculate velocity
    current_bsr = parsed.get('current_bsr')
    velocity = calculate_velocity_score(current_bsr, config)

    # Step 5: Compute score (if applicable - for Mes Niches/AutoSourcing)
    score_result = {}
    if compute_score and view_type in ['mes_niches', 'autosourcing']:
        score_result = await compute_product_score(parsed, pricing_metrics, config)

    # Step 6: Assemble response
    return {
        'asin': asin,
        'title': raw_keepa.get('title'),

        # Pricing breakdown by condition
        'pricing': {
            'current_prices': {
                'amazon': parsed.get('current_amazon_price'),
                'new': parsed.get('current_new_price'),
                'used': parsed.get('current_used_price'),
                'fba': parsed.get('current_fba_price'),
            },
            'by_condition': pricing_metrics,  # Detailed ROI per condition
            'recommended_condition': next(
                (k for k, v in pricing_metrics.items() if v.get('is_recommended')),
                'good'
            )
        },

        # Velocity metrics
        'velocity': velocity,
        'current_bsr': current_bsr,

        # Scoring (for Mes Niches/AutoSourcing)
        'score': score_result.get('score', 0) if compute_score else None,
        'rank': score_result.get('rank', 0) if compute_score else None,

        # Amazon presence
        'amazon_on_listing': amazon_result.get('on_listing'),
        'amazon_buybox': amazon_result.get('has_buybox'),

        # Metadata
        'view_type': view_type,
        'timestamp': datetime.now().isoformat()
    }
```

### Tests avec MCP Keepa
```bash
# Test 3: Validate build_unified_product_v2()
response = mcp_keepa.get_product("0593655036", domain=1, days=7, offers=20)

# Test from Analyse Manuelle perspective
product_manuelle = await build_unified_product_v2(
    response,
    keepa_service,
    config,
    view_type='analyse_manuelle',
    source_price=2.50,
    compute_score=False
)

# Test from Mes Niches perspective
product_mes_niches = await build_unified_product_v2(
    response,
    keepa_service,
    config,
    view_type='mes_niches',
    source_price=2.50,
    compute_score=True
)

# Verify:
✓ product_manuelle['pricing']['by_condition']['good']['roi_pct'] = product_mes_niches same value
✓ Both show 'good' condition recommended
✓ pricing['current_prices']['fba'] used correctly (not 'used')
✓ All pricing metrics identical
```

### Validation Criteria ✓
- [ ] Same ASIN returns identical pricing regardless of view_type
- [ ] by_condition pricing accurate
- [ ] Recommended condition always has highest ROI
- [ ] current_bsr correctly populated

---

## 🔧 PHASE 4: Refactor Tous les Endpoints

### Fichiers à Modifier
1. `backend/app/api/v1/routers/keepa.py` → Analyse Manuelle
2. `backend/app/api/v1/routers/views.py` → Mes Niches + AutoSourcing

### Changes pour Analyse Manuelle (keepa.py)

**Before:**
```python
@router.post("/ingest")
async def ingest_batch(request: IngestBatchRequest):
    for identifier in request.identifiers:
        product_data = await keepa_service.get_product_data(identifier)
        parsed = parse_keepa_product(product_data)  # ❌ Old parser
        # ... rest of logic
```

**After:**
```python
@router.post("/ingest")
async def ingest_batch(request: IngestBatchRequest):
    for identifier in request.identifiers:
        product_data = await keepa_service.get_product_data(identifier)

        # ✅ Use unified builder
        unified_product = await build_unified_product_v2(
            raw_keepa=product_data,
            keepa_service=keepa_service,
            config=config,
            view_type='analyse_manuelle',  # ← NEW parameter
            compute_score=False,
            source_price=request.source_price  # ← USER provides this
        )

        scored_products.append(unified_product)
```

### Changes pour Mes Niches + AutoSourcing (views.py)

**Before:**
```python
@router.post("/mes_niches")
async def mes_niches(request: MesNichesRequest):
    for identifier in request.identifiers:
        product_data = await keepa_service.get_product_data(identifier)
        unified_product = await build_unified_product(  # ❌ Old function
            product_data,
            keepa_service,
            config,
            view_type=view_type
        )
```

**After:**
```python
@router.post("/mes_niches")
async def mes_niches(request: MesNichesRequest):
    for identifier in request.identifiers:
        product_data = await keepa_service.get_product_data(identifier)

        # ✅ Use unified builder
        unified_product = await build_unified_product_v2(
            raw_keepa=product_data,
            keepa_service=keepa_service,
            config=config,
            view_type='mes_niches',  # ← NEW parameter
            compute_score=True,
            source_price=config.get('default_source_price', 5.0)
        )
```

### Tests avec MCP Keepa
```bash
# Test 4: Validate all three endpoints return same data structure

# Test Analyse Manuelle
response_manuelle = requests.post(
    'http://localhost:8001/api/v1/keepa/ingest',
    json={'identifiers': ['0593655036'], 'source_price': 2.50}
)

# Test Mes Niches
response_mes_niches = requests.post(
    'http://localhost:8001/api/v1/views/mes_niches',
    json={'identifiers': ['0593655036'], 'strategy': 'arbitrage'}
)

# Verify:
✓ response_manuelle['pricing'] === response_mes_niches['pricing']
✓ response_manuelle['current_bsr'] === response_mes_niches['current_bsr']
✓ response_manuelle['pricing']['by_condition']['good']['roi_pct'] matches expected ~67.3%
```

### Validation Criteria ✓
- [ ] All three endpoints use build_unified_product_v2()
- [ ] Same ASIN returns identical pricing data
- [ ] Response structure consistent across endpoints
- [ ] No regression in existing functionality

---

## 🎁 PHASE 5: Ajouter offers_by_condition Feature

### Objectif
Afficher les offres détaillées PAR CONDITION dans la réponse API.

### Code à Créer
(Déjà intégré dans Phase 3 - `build_unified_product_v2()`)

### Tests avec MCP Keepa
```bash
# Test 5: Validate offers_by_condition structure

response = requests.post(
    'http://localhost:8001/api/v1/keepa/ingest',
    json={'identifiers': ['0593655036'], 'source_price': 2.50}
).json()

pricing = response[0]['pricing']['by_condition']

# Verify structure:
✓ pricing['good']['market_price'] = 8.00
✓ pricing['good']['roi_pct'] = 67.3
✓ pricing['good']['is_recommended'] = true
✓ pricing['good']['seller_count'] = 12
✓ pricing['very_good']['market_price'] = 10.94
✓ pricing['very_good']['roi_pct'] = 42.5
✓ All conditions sorted by ROI descending
```

### Validation Criteria ✓
- [ ] offers_by_condition returns for all conditions
- [ ] Minimum price correct for each condition
- [ ] ROI calculated accurately
- [ ] Recommended badge on best ROI

---

## 🎨 PHASE 6: Mettre à Jour Frontend

### Objectif
Afficher le breakdown de pricing par condition.

### UI Changes

**Before (Current):**
```
Prix USED: $16.90 ❌ Confus
ROI USED: +48.7% ❌ Incorrect
```

**After (New):**
```
💰 Meilleur Prix: $8.00 (Used - Good) | ROI: +67.3%
👇 Voir détails

[Accordéon]
├─ ⭐ USED - Good      $8.00   | ROI: +67.3%  | 12 vendeurs
├─ USED - V. Good     $10.94  | ROI: +42.5%  | 8 vendeurs
├─ USED - Accept.     $9.94   | ROI: +57.8%  | 25 vendeurs
└─ NEW                $16.98  | ROI: -5.2%   | 4 vendeurs
```

### Components à Créer
- `<PricingBreakdown />` - Affiche prix minimum + ROI
- `<ConditionAccordion />` - Détails par condition

### Tests Frontend
```bash
# Manual testing
1. Open Analyse Manuelle
   - Enter ASIN 0593655036
   - Verify shows $8.00 as meilleur prix
   - Open accordéon
   - Verify all 4 conditions displayed

2. Open Mes Niches
   - Verify same pricing as Analyse Manuelle
   - Verify accordéon shows identical ROI values

3. Cross-browser testing
   - Chrome, Firefox, Safari
   - Mobile responsiveness
```

### Validation Criteria ✓
- [ ] Pricing breakdown displays correctly
- [ ] Accordéon toggles properly
- [ ] Same ASIN shows identical pricing across views
- [ ] Mobile responsive
- [ ] No console errors

---

## 📊 Résumé des Phases

| Phase | Objectif | Fichiers | Validation MCP | Durée |
|-------|----------|----------|---|---------|
| **1** | Unified Parser | keepa_parser_v2.py | ✓ 3+ ASINs | 1.5h |
| **2** | Unified Pricing | pricing_service.py | ✓ ROI accuracy | 1.5h |
| **3** | Unified Builder | unified_analysis.py | ✓ All endpoints | 1.5h |
| **4** | Refactor Endpoints | keepa.py, views.py | ✓ API consistency | 1.5h |
| **5** | offers_by_condition | (intégré Phase 3) | ✓ Structure | 0.5h |
| **6** | Frontend | UI Components | ✓ Display | 2h |
| **TOTAL** | | | | **8.5h** |

---

## ✅ Validation Checklist

### Après chaque phase, vérifier:
```
Phase 1 ✓
  □ MCP Keepa returns correct structure
  □ BSR correctly extracted
  □ Offers grouped by condition
  □ No -1 values for valid data

Phase 2 ✓
  □ ROI calculated accurately
  □ Good condition ROI > New ROI
  □ is_recommended flag set correctly
  □ All 4 conditions included

Phase 3 ✓
  □ build_unified_product_v2() works
  □ Same ASIN returns identical data
  □ All fields populated
  □ No errors in logs

Phase 4 ✓
  □ Analyse Manuelle uses unified builder
  □ Mes Niches uses unified builder
  □ AutoSourcing uses unified builder
  □ API response identical across endpoints

Phase 5 ✓
  □ offers_by_condition in response
  □ All conditions included
  □ Structure matches design

Phase 6 ✓
  □ UI renders correctly
  □ Accordéon toggles
  □ Mobile responsive
  □ No console errors
```

---

## 🎯 Prochaines Étapes

**Avant de commencer Phase 1:**

1. ✅ Valider ce plan avec l'utilisateur
2. ✅ Confirmer la structure des données
3. ✅ Approuver les phases et timing
4. ⏳ Commencer Phase 1 avec validation MCP Keepa

