# 🧪 Guide de Tests - Fix Prix & Timestamp Keepa

**Date** : 16 Octobre 2025
**Commits** :
- `9347e14` - Fix timestamp conversion (2015 → 2025)
- `0595255` - Fix extraction prix ($0.11 → $14.00)

**Statut Déploiement** : ✅ **EN PRODUCTION**

---

## 🎯 Qu'est-ce qui a été corrigé ?

### Bug #1 : Timestamps Incorrects
- ❌ **Avant** : Dates affichées en 2015 (ex: "2015-07-25")
- ✅ **Après** : Dates correctes en 2025 (ex: "2025-10-15")

### Bug #2 : Prix Incorrects
- ❌ **Avant** : Prix $0.11 - $0.16 (lecture depuis historique)
- ✅ **Après** : Prix réels $14.00 - $17.00 (lecture depuis snapshot actuel)

---

## 📋 ASINs de Test Recommandés

### 1. **ASIN : 0593655036** (Anxious Generation - Bestseller)
**Catégorie** : Livres / Psychology
**Prix attendu** : ~$14.00 - $17.00
**BSR attendu** : < 100 (très populaire)

**Ce que tu devrais voir** :
```json
{
  "current_price": 16.98,      // ✅ Entre $14-$20 (pas $0.16!)
  "current_bsr": 69,            // ✅ Très bas = bestseller
  "roi": {
    "sell_price": "16.98",      // ✅ Prix réel
    "roi_percentage": "30.00"   // ✅ ROI calculé avec vrai prix
  }
}
```

---

### 2. **ASIN : 0735211299** (Atomic Habits - Classic)
**Catégorie** : Livres / Self-Help
**Prix attendu** : ~$11.00 - $15.00
**BSR attendu** : < 500 (très populaire)

**Ce que tu devrais voir** :
```json
{
  "current_price": 14.00,       // ✅ ~$14 (pas $0.11!)
  "current_bsr": < 500,         // ✅ Populaire
  "title": "Atomic Habits"
}
```

---

### 3. **ASIN : B0BH3VT7WY** (AirPods Pro - Électronique)
**Catégorie** : Électronique
**Prix attendu** : ~$200 - $250
**BSR attendu** : Variable

**Ce que tu devrais voir** :
```json
{
  "current_price": 249.00,      // ✅ ~$200+ (pas $0.24!)
  "roi": {
    "category_used": "electronics"  // ✅ Fees électronique
  }
}
```

---

## 🧪 Tests à Effectuer

### Test #1 : Validation Prix Production (CRITIQUE)

**Commande** :
```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest" \
  -H "Content-Type: application/json" \
  -d '{"identifiers":["0593655036"],"strategy":"balanced"}'
```

**✅ Critères de Réussite** :
1. `current_price` entre $14.00 et $20.00 (PAS $0.16 !)
2. `current_bsr` < 100 (bestseller)
3. `roi_percentage` calculé avec vrai prix
4. `sell_price` == `current_price`

**❌ Échec si** :
- `current_price` < $1.00 → Bug prix toujours présent
- `current_bsr` > 100000 → Bug BSR ou ASIN invalide

---

### Test #2 : Timestamp Freshness (CRITIQUE)

**Objectif** : Vérifier que les timestamps montrent 2025, pas 2015

**Commande** :
```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest" \
  -H "Content-Type: application/json" \
  -d '{"identifiers":["0735211299"],"strategy":"balanced"}'
```

**✅ Ce que tu devrais voir dans la response** :
- Pas de champ `last_updated_at` visible directement (backend interne)
- Mais `current_price` et `current_bsr` doivent être **réalistes**

**Vérification Indirecte** :
- Si prix = $14.00 → Timestamp correct (données fraîches)
- Si prix = $0.11 → Timestamp incorrect (données 2015)

---

### Test #3 : Multiple ASINs Batch

**Commande** :
```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "identifiers": ["0593655036", "0735211299"],
    "strategy": "balanced"
  }'
```

**✅ Critères de Réussite** :
1. Les DEUX produits ont des prix réalistes (> $10)
2. `processed: 2, successful: 2, failed: 0`
3. ROI calculés pour chaque produit
4. BSR < 1000 pour les deux (bestsellers)

---

### Test #4 : Frontend Integration (SI DISPONIBLE)

**Étapes** :
1. Ouvre le frontend ArbitrageVault
2. Cherche ASIN : `0593655036`
3. Vérifie la card produit

**✅ Ce que tu devrais voir** :
- **Prix** : ~$16.98 (pas $0.16)
- **BSR** : ~69 (pas 696969)
- **ROI Badge** : "30%" (calculé avec vrai prix)
- **Profit** : ~$1.91 (calculé avec vrai prix)

**❌ Échec si** :
- Prix affiché < $1.00
- ROI > 1000% (indique prix faux dans calcul)
- Badge "Données obsolètes" affiché

---

## 🔍 Debugging - Si ça ne marche pas

### Problème : Prix toujours < $1.00

**Diagnostic** :
```bash
# Vérifier déploiement Render
curl https://arbitragevault-backend-v2.onrender.com/health
```

**Solutions** :
1. Vérifier que commits sont sur `main` : `git log --oneline -3`
2. Attendre 2-3 minutes (déploiement Render)
3. Forcer redéploiement Render dashboard

---

### Problème : API timeout

**Cause** : Keepa API lent (normal première requête)

**Solution** :
- Attendre 30-60 secondes
- Réessayer avec même ASIN (sera en cache)

---

### Problème : "Données obsolètes" affiché

**Diagnostic** :
- Regarde console frontend pour timestamp
- Si timestamp montre 2015 → Bug timestamp pas déployé

**Solution** :
- Vérifier commit `9347e14` sur `main`
- Clear cache Render

---

## 📊 Résultats Attendus - Récapitulatif

| ASIN | Titre | Prix Attendu | BSR Attendu | ROI Attendu |
|------|-------|--------------|-------------|-------------|
| 0593655036 | Anxious Generation | $14-$17 | < 100 | 20-35% |
| 0735211299 | Atomic Habits | $11-$15 | < 500 | 25-40% |
| B0BH3VT7WY | AirPods Pro | $200-$250 | Variable | 5-15% |

---

## ✅ Checklist Validation Finale

Avant de déclarer le fix validé, assure-toi que :

- [ ] **Prix réalistes** : Tous les ASINs montrent prix > $10 pour livres
- [ ] **BSR cohérent** : Bestsellers ont BSR < 1000
- [ ] **ROI calculé** : ROI entre 5% et 50% (pas 500%!)
- [ ] **Pas de $0.16** : Aucun prix suspect < $1.00
- [ ] **API répond** : Temps réponse < 20s
- [ ] **Batch fonctionne** : Multiple ASINs processés correctement

---

## 🎯 Commande Rapide - All-in-One Test

```bash
# Test complet avec 2 ASINs
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "identifiers": ["0593655036", "0735211299"],
    "strategy": "balanced"
  }' | python -m json.tool
```

**Résultat attendu** :
```json
{
  "processed": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "asin": "0593655036",
      "current_price": 16.98,    // ✅ $16.98 (pas $0.16)
      "current_bsr": 69,          // ✅ Bestseller
      "roi": {
        "roi_percentage": "30.00" // ✅ ROI réaliste
      }
    },
    {
      "asin": "0735211299",
      "current_price": 14.00,     // ✅ $14.00 (pas $0.14)
      "current_bsr": 200,         // ✅ Bestseller
      "roi": {
        "roi_percentage": "35.00" // ✅ ROI réaliste
      }
    }
  ]
}
```

---

## 📞 Support

Si tu vois toujours des prix $0.16 ou dates 2015 :

1. Partage le output JSON complet
2. Vérifie `git log` pour confirmer commits
3. Check Render dashboard pour déploiement status

---

**Dernière mise à jour** : 16 Octobre 2025
**Version** : Phase 2.5b - Keepa Epoch & Prix Fix
**Status** : ✅ PRODUCTION READY
