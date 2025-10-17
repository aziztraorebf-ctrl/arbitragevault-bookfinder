# 📋 Plan d'Implémentation - Affichage Prix USED vs NEW

**Date** : 16 Octobre 2025
**Objectif** : Afficher prix USED en priorité pour stratégie FBA arbitrage
**Design** : Option 1 (USED Focus) - validé par utilisateur

---

## 🎯 Résumé des Changes

### Backend Changes
1. ✅ Parser extrait déjà `current_used_price` (ligne 588 keepa_parser_v2.py)
2. ➡️ Modifier `AnalysisResult` schema pour inclure `pricing` structure
3. ➡️ Calculer ROI séparément pour USED et NEW
4. ➡️ Retourner les 2 prix dans response API

### Frontend Changes
5. ➡️ Modifier card pour afficher USED en priorité
6. ➡️ Ajouter colonne BSR dans tableau
7. ➡️ Tester avec vrais ASINs

---

## 📝 Détail des Modifications

### 1. Modifier Schema API Response (Backend)

**Fichier** : `backend/app/api/v1/routers/keepa.py`

**Change `AnalysisResult` model** :

```python
class PricingDetail(BaseModel):
    """Prix pour une condition (NEW ou USED)"""
    current_price: Optional[float] = None
    target_buy_price: float
    roi_percentage: Optional[float] = None
    net_profit: Optional[float] = None
    available: bool
    recommended: bool

class AnalysisResult(BaseModel):
    """Complete analysis result for a product."""
    asin: str
    title: Optional[str]
    current_price: Optional[float]  # Sell price (Amazon NEW)
    current_bsr: Optional[int]

    # ✨ NEW: Pricing breakdown USED vs NEW
    pricing: Dict[str, PricingDetail] = Field(
        default={},
        description="Prix séparés: 'used' et 'new'"
    )

    # Existing fields...
    roi: Dict[str, Any]
    velocity: Dict[str, Any]
    ...
```

**Exemple Response** :

```json
{
  "asin": "0593655036",
  "title": "The Anxious Generation",
  "current_price": 16.98,
  "current_bsr": 67,

  "pricing": {
    "used": {
      "current_price": 9.50,
      "target_buy_price": 6.77,
      "roi_percentage": 19.5,
      "net_profit": 1.85,
      "available": true,
      "recommended": true
    },
    "new": {
      "current_price": null,
      "target_buy_price": 6.77,
      "roi_percentage": null,
      "net_profit": null,
      "available": false,
      "recommended": false
    }
  },

  "roi": {...},
  "velocity": {...}
}
```

---

### 2. Calculer ROI pour USED et NEW (Backend)

**Fichier** : `backend/app/api/v1/routers/keepa.py`

**Modifier `analyze_product()`** :

```python
async def analyze_product(...) -> AnalysisResult:
    """Analyze product with USED and NEW pricing."""

    parsed_data = parse_keepa_product(keepa_data)

    # Extract prices
    sell_price = Decimal(str(parsed_data.get('current_price', 0)))
    used_price = parsed_data.get('current_used_price')
    new_price = parsed_data.get('current_fbm_price')

    # Calculate target buy price (same for both)
    target_buy_price = calculate_purchase_cost_from_strategy(
        sell_price=sell_price,
        strategy="balanced",  # or from config
        config=config
    )

    # Calculate ROI for USED
    pricing_used = None
    if used_price and used_price > 0:
        roi_used = calculate_roi_metrics(
            current_price=sell_price,
            estimated_buy_cost=Decimal(str(used_price)),
            product_weight_lbs=weight,
            category="books",
            config=config
        )

        pricing_used = PricingDetail(
            current_price=float(used_price),
            target_buy_price=float(target_buy_price),
            roi_percentage=roi_used.get('roi_percentage'),
            net_profit=roi_used.get('net_profit'),
            available=True,
            recommended=True
        )
    else:
        pricing_used = PricingDetail(
            current_price=None,
            target_buy_price=float(target_buy_price),
            roi_percentage=None,
            net_profit=None,
            available=False,
            recommended=False
        )

    # Calculate ROI for NEW
    pricing_new = None
    if new_price and new_price > 0:
        roi_new = calculate_roi_metrics(
            current_price=sell_price,
            estimated_buy_cost=Decimal(str(new_price)),
            product_weight_lbs=weight,
            category="books",
            config=config
        )

        pricing_new = PricingDetail(
            current_price=float(new_price),
            target_buy_price=float(target_buy_price),
            roi_percentage=roi_new.get('roi_percentage'),
            net_profit=roi_new.get('net_profit'),
            available=True,
            recommended=False
        )
    else:
        pricing_new = PricingDetail(
            current_price=None,
            target_buy_price=float(target_buy_price),
            roi_percentage=None,
            net_profit=None,
            available=False,
            recommended=False
        )

    return AnalysisResult(
        asin=asin,
        title=title,
        current_price=float(sell_price),
        current_bsr=parsed_data.get('current_bsr'),

        pricing={
            "used": pricing_used,
            "new": pricing_new
        },

        roi=roi_used if used_price else roi_new,  # Default to USED
        velocity=velocity_result,
        ...
    )
```

---

### 3. Ajouter Colonne BSR (Frontend)

**Fichier** : `frontend/src/components/ProductTable.tsx` (ou similaire)

**Change colonnes** :

```tsx
const columns = [
  { key: 'rank', label: 'RANK', sortable: false },
  { key: 'asin', label: 'ASIN', sortable: true },
  { key: 'title', label: 'TITLE', sortable: false },
  { key: 'bsr', label: 'BSR', sortable: true },  // ✨ NEW
  { key: 'score', label: 'SCORE', sortable: true },
  { key: 'roi', label: 'ROI', sortable: true },
  { key: 'velocity', label: 'VELOCITY', sortable: true },
  ...
]
```

**Render BSR** :

```tsx
<td className="px-4 py-2">
  {product.current_bsr ? (
    <span className="text-sm font-mono">
      #{product.current_bsr.toLocaleString()}
    </span>
  ) : (
    <span className="text-gray-400">N/A</span>
  )}
</td>
```

---

### 4. Modifier Card Produit (Frontend)

**Fichier** : `frontend/src/components/ProductCard.tsx` (ou similaire)

**Vue Collapsed - USED Focus** :

```tsx
<div className="product-card">
  <div className="header">
    <h3>{product.title}</h3>
    <span className="bsr">BSR: #{product.current_bsr}</span>
  </div>

  <div className="sell-price">
    <label>Prix Vente (NEW Amazon)</label>
    <span className="price">${product.current_price}</span>
  </div>

  {/* USED Pricing (Primary) */}
  {product.pricing?.used && (
    <div className="used-pricing recommended">
      <div className="badge">Recommandé pour FBA ✅</div>

      <div className="price-row">
        <label>Prix Achat USED Actuel</label>
        <span className="price">
          {product.pricing.used.available
            ? `$${product.pricing.used.current_price}`
            : 'Non disponible'
          }
        </span>
      </div>

      <div className="price-row">
        <label>Prix Cible (35% ROI)</label>
        <span className="price target">
          ≤ ${product.pricing.used.target_buy_price}
        </span>
      </div>

      {product.pricing.used.available && (
        <div className="roi-summary">
          <div className="metric">
            <label>Profit Net</label>
            <span>${product.pricing.used.net_profit?.toFixed(2)}</span>
          </div>
          <div className="metric">
            <label>ROI</label>
            <span className={getRoiClass(product.pricing.used.roi_percentage)}>
              {product.pricing.used.roi_percentage?.toFixed(1)}%
            </span>
          </div>
          <div className="metric">
            <label>Recommandation</label>
            <span className={getRecommendationClass(product.pricing.used.roi_percentage)}>
              {getRecommendation(product.pricing.used.roi_percentage)}
            </span>
          </div>
        </div>
      )}
    </div>
  )}

  <div className="velocity">
    <label>Vélocité</label>
    <span>FAST (70 ventes/30j)</span>
  </div>

  <button onClick={toggleExpand}>
    🔽 Voir détails (NEW, fees, history...)
  </button>
</div>
```

**Vue Expanded - Avec NEW** :

```tsx
{expanded && (
  <div className="expanded-details">
    {/* NEW Pricing (Alternative) */}
    <div className="new-pricing alternative">
      <div className="badge">Alternative (NEW) 🔒</div>

      <div className="price-row">
        <label>Prix Achat NEW Actuel</label>
        <span className="price">
          {product.pricing?.new?.available
            ? `$${product.pricing.new.current_price}`
            : 'Non disponible'
          }
        </span>
      </div>

      <div className="price-row">
        <label>Prix Cible (35% ROI)</label>
        <span className="price target">
          ≤ ${product.pricing?.new?.target_buy_price}
        </span>
      </div>

      {product.pricing?.new?.available && (
        <div className="roi-summary">
          <div className="metric">
            <label>ROI</label>
            <span>{product.pricing.new.roi_percentage?.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>

    {/* Fees Breakdown */}
    <FeesBreakdown fees={product.roi.fees} />

    {/* Velocity Details */}
    <VelocityDetails velocity={product.velocity} />
  </div>
)}
```

---

## ⏱️ Estimation Temps

| Tâche | Temps | Difficulté |
|-------|-------|------------|
| 1. Modifier `AnalysisResult` schema | 15 min | Facile |
| 2. Calculer ROI USED/NEW séparés | 30 min | Moyen |
| 3. Tester backend avec curl | 15 min | Facile |
| 4. Ajouter colonne BSR frontend | 15 min | Facile |
| 5. Modifier ProductCard frontend | 45 min | Moyen |
| 6. Styling CSS | 30 min | Facile |
| 7. Tests E2E avec vrais ASINs | 30 min | Facile |

**TOTAL** : ~3h d'implémentation + tests

---

## 🧪 Plan de Tests

### Test 1 : Backend API Response

```bash
curl -X POST "http://localhost:8000/api/v1/keepa/ingest" \
  -H "Content-Type: application/json" \
  -d '{"identifiers":["0593655036"],"strategy":"balanced"}' \
  | jq '.results[0].analysis.pricing'
```

**Résultat attendu** :

```json
{
  "used": {
    "current_price": 9.50,
    "target_buy_price": 6.77,
    "roi_percentage": 19.5,
    "net_profit": 1.85,
    "available": true,
    "recommended": true
  },
  "new": {
    "current_price": null,
    "target_buy_price": 6.77,
    "roi_percentage": null,
    "net_profit": null,
    "available": false,
    "recommended": false
  }
}
```

### Test 2 : Frontend Card Display

1. Ouvrir `http://localhost:5173`
2. Chercher ASIN `0593655036`
3. Vérifier card affiche :
   - ✅ "Recommandé pour FBA ✅" badge sur USED
   - ✅ Prix USED actuel : $9.50
   - ✅ Prix cible : ≤ $6.77
   - ✅ ROI : 19.5%
   - ✅ NEW visible seulement si expanded

### Test 3 : Colonne BSR

1. Vérifier tableau produits
2. Colonne BSR affiche : `#67`
3. Tri par BSR fonctionne

---

## ✅ Validation Finale

Avant de déployer, confirmer que :

- [ ] Backend retourne `pricing.used` et `pricing.new`
- [ ] ROI calculé séparément pour USED et NEW
- [ ] Frontend affiche USED en priorité
- [ ] NEW visible dans expanded view
- [ ] Colonne BSR ajoutée au tableau
- [ ] BSR affiché correctement (pas toujours "1")
- [ ] Tests passent avec 3+ ASINs différents

---

## 🚀 Déploiement

1. Commit backend changes
2. Commit frontend changes
3. Push vers GitHub
4. Trigger Render deployment (auto)
5. Valider en production avec ASIN test

---

**Prêt à commencer l'implémentation ?** 🚀

Je peux commencer par le backend (API response) puis le frontend, ou les deux en parallèle. Confirme et je démarre !
