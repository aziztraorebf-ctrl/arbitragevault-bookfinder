# 🔬 Plan Validation avec Vraies Données - Correction de Route

**Date** : 24 Octobre 2025
**Objectif** : Corriger l'approche actuelle et valider CHAQUE composant avec vraies données Keepa

---

## ⚠️ Problème Identifié

**Situation Actuelle** :
- Jour 1-2 : Code reviews et tests "happy path" (2 ASINs)
- Pas de validation batch avec vraies données
- Répétition du pattern initial (données simulées → production)

**Risque** :
- Code qui a l'air correct mais crash en production
- Edge cases non détectés
- Faux sentiment de sécurité

---

## ✅ Nouvelle Approche : Validation 3-Tiers

### **Tier 1 : Validation Unitaire (Jour 3 Matin)**

**Objectif** : Tester CHAQUE composant isolément avec vraies données

#### Test 1.1 : Keepa API Direct
```python
# backend/scripts/test_keepa_api_direct.py
import keepa

api = keepa.Keepa(API_KEY)

# Test 1 : Vérifier que product_finder existe
try:
    results = api.product_finder({...})
    print("✅ product_finder existe")
except AttributeError:
    print("❌ product_finder n'existe PAS - upgrade lib requis")

# Test 2 : Vérifier structure response
products = api.query("0593655036", domain='US', stats=180)
print(f"Structure : {products[0].keys()}")
print(f"current[3] : {products[0].get('current', [])[3] if len(products[0].get('current', [])) > 3 else 'MISSING'}")
```

**Critère Succès** : Méthodes existent + current[3] contient BSR

---

#### Test 1.2 : BSR Parsing avec 30 ASINs Réels
```python
# backend/scripts/test_bsr_parsing_batch.py

TEST_ASINS = [
    # Livres best-sellers (BSR 1k-10k)
    "0593655036", "1668026473", "0385348371", "1250178630", "0593230574",

    # Textbooks (BSR 50k-200k)
    "1449355730", "0134685997", "0134757599", "013468599X", "0134685991",

    # Électronique populaire (BSR 100-5k)
    "B07ZPKN6YR", "B0BSHF7LLL", "B08N5WRWNW", "B07FNW9FGJ", "B09B8YCWYW",

    # Produits "dead" (BSR > 500k)
    "B00001234X", "B00005678Y", "B00009012Z",

    # Edge cases
    "B000INVALID",  # ASIN invalide
    "0000000000",   # ISBN inexistant
]

async def test_batch_parsing():
    keepa_service = KeepaService(api_key=API_KEY)
    results = {
        "success": 0,
        "failed": 0,
        "bsr_missing": 0,
        "bsr_negative": 0,
        "edge_cases": []
    }

    for asin in TEST_ASINS:
        try:
            # Fetch vraie donnée
            product_data = await keepa_service.get_product_data(asin)

            if not product_data:
                results["failed"] += 1
                continue

            # Parse avec parser_v2
            parsed = parse_keepa_product(product_data)

            # Valider BSR
            if parsed.get("bsr") is None:
                results["bsr_missing"] += 1
                results["edge_cases"].append((asin, "BSR missing"))
            elif parsed.get("bsr") < 0:
                results["bsr_negative"] += 1
                results["edge_cases"].append((asin, f"BSR negative: {parsed['bsr']}"))
            else:
                results["success"] += 1

        except Exception as e:
            results["failed"] += 1
            results["edge_cases"].append((asin, str(e)))

    # Rapport
    print(f"✅ Success: {results['success']}/30 ({results['success']/30*100:.0f}%)")
    print(f"❌ Failed: {results['failed']}/30")
    print(f"⚠️  BSR Missing: {results['bsr_missing']}/30")
    print(f"⚠️  BSR Negative: {results['bsr_negative']}/30")

    if results["edge_cases"]:
        print("\nEdge Cases:")
        for asin, issue in results["edge_cases"]:
            print(f"  - {asin}: {issue}")

    # Critère succès : 90%+ (27/30)
    return results["success"] >= 27
```

**Critère Succès** : ≥90% ASINs parsés correctement (27/30)

---

#### Test 1.3 : Velocity Calculation avec BSR History Réel
```python
# backend/scripts/test_velocity_real_data.py

async def test_velocity_calculation():
    """
    Valider que velocity_score utilise BSR history correctement.
    Teste avec produits à trends différents.
    """

    test_cases = [
        {
            "asin": "0593655036",  # Best-seller stable
            "expected_velocity_range": (80, 100),
            "description": "Best-seller tendance montante"
        },
        {
            "asin": "1449355730",  # Textbook ancien
            "expected_velocity_range": (20, 60),
            "description": "Textbook mature, ventes stables"
        },
        {
            "asin": "B000DEADPROD",  # Produit discontinué
            "expected_velocity_range": (0, 20),
            "description": "Produit fin de vie"
        }
    ]

    for test_case in test_cases:
        asin = test_case["asin"]

        # Fetch vraie donnée
        product_data = await keepa_service.get_product_data(asin)
        parsed = parse_keepa_product(product_data)

        # Extraire BSR history
        bsr_history = extract_bsr_history(product_data)

        print(f"\n{asin} ({test_case['description']}):")
        print(f"  BSR Current: {parsed.get('bsr')}")
        print(f"  BSR History Points: {len(bsr_history)}")

        # Calculer velocity
        velocity = compute_velocity_score(bsr_history)

        print(f"  Velocity Score: {velocity}")

        # Valider range attendu
        min_v, max_v = test_case["expected_velocity_range"]
        if min_v <= velocity <= max_v:
            print(f"  ✅ PASS - Velocity dans range attendu [{min_v}-{max_v}]")
        else:
            print(f"  ❌ FAIL - Velocity hors range (attendu [{min_v}-{max_v}], obtenu {velocity})")

        # Diagnostic détaillé
        if len(bsr_history) > 0:
            # Trend analysis
            sorted_history = sorted(bsr_history, key=lambda x: x[0])  # Sort by timestamp
            oldest_bsr = sum([bsr for _, bsr in sorted_history[:7]]) / 7
            recent_bsr = sum([bsr for _, bsr in sorted_history[-7:]]) / 7

            improvement = (oldest_bsr - recent_bsr) / oldest_bsr if oldest_bsr > 0 else 0

            print(f"  Oldest BSR (avg 7): {oldest_bsr:.0f}")
            print(f"  Recent BSR (avg 7): {recent_bsr:.0f}")
            print(f"  Improvement: {improvement*100:.1f}%")

# Critère succès : 3/3 test cases dans range attendu
```

**Critère Succès** : 3/3 produits avec velocity dans range attendu

---

### **Tier 2 : Validation Intégration (Jour 3 Après-midi)**

**Objectif** : Tester flows complets bout-en-bout

#### Test 2.1 : Flow "Scan ASIN → Résultat" (Batch)
```python
# backend/scripts/test_scan_flow_batch.py

async def test_scan_flow_batch():
    """
    Teste le flow complet utilisateur avec 20 ASINs.
    Simule exactement ce que le frontend fait.
    """

    asins = [
        "0593655036", "B07ZPKN6YR", "1449355730", "B0BSHF7LLL",
        # ... 16 autres ASINs variés
    ]

    results = []

    for asin in asins:
        # Appel API comme frontend
        response = requests.get(
            f"{BASE_URL}/api/v1/keepa/{asin}/metrics",
            timeout=30
        )

        # Valider response
        assert response.status_code == 200, f"Status {response.status_code} pour {asin}"
        data = response.json()

        # Valider structure complète
        assert "analysis" in data
        assert "roi" in data["analysis"]
        assert "velocity" in data["analysis"]
        assert "velocity_score" in data["analysis"]
        assert "overall_rating" in data["analysis"]

        # Extraire métriques
        velocity = data["analysis"]["velocity_score"]
        roi = data["analysis"]["roi"].get("roi_percent")
        rating = data["analysis"]["overall_rating"]

        results.append({
            "asin": asin,
            "velocity": velocity,
            "roi": roi,
            "rating": rating
        })

        print(f"{asin}: Velocity={velocity}, ROI={roi}%, Rating={rating}")

    # Statistiques
    velocities = [r["velocity"] for r in results if r["velocity"] is not None]
    avg_velocity = sum(velocities) / len(velocities)

    print(f"\nStatistiques:")
    print(f"  ASINs testés: {len(results)}")
    print(f"  Velocity moyenne: {avg_velocity:.1f}")
    print(f"  Ratings distribution:")
    for rating in ["EXCELLENT", "GOOD", "FAIR", "POOR"]:
        count = sum(1 for r in results if r["rating"] == rating)
        print(f"    {rating}: {count}/20 ({count/20*100:.0f}%)")

# Critère succès : 20/20 ASINs retournent résultats complets
```

**Critère Succès** : 100% ASINs (20/20) retournent données complètes

---

#### Test 2.2 : AutoSourcing Flow Complet
```python
# backend/scripts/test_autosourcing_e2e.py

async def test_autosourcing_complete():
    """
    Teste AutoSourcing bout-en-bout avec vraie découverte Keepa.
    """

    # Payload test
    payload = {
        "profile_name": "Test E2E Production",
        "discovery_config": {
            "categories": ["Books"],
            "price_range": [10, 50],
            "bsr_range": [1000, 50000],
            "max_results": 10  # Petit batch pour test
        },
        "scoring_config": {
            "roi_min": 30,
            "velocity_min": 70,
            "stability_min": 70,
            "confidence_min": 70,
            "rating_required": "GOOD"
        }
    }

    print("🚀 Lancement AutoSourcing E2E...")

    # Appel API
    response = requests.post(
        f"{BASE_URL}/api/v1/autosourcing/run-custom",
        json=payload,
        timeout=120  # 2min max
    )

    print(f"Status: {response.status_code}")

    # Valider création job
    assert response.status_code in [200, 202], f"Expected 200/202, got {response.status_code}"

    data = response.json()
    job_id = data.get("id")

    print(f"✅ Job créé: {job_id}")
    print(f"Total tested: {data.get('total_tested', 0)}")
    print(f"Total selected: {data.get('total_selected', 0)}")

    # Valider picks
    picks = data.get("picks", [])
    print(f"\nPicks découverts: {len(picks)}")

    for pick in picks[:5]:  # Afficher top 5
        print(f"  - {pick['asin']}: ROI={pick['roi_percentage']:.0f}%, Velocity={pick['velocity_score']}")

    # Critères succès
    assert len(picks) > 0, "Aucun pick découvert"
    assert data.get("total_tested", 0) > 0, "Aucun produit testé"

    print("\n✅ AutoSourcing E2E: PASS")

# Critère succès : Job créé + Au moins 1 pick découvert
```

**Critère Succès** : Job créé avec succès + ≥1 pick retourné

---

### **Tier 3 : Validation Robustesse (Jour 3 Fin)**

**Objectif** : Tester edge cases et limites système

#### Test 3.1 : Edge Cases
```python
# backend/scripts/test_edge_cases.py

EDGE_CASES = [
    {
        "asin": "B000INVALID",
        "expected": "404 ou empty response",
        "description": "ASIN invalide"
    },
    {
        "asin": "0000000000",
        "expected": "404 ou empty response",
        "description": "ISBN inexistant"
    },
    {
        "asin": "B07ZPKN6YR",  # Produit très populaire
        "test": "timeout",
        "description": "Produit avec énorme historique (timeout possible)"
    },
    {
        "asin": "B00DEADPROD",  # Produit discontinué
        "expected": "BSR = None ou très élevé",
        "description": "Produit fin de vie"
    }
]

# Tester chaque edge case et documenter comportement
```

---

#### Test 3.2 : Load Test
```python
# backend/scripts/test_load_batch.py

async def test_load_100_asins():
    """
    Teste système avec batch de 100 ASINs simultanés.
    Valide que cache, DB, et API Keepa tiennent la charge.
    """

    asins = generate_100_varied_asins()  # Mix livres/électronique

    # Batch parallel requests
    tasks = [fetch_metrics(asin) for asin in asins]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analyser résultats
    success = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - success

    print(f"Load Test 100 ASINs:")
    print(f"  ✅ Success: {success}/100 ({success}%)")
    print(f"  ❌ Failed: {failed}/100")

    # Critère : 95%+ success rate
    assert success >= 95, f"Load test échoué: {success}% success (minimum 95%)"
```

---

## 📊 Critères de Validation Globaux

### **Tier 1 : Unitaire**
- ✅ Keepa API methods existent (product_finder, query)
- ✅ 90%+ ASINs parsent correctement (27/30)
- ✅ Velocity calculation dans range attendu (3/3)

### **Tier 2 : Intégration**
- ✅ 100% flow "Scan ASIN → Résultat" (20/20)
- ✅ AutoSourcing E2E crée job + picks (≥1 pick)

### **Tier 3 : Robustesse**
- ✅ Edge cases documentés (comportement défini)
- ✅ Load test 95%+ success (95/100)

---

## 🎯 Estimation Temps

| Tier | Tests | Durée | Priorité |
|------|-------|-------|----------|
| Tier 1 | 3 tests unitaires | 3h | 🔴 CRITIQUE |
| Tier 2 | 2 tests intégration | 2h | 🟡 IMPORTANT |
| Tier 3 | 2 tests robustesse | 1h | 🟢 NICE-TO-HAVE |

**Total** : 6h (avec buffer → 8h journée complète)

---

## ✅ Livrables Attendus

1. **Scripts de Test** :
   - `test_keepa_api_direct.py`
   - `test_bsr_parsing_batch.py`
   - `test_velocity_real_data.py`
   - `test_scan_flow_batch.py`
   - `test_autosourcing_e2e.py`
   - `test_edge_cases.py`
   - `test_load_batch.py`

2. **Rapports de Résultats** :
   - `validation_tier1_results.md` (parsing, velocity)
   - `validation_tier2_results.md` (flows E2E)
   - `validation_tier3_results.md` (edge cases, load)

3. **Fixes Identifiés** :
   - Liste bugs découverts avec vraies données
   - Patches appliqués
   - Re-validation après fixes

---

## 🚨 GO/NO-GO Decision

**Critère GO Phase 1** :
- ✅ Tier 1 : 100% validé (tous tests passent)
- ✅ Tier 2 : 100% validé (flows E2E OK)
- ⚠️  Tier 3 : 80%+ validé (edge cases documentés)

**Si < 80% Tier 1+2** : NO-GO → Investigation approfondie requise

---

**Plan révisé prêt pour exécution Jour 3 avec VRAIES données.**
