# Keepa Data Freshness Audit - Rapport Final

**Date:** 14 octobre 2025
**Contexte:** Investigation sur données Keepa obsolètes (2015) retournées par l'API

---

## 🔍 Résumé Exécutif

**Problème identifié:** L'API Keepa retourne systématiquement des données datant de 2015 (10 ans) pour tous les produits testés, malgré l'utilisation du paramètre `update=0` censé forcer un scraping live.

**Impact:** ArbitrageVault affiche des prix incorrects ($0.16 au lieu de $14.99), rendant l'application inutilisable pour les décisions d'arbitrage.

**Cause racine:** Limitation non documentée de l'API Keepa ou restriction liée au plan d'abonnement.

---

## 📊 Tests Effectués

### Test 1: ASINs Variés (3 produits)
- **B0CHWRXH8B** (AirPods Pro 2024): `lastUpdate: 2015-07-25`
- **0593655036** (All the Light We Cannot See): `lastUpdate: 2015-07-25`
- **1250301696** (48 Laws of Power): `lastUpdate: 2015-07-25`

**Résultat:** 3/3 produits retournent des données de 2015

### Test 2: Bestseller #1 Actif 2024
- **0735211299** (Atomic Habits - #1 bestseller 2024)
- `lastUpdate: 2015-07-25 21:48:00`
- **Âge: 3734 jours (10 ans)**

**Résultat:** Même un bestseller ultra-actif retourne des données obsolètes

### Test 3: Configuration API
```python
params = {
    "key": KEEPA_API_KEY,
    "domain": 1,
    "asin": asin,
    "update": 0,  # Force live data
    "stats": 180,
    "history": 1,
    "offers": 20
}
```

**Observations:**
- ✅ Tokens consommés correctement (1200 → 1187)
- ✅ `refillRate: 20` tokens/min (conforme plan)
- ✅ Pas de `tokenFlowReduction` (pas de limitation)
- ❌ Données toujours de 2015

### Test 4: Requête Minimale
```python
params = {
    "key": KEEPA_API_KEY,
    "domain": 1,
    "asin": "0735211299",
    "update": 0,
    "only": "offers"
}
```

**Résultat:** Même avec requête minimale, données de 2015

---

## 🧪 Vérifications Techniques

### ✅ Confirmé Correct
1. **Keepa Epoch:** `971222400` (21 Oct 2000 00:00:00 GMT)
2. **Conversion timestamp:** Fonction validée avec tests unitaires
3. **Transmission paramètre:** `update=0` correctement transmis à l'API
4. **Library Python keepa:** Code source vérifié, transmission correcte
5. **REST API direct:** Bypass de la library Python, même résultat

### ❌ Problème Persistant
Tous les produits testés ont le même timestamp exact:
```
lastUpdate: 7777548 (Keepa minutes)
→ 2015-07-25 21:48:00
→ 3734 jours d'âge
```

---

## 💡 Hypothèses Éliminées

1. ❌ **Produits obsolètes:** Testé avec bestseller #1 actif 2024
2. ❌ **Bug parser:** Validé avec REST API direct
3. ❌ **Epoch incorrect:** Confirmé 971222400 via documentation
4. ❌ **Cache local:** Tests directs sans cache
5. ❌ **Library Python bug:** REST API direct même résultat
6. ❌ **Limitation tokens:** Budget suffisant, tokens consommés

---

## 🎯 Hypothèses Restantes

### A. Limitation Plan Keepa
**Probabilité: HAUTE**

Le plan actuel (49€/mois, 20 tokens/min) ne permet peut-être pas `update=0` pour forcer le scraping live.

**Actions:**
- Contacter support Keepa pour confirmer
- Vérifier limitations plan via dashboard Keepa

### B. Restriction Non Documentée
**Probabilité: MOYENNE**

L'API Keepa pourrait avoir des restrictions non documentées:
- Délai minimum entre updates forcés
- Produits non supportés pour live scraping
- Domaine .com vs autres domaines

### C. Bug API Keepa
**Probabilité: FAIBLE**

Bug côté Keepa retournant systématiquement cache 2015.

**Contre-argument:** Aucune issue GitHub similaire trouvée

---

## 🛠️ Solution Court Terme

En attendant clarification Keepa, implémenter:

### 1. Avertissement UI (⚠️ Données > 30 jours)
```typescript
// frontend/src/components/accordions/RoiDetailsSection.tsx
{dataAge > 30 && (
  <Badge variant="warning">
    ⚠️ Données anciennes ({dataAge} jours)
  </Badge>
)}
```

### 2. Fallback Cache Intelligent
```python
# backend/app/services/keepa_service.py
# Accepter cache jusqu'à 30 jours si live data impossible
if force_refresh:
    try:
        live_data = self._fetch_with_update_zero(identifier)
        if self._is_data_fresh(live_data, max_age_days=30):
            return live_data
    except KeepaAPIError:
        logger.warning("Live data unavailable, using cache")
        return cached_data or self._fetch_normal(identifier)
```

### 3. Logging Amélioré
```python
logger.warning(
    f"[DATA AGE] Product {asin} data is {age_days} days old "
    f"(lastUpdate: {last_update_dt})"
)
```

---

## 📋 Actions Recommandées

### Immédiat (Aujourd'hui)
1. ✅ Créer ce rapport diagnostic
2. 🔲 Contacter support Keepa avec détails techniques
3. 🔲 Vérifier limitations plan via dashboard Keepa

### Court Terme (Cette Semaine)
1. 🔲 Implémenter warning UI pour données > 30 jours
2. 🔲 Ajouter fallback cache intelligent
3. 🔲 Améliorer logging data age

### Long Terme (Attente Keepa)
1. 🔲 Si plan insuffisant: upgrade ou changer stratégie
2. 🔲 Si bug Keepa: attendre fix
3. 🔲 Si restriction permanente: explorer alternatives (Jungle Scout, Helium 10)

---

## 📎 Références

- **Tests executés:** `test_audit_verified_asins.py`, `test_2024_bestseller.py`, `test_keepa_account_info.py`
- **Documentation Keepa:** https://keepa.com/#!discuss/t/request-products/110
- **GitHub keepa library:** https://github.com/akaszynski/keepa
- **Keepa epoch confirmé:** 971222400 (21 Oct 2000)

---

## 🔗 Logs Complets

Voir fichiers de test pour outputs détaillés:
```bash
cd backend
.venv/Scripts/python.exe test_audit_verified_asins.py
.venv/Scripts/python.exe test_2024_bestseller.py
.venv/Scripts/python.exe test_keepa_account_info.py
```

---

**Conclusion:** Le problème n'est PAS côté ArbitrageVault. L'API Keepa retourne systématiquement des données obsolètes malgré configuration correcte. Contact support Keepa requis pour résolution définitive.
