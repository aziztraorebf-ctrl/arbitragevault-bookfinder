# Plan: Product Finder Post-Filtering Strategy

**Date**: 15 Decembre 2025
**Phase**: 6.2 - Niche Discovery Fix
**Statut**: VALIDE PAR TESTS

---

## Contexte

### Probleme Original
- "Surprise Me!" retourne 0 niches
- Les templates CURATED_NICHES utilisent des filtres stricts (FBA<=3, no Amazon)

### Tests Executes

| Script | Resultat | Conclusion |
|--------|----------|------------|
| `test_product_finder_relaxed.py` | 0/8 tests | Subcategories ne marchent pas |
| `test_product_finder_v3.py` | 2/6 tests | Root categories only |
| `test_product_finder_final.py` | 2/7 tests | Amazon exclusion + FBA = 0 |

### Decouvertes Cles

1. **ROOT CAUSE #1**: Product Finder `/query` ne supporte que categories RACINE
   - `rootCategory: 283155` (Books) = OK
   - `rootCategory: 10777` (Law subcategory) = 0 resultats

2. **ROOT CAUSE #2**: Combinaison `current_AMAZON_lte: -1` + `offerCountFBA_lte` = toujours 0
   - API ne supporte pas cette combinaison de pre-filtrage
   - Les produits existent (vus dans Test 5 avec `no-amz`)

### Resultats Valides

| Test | Filtres | Produits |
|------|---------|----------|
| Test 5 | BSR + Prix + FBA<=5 (sans Amazon exclusion) | **100,919** |
| Test 6 | BSR + Prix only | **32,698** |

---

## Solution: Post-Filtrage

### Architecture

```
[Product Finder /query]     [Product /product]        [Backend Filter]
        |                          |                        |
   Pre-filtres:               Enrichissement:          Post-filtres:
   - rootCategory             - FBA count reel         - exclude_amazon_seller
   - BSR range                - Amazon price           - max_fba_sellers
   - Price range              - Offer details          - ROI minimum
        |                          |                        |
        v                          v                        v
   ~30K ASINs              Details 50 produits        10-20 opportunites
   (10 tokens)               (50 tokens)                   (0 tokens)
```

### Flux Detaille

1. **Query Product Finder** (pre-filtres supportes uniquement)
   ```python
   selection = {
       "rootCategory": 283155,  # Books (ROOT obligatoire)
       "perPage": 50,
       "current_SALES_gte": 10000,   # BSR min
       "current_SALES_lte": 200000,  # BSR max
       "current_NEW_gte": 2000,      # Prix min ($20)
       "current_NEW_lte": 15000      # Prix max ($150)
   }
   ```

2. **Enrichir via /product API**
   ```python
   # Recuperer details pour 50 ASINs
   params = {
       "asin": ",".join(asins[:50]),
       "stats": 1,
       "offers": 20  # Pour compter FBA sellers
   }
   ```

3. **Post-filtrer backend**
   ```python
   def post_filter(products, criteria):
       filtered = []
       for p in products:
           # Extraire metriques
           amazon_price = p.stats.current[0]
           fba_count = p.stats.current[11]

           # Appliquer filtres utilisateur
           if criteria.exclude_amazon_seller and amazon_price > 0:
               continue
           if fba_count > criteria.max_fba_sellers:
               continue

           filtered.append(p)
       return filtered
   ```

---

## Implementation

### Task 1: Modifier NicheDiscoveryService

**Fichier**: `backend/app/services/niche_discovery_service.py`

**Changements**:
1. Ajouter methode `_query_product_finder()` avec pre-filtres supportes
2. Ajouter methode `_post_filter_products()` pour criteres non-supportes
3. Modifier `discover_niches()` pour utiliser nouvelle strategie

### Task 2: Adapter Templates CURATED_NICHES

**Fichier**: `backend/app/services/niche_templates.py`

**Changements**:
1. Remplacer `category_id` (subcategory) par `root_category_id`
2. Separer `pre_filters` (API) et `post_filters` (backend)
3. Ajouter mapping subcategory -> root category

### Task 3: Tests

**Fichiers**:
- `backend/tests/unit/test_post_filtering.py`
- `backend/tests/integration/test_product_finder_integration.py`

---

## Estimation Tokens

| Operation | Tokens | Frequence |
|-----------|--------|-----------|
| Product Finder query | ~10 | 1x par template |
| Product details (50) | ~50 | 1x par template |
| **Total par template** | ~60 | - |
| **Total 3 templates** | ~180 | Par "Surprise Me!" |

vs. Actuel (bestsellers): ~150 tokens pour 3 categories

**Delta**: +30 tokens mais avec filtrage precis

---

## Criteres de Succes

1. [ ] "Surprise Me!" retourne 1+ niches
2. [ ] Produits retournes respectent: `exclude_amazon_seller=true`, `max_fba_sellers<=3`
3. [ ] Temps reponse < 10 secondes
4. [ ] Tokens consommes < 200 par requete

---

## Rollback

Si probleme:
1. Revenir a strategie bestsellers actuelle
2. Elargir filtres templates (option 1 du diagnostic original)

---

**Auteur**: Claude Code
**Validation**: Tests `test_product_finder_final.py` - 100,919 produits avec BSR/prix filters
