# MCP Keepa Server - Guide d'Utilisation pour ArbitrageVault

## 🚀 Installation & Configuration

### Statut
✅ **MCP Keepa server est maintenant configuré dans `.mcp.json`**

```json
{
  "mcpServers": {
    "keepa": {
      "command": "npx",
      "args": ["-y", "keepa-mcp-server@latest"],
      "env": {
        "KEEPA_API_KEY": "YOUR_KEY_HERE",
        "KEEPA_BASE_URL": "https://api.keepa.com"
      }
    }
  }
}
```

### Vérifier que le serveur fonctionne
```bash
# Dans Claude Code, utilise directement les outils MCP :
mcp__keepa__get_product({ domain: 1, asin: "0593655036" })
```

---

## 🔥 CAS D'USAGE PRINCIPAUX

### 1. **Test ASIN Simple (Avec Cache)**

**Objectif** : Récupérer données produit avec bénéfice du cache

```javascript
// Premier appel (consomme 1 token Keepa)
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  summarizeHistory: true
})

// Appel dans les 10 minutes suivantes (0 token - CACHE HIT!)
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  summarizeHistory: true
})
```

**Données retournées** :
```json
{
  "asin": "0593655036",
  "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits...",
  "current_price": 1499,
  "current_used_price": 899,
  "current_new_price": 1499,
  "current_bsr": 2841,
  "csv": [...],
  "csvSummary": {
    "usedPrice": { "min": 799, "max": 1099, "avg": 899 },
    "newPrice": { "min": 1299, "max": 1999, "avg": 1599 }
  }
}
```

---

### 2. **Debug Pricing USED vs NEW**

**Objectif** : Analyser rapidement structure USED/NEW pour un bug frontend

```javascript
mcp__keepa__get_product({
  domain: 1,
  asin: "PROBLEMATIC_ASIN",
  summarizeHistory: true,
  excludeFields: ["csv"],  // Ignorer données volumineuses
  offers: 10,
  maxOffers: 5,
  offersCompact: true
})
```

**Sortie** :
```json
{
  "asin": "PROBLEMATIC_ASIN",
  "title": "...",
  "current_used_price": 899,  // ✅ USED disponible
  "current_new_price": null,  // ❌ NEW pas disponible
  "current_bsr": 125000,
  "offers": [
    {
      "merchant": "FBA",
      "price": 899,
      "condition": "Used",
      "quantity": 15
    },
    ...
  ]
}
```

**Diagnostic rapide** : Produit n'a PAS de NEW offers → Backend OK, c'est normal

---

### 3. **Batch Request - 100 ASINs Simultanés**

**Objectif** : Analyser multiple products avec 1 seul appel

```javascript
const asins = "0593655036,B08N5WRWNW,0134685997,..."; // Jusqu'à 100

mcp__keepa__get_product({
  domain: 1,
  asin: asins,
  summarizeHistory: true,
  maxOffers: 5,
  excludeFields: ["csv"]  // Économiser taille réponse
})
```

**Coûts** :
- **Sans MCP** : 100 appels = 100 tokens
- **Avec MCP** : 1 appel batch = 100 tokens (MAIS réutilisable 10min gratuitement)

---

### 4. **Découverte Champs - Ajouter une Feature**

**Objectif** : Trouver les champs disponibles pour nouvelle feature

**Exemple** : Ajouter "Prime Eligibility"

```javascript
// Requête sans filtrage pour voir TOUS les champs
mcp__keepa__get_product({
  domain: 1,
  asin: "B08N5WRWNW",
  includeHistory: false,
  summarizeHistory: false,
  excludeFields: []  // Voir tous les champs
})
```

**Réponse montre** :
```json
{
  "asin": "B08N5WRWNW",
  "title": "...",
  "current_price": 2999,
  "isPrime": true,          // ✅ Champ Prime trouvé !
  "primeExclusive": false,
  "primeIncentivized": true,
  "isAMAZON": true,
  "isSMART": true,
  "availabilityAmazon": 0,
  "isEligibleForTradeIn": true,
  "isLightningDeal": false,
  "isRecent": true,
  "csv": [...],
  "offers": [...]
}
```

**Résultat** : Trouve immédiatement les champs Prime → Plus besoin de docs!

---

### 5. **Générer Chart Prix/BSR (BONUS)**

**Objectif** : Créer graphique prix et BSR automatiquement

```javascript
mcp__keepa__product_chart({
  asin: "0593655036",
  domain: 1,
  salesrank: 1,  // Inclure BSR
  bb: 1,         // BuyBox price
  fba: 1,        // FBA price
  fbm: 0,        // Sans FBM
  range: 90,     // 90 jours
  width: 800,
  height: 600
})
```

**Sortie** :
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",  // PNG base64
  "metadata": {
    "domain": "amazon.com",
    "asin": "0593655036",
    "dataTypes": ["salesrank", "buybox", "fba"],
    "range": 90
  }
}
```

**Usage** :
```html
<!-- Directement dans frontend -->
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." />
```

---

## 📊 Monitoring Performance

### Voir Métriques Cache

```javascript
mcp__keepa__get_metrics()
```

**Réponse** :
```json
{
  "requests": {
    "total": 250,
    "successful": 245,
    "failed": 5,
    "cached": 180
  },
  "cache": {
    "hits": 180,
    "misses": 65,
    "hitRatio": 0.735,  // 73.5% cache hits !
    "size": 45
  },
  "performance": {
    "averageResponseTime": 245,
    "errorRate": 0.02,
    "cacheHitRatio": 0.735
  }
}
```

**Interprétation** :
- ✅ 73.5% cache hits = Excellent!
- ✅ 245ms réponse moyenne = Bon
- ✅ 2% erreur rate = Acceptable

---

## 🎯 Workflow Recommandé

### Pour les Tests E2E

```javascript
// ✅ BON - Économise tokens
for (let i = 0; i < 5; i++) {
  // Teste backend avec cache MCP
  mcp__keepa__get_product({
    domain: 1,
    asin: "0593655036",
    summarizeHistory: true
  })
  // Appels 2-5 = 0 tokens (cache hit)
}

// ❌ MAUVAIS - Gaspille tokens
for (let i = 0; i < 5; i++) {
  await curl("https://api.keepa.com/product?asin=0593655036")
  // Chaque appel = 1 token, total 5 tokens
}
```

### Pour le Debug

```javascript
// 1. Reproduire le bug
const result = await backend.analyzeProduct("PROBLEMATIC_ASIN")
// Problème constaté

// 2. Debugger avec MCP (instantané)
mcp__keepa__get_product({
  domain: 1,
  asin: "PROBLEMATIC_ASIN",
  summarizeHistory: true
})
// Analyser réponse → Découvrir la cause

// 3. Comprendre la structure
// Comparer avec réponse working ASIN
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036",
  summarizeHistory: true
})
// Identifier différence
```

---

## 🔧 Options Filtrage (Important!)

### summarizeHistory
```javascript
// ✅ RECOMMANDÉ pour la plupart des cas
summarizeHistory: true
// Retourne : { min, max, avg } au lieu de [0, 100, 200, 150, ...]
// Réduit taille réponse de 80%

// ❌ Seulement si tu as VRAIMENT besoin des données brutes
includeHistory: true
// Retourne : Array complet [0, 100, 200, 150, ...]
// Très volumineuse
```

### maxOffers
```javascript
// ✅ Pour most use cases
maxOffers: 10
// Retourne top 10 offers seulement

// ❌ À éviter
offers: 50
// Demande beaucoup de data, risque truncation
```

### offersCompact
```javascript
// ✅ Pour affichage UI
offersCompact: true
// Format minimal { merchant, price, condition }

// ❌ Pour analyse détaillée
offersCompact: false
// Format complet { merchant, price, condition, quantity, ... }
```

---

## ⚠️ Limites & Gotchas

### 1. **Limite 1MB Réponse MCP**
```javascript
// ❌ RISK: Peut dépasser 1MB
get_product({
  domain: 1,
  asin: "B07CYVDSF4",
  offers: 100,           // Trop !
  includeHistory: true,  // Trop !
  stats: 365             // Trop !
})

// ✅ SAFE: Bien filtré
get_product({
  domain: 1,
  asin: "B07CYVDSF4",
  maxOffers: 10,
  summarizeHistory: true,
  excludeFields: ["csv"]
})
```

### 2. **Cache TTL 10 minutes**
```javascript
// Cache expires après 10 minutes
// Réappelle le même produit après 10min = Nouveau token utilisé

// Planification optimale :
// - Tests intensifs dans 10min window
// - Réutiliser résultats en mémoire après cache expiry
```

### 3. **Rate Limiting Keepa API**
```javascript
// MCP respecte rate limiting Keepa
// Mais ne limite PAS automatiquement CLI calls
// À toi de contrôler : pas 1000 ASINs en parallèle !

// ✅ BON
Promise.all([
  get_product({...asin1}),
  get_product({...asin2}),
  get_product({...asin3})
])

// ❌ MAUVAIS
for (let asin of 1000_asins) {
  get_product({...asin}) // Trop rapide !
}
```

---

## 📚 Ressources

- **Docs MCP Keepa** : C:\keepa mcp server\Keepa MCP Server README.md
- **Changelog** : C:\keepa mcp server\Keepa MCP Server CHANGELONG.md
- **Installation Guide** : C:\keepa mcp server\Keepa MCP Server INSTALL.md

---

## ✅ Checklist Utilisation

- [ ] MCP Keepa configuré dans `.mcp.json`
- [ ] Premier appel `get_product` testé
- [ ] Cache hit observé (2ème appel instantané)
- [ ] Documentation partagée avec équipe
- [ ] Best practices de filtrage compris

---

**Dernière mise à jour** : Octobre 2025
**Statut** : ✅ Production Ready

