# Phase 4 - Backlog Cleanup

**Date de création**: 31 Octobre 2025
**Statut**: À traiter en priorité au démarrage Phase 4

## 🧹 Endpoints à Corriger

### 1. `/api/v1/niches/discover` - Errno 22 (Invalid argument)
**Problème**: Erreur 500 lors de l'appel
**Erreur**: `[Errno 22] Invalid argument`
**Cause probable**: Problème de chemin Windows dans le cache local ou lecture fichiers
**Action**:
- Vérifier les chemins de fichiers (utiliser `os.path.join()`)
- Tester la lecture/écriture cache sur Windows
- Valider avec vraies données Keepa

**Fichier concerné**: `backend/app/api/v1/niches.py` ou `backend/app/services/niche_templates.py`

---

### 2. `/api/v1/keepa/{asin}/metrics` - 404 Not Found
**Problème**: Endpoint retourne 404
**Cause probable**: Route renommée ou déplacée après refactor
**Action**:
- Vérifier que la route existe dans `backend/app/api/v1/keepa.py`
- Si renommée, mettre à jour tous les tests
- Documenter le nouveau chemin si changé

**Fichier concerné**: `backend/app/api/v1/keepa.py`

---

### 3. `/api/v1/products/discover` - 404 Not Found
**Problème**: Endpoint retourne 404
**Cause probable**: Route non montée ou déplacée
**Action**:
- Vérifier montage du router dans `main.py`
- Vérifier existence de `backend/app/api/v1/products.py`
- Tester avec paramètres valides

**Fichier concerné**: `backend/app/api/v1/products.py` et `backend/app/main.py`

---

### 4. Clé `hit_rate` manquante dans `/api/v1/keepa/health`
**Problème**: KeyError lors de l'accès à `data['cache']['hit_rate']`
**Cause**: Réponse JSON ne contient plus cette clé
**Action**:
- Ajouter `hit_rate` dans la réponse du health check
- Vérifier que le cache service calcule bien ce métrique
- Mettre à jour tous les tests qui utilisent cette clé

**Fichier concerné**: `backend/app/api/v1/keepa.py` (endpoint health)

**Format attendu**:
```json
{
  "tokens": {"remaining": 670},
  "status": "healthy",
  "cache": {
    "hit_rate": 70.5,
    "hits": 140,
    "misses": 60,
    "total": 200
  }
}
```

---

## 📝 Note Technique

**Table `configurations` manquante**
- Existe dans migrations mais pas créée en DB
- Actuellement: Fallback avec valeurs par défaut dans `keepa_product_finder.py`
- À décider: Recréer table OU nettoyer migrations obsolètes

---

## ✅ Validation Post-Cleanup

Une fois ces 4 points corrigés, exécuter:
```bash
cd backend
python test_e2e_simple_discovery.py
```

**Résultat attendu**:
- ✅ Aucun KeyError
- ✅ Tous endpoints retournent 200 OK
- ✅ Cache hit_rate visible
- ✅ Tokens Keepa stables (pas de consommation inutile)

---

## 🎯 Priorité Phase 4

**Ordre recommandé**:
1. Fix `hit_rate` (rapide, 5 min)
2. Fix `/products/discover` (vérifier montage router)
3. Fix `/keepa/metrics` (vérifier route)
4. Fix `/niches/discover` Errno 22 (plus complexe, chemins Windows)

**Temps estimé total**: 1-2 heures

---

*Backlog créé le 31/10/2025 - Phase 3 Day 10 Complete*