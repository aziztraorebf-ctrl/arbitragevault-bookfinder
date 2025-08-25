# 📦 Stock Estimate API v1.0

Simple et robuste estimation du stock disponible pour optimiser les décisions d'achat.

## 🎯 **Objectif**
Décider en **2 secondes** si un deal est **scalable** (acheter 2-3 unités) ou juste un **one-off**.

## 🚀 **Endpoints**

### GET `/api/v1/products/{asin}/stock-estimate`

Obtient l'estimation de stock pour un ASIN donné.

**Paramètres :**
- `asin` (path) : Identifiant Amazon ASIN
- `price_target` (query, optionnel) : Prix cible pour filtrer les offres pertinentes

**Réponse 200 :**
```json
{
  "asin": "B00EXEMPLE",
  "units_available_estimate": 3,
  "offers_fba": 2,
  "offers_mfn": 5,
  "source": "fresh",
  "updated_at": "2025-01-17T20:14:12Z",
  "ttl": 86399
}
```

**Exemples d'appel :**
```bash
# Simple
curl "http://localhost:8000/api/v1/products/B00EXEMPLE/stock-estimate"

# Avec prix cible
curl "http://localhost:8000/api/v1/products/B00EXEMPLE/stock-estimate?price_target=15.50"
```

### GET `/api/v1/products/stock-estimate/health`

Health check du service.

**Réponse :**
```json
{
  "service": "stock_estimate",
  "status": "healthy",
  "version": "v1.0.0"
}
```

## 🧠 **Logique d'Estimation (v1)**

### Heuristique Ultra-Simple
```python
# Compter les offres FBA dans la fourchette de prix
fba_offers_in_range = count_fba_offers(offers, price_target ± 15%)

# Estimation = min(10, max(1 si FBA > 0, fba_count))
units_estimate = min(10, max(1 if fba_count > 0 else 0, fba_count))
```

### Cache Strategy
- **TTL** : 24 heures par défaut
- **Cache-First** : Vérification cache avant appel Keepa
- **Source** : `"cache"` | `"fresh"` | `"error"`

### Configuration
```json
{
  "ttl_hours": 24,
  "price_band_pct": 0.15,
  "max_estimate": 10,
  "timeout_seconds": 4
}
```

## 📋 **Cases d'Usage**

### 1. **Validation Rapide Post-RUN**
Après avoir trouvé des opportunités, vérifier rapidement la scalabilité :
```bash
curl "http://localhost:8000/api/v1/products/B07ABC123/stock-estimate"
# → units_available_estimate: 5 = Scalable ✅
# → units_available_estimate: 1 = One-off ⚠️
```

### 2. **Priorisation avec Prix Cible**
Filtrer selon votre prix d'achat maximal :
```bash
curl "http://localhost:8000/api/v1/products/B07ABC123/stock-estimate?price_target=12.99"
# → Seules les offres dans [11.04, 14.94] comptent
```

### 3. **Cache Intelligent**
```bash
# Premier appel = Fresh data
curl "http://localhost:8000/api/v1/products/B07ABC123/stock-estimate"
# → "source": "fresh"

# Dans les 24h suivantes = Cache
curl "http://localhost:8000/api/v1/products/B07ABC123/stock-estimate"  
# → "source": "cache"
```

## 🔍 **Interprétation des Résultats**

| `units_available_estimate` | Signification | Action Recommandée |
|---------------------------|---------------|-------------------|
| **0** | Aucune offre FBA pertinente | ❌ Passer |
| **1** | One-off, stock limité | ⚠️ Tester 1 unité |
| **2-5** | Stock modéré, scalable | ✅ Acheter 2-3 unités |
| **6-10** | Stock élevé, très scalable | 🚀 Acheter jusqu'à 5+ unités |

## ⚡ **Performance**

- **Cache Hit** : ~50ms
- **Cache Miss** : ~2-4 secondes (appel Keepa)
- **Rate Limit** : 60 req/min (configurable)
- **Timeout** : 4 secondes max

## 🔒 **Gestion d'Erreurs**

| Code | Cause | Action |
|------|-------|--------|
| **200** | Succès | Utiliser estimation |
| **400** | ASIN invalide | Corriger format ASIN |
| **504** | Timeout Keepa + pas de cache | Réessayer plus tard |
| **500** | Erreur serveur | Contacter support |

## 🧪 **Tests Validés**

✅ **Logique Core** : Calculs d'estimation, filtrage prix, plafonnement  
✅ **Cache** : TTL, expiration, to_dict conversion  
✅ **Endpoints** : Validation ASIN, paramètres, gestion erreurs  
✅ **Intégration** : Flow complet avec données mockées  

## 🎯 **Intégration Frontend**

### Déclencher l'appel après RUN :
```javascript
// Au clic sur une opportunité
const checkStock = async (asin, targetPrice) => {
  const response = await fetch(
    `/api/v1/products/${asin}/stock-estimate?price_target=${targetPrice}`
  );
  const data = await response.json();
  
  if (data.units_available_estimate >= 3) {
    showScalableIcon(data.units_available_estimate);
  }
}
```

### Batch checking pour top opportunities :
```javascript
// Pour les 5 meilleures opportunités
const topAsins = ['B07ABC123', 'B07DEF456', ...];
const stockPromises = topAsins.map(asin => 
  fetch(`/api/v1/products/${asin}/stock-estimate`)
);
```

## 📈 **Roadmap v2 (Futur)**

- **POST `/stock-estimate:batch`** : Estimation en lot
- **Heuristique avancée** : Bonus pour prix serrés, patterns saisonniers
- **Métriques** : Précision des estimations, cache hit ratio
- **Configuration par utilisateur** : TTL personnalisé, seuils ajustables

---
**Version**: v1.0.0  
**Dernière mise à jour**: Janvier 2025