# 🔍 Analyse : Prix NEW vs USED - Stratégie Arbitrage

**Date** : 16 Octobre 2025
**Question Utilisateur** : Est-ce que l'app montre seulement prix NEW ou aussi USED ?

---

## 📊 Ce que le Backend EXTRAIT (Code)

### Données Disponibles dans Keepa

Le parser **EXTRAIT** tous ces prix depuis `stats.current[]` :

```python
# backend/app/services/keepa_parser_v2.py lignes 122-130
extractors = [
    (0, 'amazon_price', True),      # Amazon prix (NEW direct)
    (1, 'new_price', True),         # 3rd party NEW prix
    (2, 'used_price', True),        # ✅ USED prix EXTRAIT !
    (3, 'bsr', False),              # BSR
    (4, 'list_price', True),        # List prix
    (10, 'fba_price', True),        # FBA prix (3rd party)
    (18, 'buybox_price', True),     # Buy Box prix
]
```

**✅ Le backend EXTRAIT `used_price` depuis Keepa !**

---

## 🔍 Ce qui est AFFICHÉ au Frontend

### Response API (test réel ASIN 0593655036)

```json
{
  "asin": "0593655036",
  "title": "The Anxious Generation",
  "current_price": 16.98,          // Vente
  "current_bsr": 67,
  "roi": {
    "sell_price": "16.98",         // Vente
    "buy_cost": "6.6272",          // ❓ D'où vient ce prix ?
    "target_buy_price": "6.29584"  // Prix cible pour 30% ROI
  }
}
```

**❌ La response ne contient PAS** :
- `current_fbm_price` (NEW)
- `current_used_price` (USED)
- `current_fba_price` (FBA)

**Problème** : Le frontend reçoit seulement `current_price` et `buy_cost`, mais ne sait pas **QUELLE source** (NEW vs USED).

---

## 🎯 Ta Question : Prix NEW ou USED ?

### Ce que tu veux (Stratégie Arbitrage USED) :

```
ACHETER : Livres USED de 3rd party sellers
  - Source : FBM ou FBA
  - Condition : USED - Good/Very Good
  - Prix : $3-8
  - Temps livraison : 1-2 semaines OK

REVENDRE : Livres USED via Amazon FBA
  - Condition : USED - Good/Very Good
  - Prix : $12-18
  - ROI : 30-50%
```

### Ce que l'app affiche ACTUELLEMENT :

#### Screenshot "The Anxious Generation" :

```
Market Sell: $16.98  ← current_amazon_price (NEW)
Market Buy: $0.00    ← current_fbm_price (NEW) = pas disponible
Max Buy: $6.77       ← target_buy_price (30% ROI)
```

**Problème** :
- `Market Buy $0.00` = Aucune offre NEW disponible
- Prix USED n'est **PAS affiché**
- Utilisateur ne sait pas s'il y a des offres USED

#### Screenshot "Atomic Habits" :

```
Market Sell: $15.39   ← Vente
Market Buy: $15.36    ← current_fbm_price (NEW)
Max Buy: $5.76        ← target_buy_price (35% ROI)
```

**Problème** :
- `Market Buy $15.36` = Prix NEW (trop cher pour arbitrage)
- Prix USED n'est **PAS affiché**
- ROI négatif -54.4% car calculé avec prix NEW

---

## 💡 Réponse à Ta Question

### ❌ **NON, l'app NE montre PAS les prix USED**

**Actuellement** :
- Le backend **extrait** `used_price` depuis Keepa
- Mais le backend **NE L'ENVOIE PAS** au frontend dans la response API
- Le frontend affiche seulement `current_price` (vente) et `buy_cost` (calculé)

**Le "Market Buy" affiché est** :
- `current_fbm_price` = Prix NEW 3rd party
- **PAS** `current_used_price` = Prix USED

---

## 🚨 Impact sur ta Stratégie

### Scénario Réel : Atomic Habits

**Ce que Keepa a** :
```
Prix Amazon (NEW direct): $15.39
Prix NEW 3rd party: $15.36
Prix USED: $8.50 ← ✅ PAS AFFICHÉ !
Prix FBA: $14.00
```

**Ce que l'app affiche** :
```
Market Sell: $15.39
Market Buy: $15.36 (NEW)
ROI: -54.4% ← Calculé avec NEW !
```

**Ce que tu DEVRAIS voir** :
```
Prix Vente (NEW): $15.39
Prix Achat USED: $8.50 ← ✅ Le vrai prix pour arbitrage !
ROI: ~25% (si achat à $8.50)
```

---

## ✅ Solution Nécessaire

### 1. **Modifier Response API**

Ajouter ces champs dans la response :

```json
{
  "asin": "0593655036",
  "current_price": 16.98,
  "current_amazon_price": 16.98,
  "current_fbm_price": 0.00,      // NEW 3rd party
  "current_used_price": 9.50,     // ✅ USED
  "current_fba_price": 14.00,     // FBA
  "roi": {
    "sell_price": "16.98",
    "buy_cost_new": "0.00",       // NEW si disponible
    "buy_cost_used": "9.50",      // ✅ USED
    "target_buy_price": "6.29"
  }
}
```

### 2. **Modifier Affichage Frontend**

```
╔═══════════════════════════════════════════════╗
║ The Anxious Generation                        ║
║═══════════════════════════════════════════════║
║ 💰 Prix Vente (NEW): $16.98                   ║
║                                               ║
║ 📦 Prix Achat Disponibles:                    ║
║   • NEW (3rd party): Non disponible           ║
║   • USED (3rd party): $9.50  ← ✅ AFFICHER !  ║
║   • FBA: $14.00                               ║
║                                               ║
║ 🎯 Stratégie Recommandée:                     ║
║   Acheter USED à: < $6.77                     ║
║   Revendre via FBA: $16.98                    ║
║   ROI estimé: 30%                             ║
╚═══════════════════════════════════════════════╝
```

### 3. **Clarifier Calcul ROI**

Calculer 2 ROI séparés :

```python
# ROI si achat NEW
roi_new = calculate_roi(
    sell_price=16.98,
    buy_cost=current_fbm_price  # NEW
)

# ROI si achat USED ✅ IMPORTANT POUR TOI
roi_used = calculate_roi(
    sell_price=16.98,
    buy_cost=current_used_price  # USED
)
```

---

## 🔄 Prochaines Étapes

### Attends ma validation avant de continuer :

1. **Est-ce que je comprends bien ta stratégie ?**
   - Tu veux acheter USED à bas prix
   - Revendre USED via FBA
   - Pas forcément NEW-to-NEW

2. **Veux-tu que je modifie l'app pour** :
   - Afficher `current_used_price` dans frontend ?
   - Calculer ROI avec prix USED au lieu de NEW ?
   - Montrer les 2 options (NEW et USED) côte à côte ?

3. **Quelle est ta priorité ?**
   - A) Fix affichage (montrer prix USED) = rapide
   - B) Fix calcul ROI (utiliser prix USED) = moyen
   - C) Refonte complète UI (NEW vs USED) = long

---

## 📊 Résumé

| Question | Réponse |
|----------|---------|
| **Backend extrait USED prix ?** | ✅ OUI (`used_price` extrait) |
| **Frontend affiche USED prix ?** | ❌ NON (pas dans response API) |
| **ROI calculé avec USED ?** | ❌ NON (utilise NEW ou target) |
| **Stratégie actuelle** | NEW-to-NEW (pas USED-to-USED) |

---

**Confirme-moi ce que tu veux et je te propose les fixes appropriés !**
