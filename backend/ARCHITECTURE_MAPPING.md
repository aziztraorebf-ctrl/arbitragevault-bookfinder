# Architecture Mapping - Incohérences Identifiées

## 🚨 Problèmes Critiques Détectés

### 1. Batch Model vs Schema Mismatch

**Modèle (app/models/batch.py)**
```python
class Batch:
    name: str          # ✅ Présent
    # description        # ❌ MANQUANT
    status: BatchStatus # ✅ Présent (enum)
    items_total: int   # ✅ Présent
    user_id: str       # ✅ Présent (required)
```

**Schema (app/schemas/batch.py)**  
```python
class BatchResponse:
    name: str          # ✅ Match
    # description        # ❌ Supposé présent par tests
    status: str        # ⚠️ String vs Enum
    items_total: int   # ✅ Match
```

**Tests Supposaient**
```python
batch_data = {
    "description": "Test description"  # ❌ N'existe pas
}
```

**🔧 Action Requise**: Ajouter `description` au modèle OU l'enlever des tests

---

### 2. Services - Méthodes Incorrectes

**SalesVelocityService Réel**
```python
# ✅ Méthodes disponibles:
- analyze_product_velocity()
- estimate_monthly_sales()
- classify_velocity_tier()
```

**Tests Supposaient**
```python
service.calculate_velocity_score()  # ❌ N'existe pas
```

**🔧 Action Requise**: Utiliser méthodes réelles ou créer wrapper

---

### 3. Strategic Views - Mauvais Emplacement

**Emplacement Réel**
```
✅ app/routers/strategic_views.py
```

**Tests Cherchaient**
```python
from app.services.strategic_views_service  # ❌ N'existe pas
```

**🔧 Action Requise**: Créer service OU changer import tests

---

### 4. KeepaService - Initialisation Obligatoire

**Service Réel**
```python
def __init__(self, api_key: str, concurrency: int = 3):  # api_key REQUIRED
```

**Tests Supposaient**
```python
service = KeepaService()  # ❌ Manque api_key
```

**🔧 Action Requise**: Injection api_key via keyring

---

## 🎯 Plan de Refactoring

### Phase 1: Modèles & Schémas
- [ ] Harmoniser Batch model/schema
- [ ] Ajouter champ description si nécessaire  
- [ ] Valider enum vs string consistency

### Phase 2: Services Layer
- [ ] Créer StrategicViewsService wrapper
- [ ] Standardiser méthodes SalesVelocityService
- [ ] Factory pattern pour KeepaService avec secrets

### Phase 3: API Contracts
- [ ] Valider endpoints vs schemas
- [ ] Corriger routers pour cohérence
- [ ] Tests d'intégration par couche

### Phase 4: End-to-End Validation
- [ ] Tests unitaires par service
- [ ] Tests d'intégration API
- [ ] Performance et sécurité

## 📊 Success Criteria

- [ ] Tous modèles ↔ schémas cohérents
- [ ] Services initialisables sans erreur
- [ ] 100% tests unitaires passent
- [ ] API contracts respectés
- [ ] Architecture documentée

---

**Créé**: 2025-08-27
**Objectif**: Architecture cohérente pour frontend development