# MCP Keepa - Commandes de Test Pratiques

## 🎯 Tests Immédiats à Faire

### Test #1 : Produit Simple (2 secondes)
```javascript
// Teste : Récupération basique
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036"  // Atomic Habits
})

// Résultat attendu :
// {
//   asin: "0593655036",
//   title: "Atomic Habits: An Easy & Proven Way...",
//   current_price: 1499,
//   current_used_price: 899,
//   current_bsr: 2841
// }
```

**À observer** :
- ✅ Réponse immédiate
- ✅ Champs USED/NEW présents
- ✅ BSR visible

---

### Test #2 : Vérifier le Cache (30 secondes)
```javascript
// Première fois - NOTE LE TIMESTAMP
console.log("START:", new Date().toISOString())
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  summarizeHistory: true
})
// Première réponse : ~200-500ms

// Attends 1 seconde, puis réappelle
console.log("CACHE TEST:", new Date().toISOString())
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  summarizeHistory: true
})
// Deuxième réponse : <100ms (cache hit!)
```

**À observer** :
- 2ème appel est **BEAUCOUP** plus rapide
- Cela démontre le cache fonctionne

---

### Test #3 : Comparer Sommaire vs Détail (1 minute)
```javascript
// VERSION LÉGÈRE (recommandée)
mcp__keepa__get_product({
  domain: 1,
  asin: "B08N5WRWNW",
  summarizeHistory: true,  // ✅ Résumé stats
  excludeFields: ["csv"]   // ✅ Ignore données brutes
})

// VERSION LOURD (pour data science)
mcp__keepa__get_product({
  domain: 1,
  asin: "B08N5WRWNW",
  includeHistory: true     // ❌ DONNÉES VOLUMINEUSES
})
```

**Comparaison** :
- Version légère : ~50KB réponse
- Version lourd : ~500KB réponse
- Économie : **10x plus petite !**

---

### Test #4 : Batch 3 ASINs (10 secondes)
```javascript
// Test : Batch request
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036,B08N5WRWNW,0134685997",  // 3 ASINs
  summarizeHistory: true,
  maxOffers: 5
})

// Résultat : Array de 3 produits
// [
//   { asin: "0593655036", ... },
//   { asin: "B08N5WRWNW", ... },
//   { asin: "0134685997", ... }
// ]
```

**À observer** :
- ✅ Tous 3 produits retournés
- ✅ Structure cohérente
- ✅ 1 seul appel API (vs 3 séparés)

---

### Test #5 : Offers (Vendeurs) (20 secondes)
```javascript
// Teste : Structure offers USED vs NEW
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  offers: 20,
  maxOffers: 10,           // Limiter à top 10
  offersCompact: true,     // Format minimal
  summarizeHistory: true
})

// Résultat :
// {
//   asin: "0593655036",
//   offers: [
//     {
//       merchant: "Amazon.com",
//       price: 899,
//       condition: "Used",
//       quantity: 25,
//       isAmazon: true,
//       isFBA: true
//     },
//     {
//       merchant: "FastShip",
//       price: 799,
//       condition: "Used",
//       isFBA: false
//     },
//     ...
//   ]
// }
```

**À observer** :
- ✅ USED offers visibles avec prix
- ✅ Merchant info (Amazon vs 3P)
- ✅ FBA flag visible

---

### Test #6 : Metrics (Cache Stats) (5 secondes)
```javascript
// Teste : Voir performance cache
mcp__keepa__get_metrics()

// Résultat :
// {
//   cache: {
//     hits: 3,
//     misses: 2,
//     hitRatio: 0.6  // 60% cache hits
//   },
//   requests: {
//     total: 5,
//     cached: 3
//   }
// }
```

**À observer** :
- ✅ Cache hits comptés
- ✅ Hit ratio visible
- ✅ Performance statistiques

---

### Test #7 : Chart Graphique (10 secondes)
```javascript
// Teste : Génération graphique
mcp__keepa__product_chart({
  asin: "0593655036",
  domain: 1,
  salesrank: 1,    // Inclure BSR
  bb: 1,           // BuyBox
  range: 90,       // 90 jours
  width: 800,
  height: 600
})

// Résultat :
// {
//   image: "iVBORw0KGgoAAAANSUhEUgAA...",  // PNG base64
//   metadata: {
//     asin: "0593655036",
//     dataTypes: ["salesrank", "buybox"]
//   }
// }
```

**À observer** :
- ✅ Image base64 retournée
- ✅ Format PNG valide
- ✅ Prêt à afficher dans HTML

---

## 🧪 Tests d'Erreur (Gestion Gracieuse)

### Test Error #1 : ASIN Invalide
```javascript
// Teste : Format invalide
mcp__keepa__get_product({
  domain: 1,
  asin: "INVALID"  // Pas 10 caractères
})

// Résultat attendu :
// Erreur : ValidationError - ASIN must be 10 characters
```

---

### Test Error #2 : Produit Inexistant
```javascript
// Teste : Produit absent Keepa
mcp__keepa__get_product({
  domain: 1,
  asin: "0000000000"  // Format valide mais produit ghost
})

// Résultat attendu :
// null (produit pas en DB Keepa)
```

---

## 📊 Scénario Complet : Debug Pricing Bug

**Contexte** : Frontend affiche "USED price = null" pour un produit

### Étape 1 : Appeler Keepa pour le produit
```javascript
// Identifier problématique ASIN
const problematicAsin = "B07CYVDSF4"

mcp__keepa__get_product({
  domain: 1,
  asin: problematicAsin,
  summarizeHistory: true,
  excludeFields: ["csv"],
  offers: 10
})
```

### Étape 2 : Analyser Réponse
```json
{
  "asin": "B07CYVDSF4",
  "current_used_price": null,      // ❌ AH! Pas de USED
  "current_new_price": 2999,       // ✅ NEW existe
  "current_bsr": 45000,
  "offers": [
    {
      "merchant": "Amazon.com",
      "price": 2999,
      "condition": "New"
    }
  ]
  // ❌ Pas d'offers USED
}
```

### Étape 3 : Diagnostic
```
✅ Conclusion : Backend code OK
❌ Problème : Ce produit n'a PAS de USED listings
✅ Solution : Frontend doit afficher "N/A" pour USED gracieusement
```

### Résultat
- **Temps debug** : ~2 minutes (vs 30min manual)
- **Certitude** : 100% (données directes Keepa)

---

## 🚀 Optimisation Recommandée

### Pour Tests Rapides
```javascript
// Toujours utiliser ces options
mcp__keepa__get_product({
  domain: 1,
  asin: "YOUR_ASIN",
  summarizeHistory: true,    // ✅ Résumé stats
  excludeFields: ["csv"],    // ✅ Pas données brutes
  maxOffers: 10,             // ✅ Top 10 offers
  offersCompact: true        // ✅ Format minimal
})

// Économise : ~80% bande passante + plus rapide
```

### Pour Tests Parallèles
```javascript
// Batch jusqu'à 100 ASINs
const asins = "ASIN1,ASIN2,...,ASIN100"  // Jusqu'à 100

mcp__keepa__get_product({
  domain: 1,
  asin: asins,
  summarizeHistory: true
})

// Résultat : 1 appel au lieu de 100!
```

---

## ✅ Checklist Test Complet

- [ ] Test #1 : Produit simple fonctionné
- [ ] Test #2 : Cache hit observé (2ème appel rapide)
- [ ] Test #3 : Filtrage réduit taille 10x
- [ ] Test #4 : Batch 3 ASINs fonctionne
- [ ] Test #5 : Offers USED/NEW visibles
- [ ] Test #6 : Metrics affiche cache hits
- [ ] Test #7 : Chart graphique généré
- [ ] Scenario debug : ASIN problématique diagnosed

---

## 💡 Après Tests

Une fois tous les tests OK, tu auras confirmé que :

✅ MCP Keepa est **100% opérationnel**
✅ Cache économise **15-20 tokens/heure**
✅ Debug est **10x plus rapide**
✅ Données sont **structurées et typées**
✅ Performance est **excellente** (<100ms avec cache)

**Prochaines étapes** :
1. Documenter patterns pour équipe
2. Intégrer dans workflow tests E2E
3. Utiliser pour validation features
4. Monitor cache hits avec metrics

---

**Tests créés** : Octobre 2025
**Status** : Ready to run!

