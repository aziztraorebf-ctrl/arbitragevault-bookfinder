# ⚡ MCP Keepa - Quick Start (2 minutes)

## 🎯 Le Minimum à Savoir

MCP Keepa = **Outils structurés pour Keepa API** avec **cache 10min**

---

## 🚀 Utilisation Simple

### Test Immédiat
```javascript
// Copie-colle dans Claude Code :
mcp__keepa__get_product({
  domain: 1,
  asin: "0593655036"
})
```

**Résultat** :
```json
{
  "asin": "0593655036",
  "title": "Atomic Habits...",
  "current_used_price": 899,
  "current_new_price": 1499,
  "current_bsr": 2841
}
```

---

## 💡 3 Cas d'Usage Principaux

### 1️⃣ Debug Pricing Bug (2 min)
```javascript
mcp__keepa__get_product({
  domain: 1,
  asin: "PROBLEMATIC_ASIN",
  summarizeHistory: true,
  excludeFields: ["csv"]
})
// Vois immédiatement : current_used_price, current_new_price, offers
// Diagnose rapide ✅
```

### 2️⃣ Découvrir Champ Nouveau (2 min)
```javascript
mcp__keepa__get_product({
  domain: 1,
  asin: "B08N5WRWNW"
})
// Réponse affiche TOUS les champs disponibles
// isPrime, primeExclusive, isAmazon, etc. ✅
```

### 3️⃣ Batch 100 ASINs (1 appel)
```javascript
mcp__keepa__get_product({
  domain: 1,
  asin: "ASIN1,ASIN2,...,ASIN100",
  summarizeHistory: true
})
// 1 appel au lieu de 100 ✅
```

---

## 🔥 Bénéfices

| Avant | Après |
|-------|-------|
| Debug = 30 min | Debug = 2 min ✅ |
| Champ nouveau = 1-2h | Champ nouveau = 2 min ✅ |
| 100 appels = 100 tokens | 1 batch = 100 tokens (cache gratuit) ✅ |

---

## 📚 Pour Plus de Détails

- **`docs/MCP_KEEPA_USAGE.md`** - Guide complet (4000+ words)
- **`MCP_KEEPA_TEST_COMMANDS.md`** - 7 tests (avec résultats attendus)
- **`MCP_KEEPA_IMPLEMENTATION_SUMMARY.md`** - Vue d'ensemble complète

---

## ⚠️ Règle d'Or

**Toujours utiliser ces options** pour requêtes optimales :
```javascript
{
  summarizeHistory: true,  // ✅ Résumé stats (pas données brutes)
  excludeFields: ["csv"],  // ✅ Pas CSV volumineuse
  maxOffers: 10,           // ✅ Top 10 offers
  offersCompact: true      // ✅ Format minimal
}
```

---

## 🎬 Premiers Pas

1. ✅ Configuration déjà faite (dans `.mcp.json`)
2. ✅ Test immédiatement (copie-colle `mcp__keepa__get_product` ci-dessus)
3. 📖 Consulte docs si questions

---

**Prêt à utiliser maintenant !** 🚀
