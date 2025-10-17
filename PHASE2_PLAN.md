# Phase 2 Implementation Plan - Views Integration

**Date** : 2025-10-11
**Prerequisites** : Phase 1 COMPLETE ✅
**Estimated Time** : 3-4h implementation + 1h testing + 48h shadow mode validation

---

## 🎯 Objectif Phase 2

Implémenter scoring adaptatif par vue (Dashboard, MesNiches, AnalyseStrategique, etc.) avec pondérations spécifiques selon contexte utilisateur.

---

## 📋 Scope Phase 2

### **1. VIEW_WEIGHTS Matrix** (1h)
**Fichier** : `backend/app/services/scoring_v2.py` (nouveau)

**Structure** :
```python
VIEW_WEIGHTS = {
    "dashboard": {
        "roi": 0.5,
        "velocity": 0.5,
        "stability": 0.3
    },
    "mes_niches": {
        "roi": 0.6,
        "velocity": 0.4,
        "stability": 0.5
    },
    "analyse_strategique": {
        "roi": 0.4,
        "velocity": 0.6,
        "stability": 0.2
    },
    "auto_sourcing": {
        "roi": 0.3,
        "velocity": 0.7,
        "stability": 0.1
    },
    "stock_estimates": {
        "roi": 0.45,
        "velocity": 0.45,
        "stability": 0.6
    },
    "niche_discovery": {
        "roi": 0.5,
        "velocity": 0.5,
        "stability": 0.4
    }
}
```

**Logique Business** :
- **Dashboard** : Équilibré (ROI=velocity)
- **MesNiches** : ROI prioritaire (niches rentables)
- **AnalyseStrategique** : Velocity prioritaire (rotation rapide)
- **AutoSourcing** : Velocity maximal (automatisation rapide)
- **StockEstimates** : Stability prioritaire (prédictions fiables)
- **NicheDiscovery** : Équilibré + stabilité (exploration)

---

### **2. compute_view_score() Function** (1h)
**Fichier** : `backend/app/services/scoring_v2.py`

**Signature** :
```python
def compute_view_score(
    parsed_data: Dict[str, Any],
    view_type: str,
    strategy_profile: str
) -> Dict[str, Any]:
    """
    Calculate adaptive score based on view context.

    Args:
        parsed_data: Keepa parsed product data
        view_type: Vue frontend (dashboard, mes_niches, etc.)
        strategy_profile: textbook | velocity | balanced

    Returns:
        {
            "score": float (0-100),
            "view_type": str,
            "weights_applied": dict,
            "components": {
                "roi_contribution": float,
                "velocity_contribution": float,
                "stability_contribution": float
            }
        }
    """
```

**Calcul** :
```python
# 1. Extraire weights de la vue
weights = VIEW_WEIGHTS.get(view_type, VIEW_WEIGHTS["dashboard"])

# 2. Extraire métriques du parsed_data
roi_pct = parsed_data.get("roi", {}).get("roi_percentage", 0)
velocity_score = parsed_data.get("velocity_score", 0)
stability_score = parsed_data.get("stability_score", 50)  # default neutre

# 3. Normaliser métriques (0-100)
roi_norm = min(max(roi_pct, 0), 100)
velocity_norm = min(max(velocity_score, 0), 100)
stability_norm = min(max(stability_score, 0), 100)

# 4. Calcul pondéré
score = (
    roi_norm * weights["roi"] +
    velocity_norm * weights["velocity"] +
    stability_norm * weights["stability"]
)

# 5. Appliquer stratégie boost (optional)
strategy_boosts = {
    "textbook": {"roi": 1.2},
    "velocity": {"velocity": 1.2},
    "balanced": {}
}
# Apply boost logic...

return {
    "score": round(score, 2),
    "view_type": view_type,
    "weights_applied": weights,
    "components": {
        "roi_contribution": round(roi_norm * weights["roi"], 2),
        "velocity_contribution": round(velocity_norm * weights["velocity"], 2),
        "stability_contribution": round(stability_norm * weights["stability"], 2)
    }
}
```

---

### **3. New Endpoint `/views/{view_type}`** (1h)
**Fichier** : `backend/app/api/v1/routers/views.py` (nouveau)

**Signature** :
```python
@router.post("/views/{view_type}", response_model=ViewScoreResponse)
async def score_products_for_view(
    view_type: str,
    request: ViewScoreRequest,
    http_request: Request,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Score products with view-specific weights.

    Path Params:
        view_type: dashboard | mes_niches | analyse_strategique |
                   auto_sourcing | stock_estimates | niche_discovery

    Request Body:
        {
            "identifiers": ["ASIN1", "ASIN2", ...],
            "strategy": "textbook" | "velocity" | "balanced" (optional)
        }

    Response:
        {
            "view_type": str,
            "products": [
                {
                    "asin": str,
                    "score": float,
                    "strategy_profile": str,
                    "components": {...},
                    "rank": int
                },
                ...
            ],
            "metadata": {
                "weights_used": {...},
                "total_products": int,
                "avg_score": float
            }
        }
    """
```

**Logique** :
1. Valider `view_type` (enum)
2. Fetch Keepa data pour ASINs
3. Parse data avec `keepa_parser_v2.py`
4. Pour chaque produit → `compute_view_score()`
5. Trier par score DESC
6. Assigner ranks
7. Retourner JSON

---

### **4. Tests Unitaires** (1h)
**Fichier** : `backend/tests/unit/test_view_scoring.py` (nouveau)

**Coverage** :
```python
# Test 1: VIEW_WEIGHTS matrix structure
def test_view_weights_structure():
    assert "dashboard" in VIEW_WEIGHTS
    assert all(k in VIEW_WEIGHTS["dashboard"] for k in ["roi", "velocity", "stability"])

# Test 2: compute_view_score() avec données complètes
def test_compute_view_score_complete_data():
    parsed = {
        "roi": {"roi_percentage": 50},
        "velocity_score": 70,
        "stability_score": 60
    }
    result = compute_view_score(parsed, "dashboard", "balanced")
    assert 40 <= result["score"] <= 80  # Expected range

# Test 3: compute_view_score() avec données manquantes
def test_compute_view_score_missing_metrics():
    parsed = {"roi": {"roi_percentage": 0}}  # Missing velocity/stability
    result = compute_view_score(parsed, "mes_niches", "textbook")
    assert result["score"] >= 0

# Test 4: View type invalide → fallback dashboard
def test_invalid_view_type_fallback():
    result = compute_view_score({}, "invalid_view", "balanced")
    assert result["weights_applied"] == VIEW_WEIGHTS["dashboard"]

# Test 5: Strategy boost application
def test_strategy_boost_textbook():
    parsed = {"roi": {"roi_percentage": 80}, "velocity_score": 30}
    result = compute_view_score(parsed, "mes_niches", "textbook")
    # textbook boost should increase score vs balanced
    result_balanced = compute_view_score(parsed, "mes_niches", "balanced")
    assert result["score"] >= result_balanced["score"]

# Test 6: Normalisation boundaries (ROI > 100, négatif)
def test_score_normalization():
    parsed = {"roi": {"roi_percentage": 150}}  # Over 100%
    result = compute_view_score(parsed, "dashboard", "balanced")
    assert result["components"]["roi_contribution"] <= 100

# Test 7: E2E avec endpoint /views/{view_type}
@pytest.mark.asyncio
async def test_views_endpoint_integration():
    # Mock Keepa API response
    # Call /views/dashboard with 3 ASINs
    # Assert response structure + ranking
    pass
```

**Target Coverage** : 90%+ pour `scoring_v2.py` et `views.py`

---

## 🔧 Technical Implementation Details

### **Fichiers à Créer**
1. `backend/app/services/scoring_v2.py`
   - VIEW_WEIGHTS constant
   - compute_view_score() function
   - Optional: compute_strategy_boost() helper

2. `backend/app/api/v1/routers/views.py`
   - POST /views/{view_type} endpoint
   - ViewScoreRequest schema (Pydantic)
   - ViewScoreResponse schema (Pydantic)

3. `backend/tests/unit/test_view_scoring.py`
   - 7+ unit tests covering edge cases

### **Fichiers à Modifier**
1. `backend/app/main.py`
   - Ajouter router views : `app.include_router(views.router, prefix="/api/v1", tags=["views"])`

2. `backend/config/business_rules.json`
   - Activer feature flag après validation :
     ```json
     "feature_flags": {
       "view_specific_scoring": true  // OFF → ON après tests
     }
     ```

3. `backend/app/core/version.py`
   - Update BUILD_TAG : `strategy_refactor_v2_phase2_views`

---

## 🧪 Testing Strategy

### **1. Unit Tests** (1h)
```bash
cd backend
pytest tests/unit/test_view_scoring.py -v --cov=app/services/scoring_v2 --cov=app/api/v1/routers/views
```

**Success Criteria** :
- ✅ 7+ tests PASS
- ✅ Coverage ≥ 90%
- ✅ Edge cases handled (missing data, invalid view types)

### **2. Manual API Testing** (30m)
```bash
# Test 1: Dashboard view
curl -X POST "http://localhost:8000/api/v1/views/dashboard" \
  -H "Content-Type: application/json" \
  -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \
  -d '{"identifiers":["0593655036","B08N5WRWNW"]}'

# Test 2: MesNiches view (ROI-heavy)
curl -X POST "http://localhost:8000/api/v1/views/mes_niches" \
  -H "Content-Type: application/json" \
  -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \
  -d '{"identifiers":["0134685997","1259573545"],"strategy":"textbook"}'

# Test 3: AutoSourcing view (Velocity-heavy)
curl -X POST "http://localhost:8000/api/v1/views/auto_sourcing" \
  -H "Content-Type: application/json" \
  -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \
  -d '{"identifiers":["B00FLIJJSA","B0DFMNSKAX"],"strategy":"velocity"}'
```

**Validation** :
- ✅ Scores différents selon view_type
- ✅ Rankings cohérents avec weights
- ✅ Components détaillés (roi/velocity/stability contributions)

### **3. Production Shadow Mode** (48h)
```bash
# Activer shadow mode
# backend/config/business_rules.json:
{
  "feature_flags": {
    "view_specific_scoring": true,
    "scoring_shadow_mode": true  // Log V1 + V2 scores
  }
}
```

**Monitoring** :
- Logs Render : Comparer scores V1 vs V2 par vue
- Métriques : Temps réponse, erreurs, cohérence rankings
- Seuil GO/NO-GO : ±15% delta acceptable, zero erreurs critiques

---

## 🚀 Deployment Plan

### **Step 1: Implementation** (3h)
1. Créer `scoring_v2.py` avec VIEW_WEIGHTS + compute_view_score()
2. Créer `views.py` avec endpoint POST /views/{view_type}
3. Ajouter schemas Pydantic (ViewScoreRequest/Response)
4. Créer tests unitaires (7+ tests)
5. Update BUILD_TAG dans version.py

### **Step 2: Local Testing** (1h)
1. Lancer backend local
2. Run unit tests → Coverage ≥90%
3. Manual API tests (3 vues minimum)
4. Fix bugs si nécessaires

### **Step 3: Commit + Deploy** (30m)
```bash
git add backend/app/services/scoring_v2.py \
        backend/app/api/v1/routers/views.py \
        backend/tests/unit/test_view_scoring.py \
        backend/app/main.py \
        backend/app/core/version.py

git commit -m "feat(phase2): Add view-specific scoring system

- Create VIEW_WEIGHTS matrix (6 views)
- Implement compute_view_score() with adaptive weights
- Add POST /views/{view_type} endpoint
- 7+ unit tests with 90%+ coverage
- Feature flag: view_specific_scoring (OFF by default)

BUILD_TAG: strategy_refactor_v2_phase2_views"

git push origin main
```

### **Step 4: Production Validation** (48h)
1. Vérifier deploy Render SUCCESS
2. Activer shadow mode via config
3. Tester endpoints production avec header override
4. Monitorer logs 48h
5. Analyser delta scores V1 vs V2

### **Step 5: GO/NO-GO Decision**
**Critères GO** :
- ✅ Zero erreurs critiques
- ✅ Scores cohérents avec business rules
- ✅ Temps réponse < 3s par produit
- ✅ Delta V1 vs V2 acceptable (±15%)

**Si GO** :
```json
// backend/config/business_rules.json
{
  "feature_flags": {
    "view_specific_scoring": true,  // ON
    "scoring_shadow_mode": false    // OFF (validated)
  }
}
```

**Si NO-GO** :
- Rollback feature flag → false
- Investiguer logs anomalies
- Fix bugs + redeploy
- Re-validate 48h

---

## 📊 Success Metrics

### **Phase 2 Definition of Done**
- ✅ VIEW_WEIGHTS matrix défini (6 vues)
- ✅ compute_view_score() implémenté
- ✅ Endpoint POST /views/{view_type} créé
- ✅ Unit tests PASS (7+ tests, coverage ≥90%)
- ✅ Manual API tests validés (3 vues minimum)
- ✅ Deployed to production
- ✅ Shadow mode validation 48h PASS
- ✅ Feature flag activated in production
- ✅ BUILD_TAG updated

### **Performance Targets**
- Response time : < 3s par produit
- Error rate : < 1%
- Coverage : ≥ 90%

---

## 🔗 Dependencies & Prerequisites

### **Phase 1 Prerequisites (COMPLETE ✅)**
- ✅ Header override mechanism
- ✅ Feature flags infrastructure
- ✅ Strategy auto-selection logic
- ✅ Keepa price extraction functions

### **Phase 2 New Dependencies**
- None (uses existing Keepa parser + config service)

### **Optional Future Enhancements (Phase 3+)**
- User-specific weight customization
- A/B testing framework for weights
- ML-based weight optimization
- Real-time weight adjustment based on market conditions

---

## 📝 Documentation Tasks

1. **API Documentation** : Documenter endpoint /views/{view_type} dans OpenAPI
2. **Frontend Integration Guide** : Comment appeler endpoint depuis React
3. **Business Rules Doc** : Justification weights par vue
4. **Troubleshooting Guide** : Edge cases + fixes

---

## ⏱️ Timeline Summary

| Task | Duration | Status |
|------|----------|--------|
| Implementation (scoring_v2.py + views.py) | 3h | 🔜 Pending |
| Unit tests creation | 1h | 🔜 Pending |
| Local testing + fixes | 1h | 🔜 Pending |
| Commit + deploy to Render | 30m | 🔜 Pending |
| Production shadow mode validation | 48h | 🔜 Pending |
| GO/NO-GO decision + flag activation | 1h | 🔜 Pending |

**Total Estimated Time** : ~4-5h active work + 48h passive monitoring

---

## 🎯 Next Immediate Action

**READY TO START** : Implémenter `scoring_v2.py` avec VIEW_WEIGHTS matrix + compute_view_score() function.

**User Decision Required** :
1. Valider weights business logic (dashboard/mes_niches/etc.)
2. Confirmer vues prioritaires (6 vues ou subset ?)
3. Approuver début implémentation Phase 2

---

**Status** : 📋 **PLAN READY - Awaiting User GO for Phase 2 Implementation**

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
