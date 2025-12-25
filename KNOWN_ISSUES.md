# Known Issues - ArbitrageVault BookFinder

Document des bugs et limitations connus. A adresser lors de la phase de polish finale.

## Status: Phase 8+ Complete - Moving to UI Completion

---

## Bugs Corriges (Session 2025-12-25)

### 1. Ecran blanc apres clic "Verifier" (CORRIGE)
- **Commit**: `25ea9d8` - fix(ui): use != null for null checks in VerificationDetails
- **Root cause**: API retourne `null` explicitement, `!== undefined` ne protegeait pas
- **Fix**: Change `!== undefined` en `!= null` dans ProductsTable.tsx

### 2. Patterns null check inconsistants Smart Velocity (CORRIGE)
- **Commit**: `128813f` - fix(ui): apply consistent null checks across Smart Velocity components
- **Fichiers**: VelocityDetailsSection.tsx, ResultsView.tsx, ViewResultsRow.tsx
- **Fix**: Standardise `value != null` au lieu de `value !== null && value !== undefined`

---

## Bugs Connus (A Traiter Plus Tard)

### Frontend

#### 1. Buy Opportunities parfois vides
- **Severite**: Moyenne
- **Description**: L'API retourne `buy_opportunities: []` pour certains produits
- **Impact**: Pas de calcul de profit affiche pour ces produits
- **Workaround**: Message "Aucune opportunite d'achat profitable" affiche

#### 2. Donnees manquantes dans verification
- **Severite**: Basse
- **Description**: `sell_price`, `used_sell_price`, `current_bsr` parfois null
- **Impact**: Champs non affiches (gere avec `!= null` check)
- **Root cause**: Produits sans historique Keepa suffisant

#### 3. FBA count = -1
- **Severite**: Basse
- **Description**: API retourne -1 quand donnee non disponible
- **Fix applique**: Check `>= 0` ajoute en plus de `!= null`

### Backend

#### 1. Tokens Keepa consommes meme en cache hit
- **Severite**: Basse
- **Description**: Certaines requetes consomment des tokens malgre le cache
- **A investiguer**: Verification si cache Redis fonctionne correctement

#### 2. Timeout sur grosses niches
- **Severite**: Moyenne
- **Description**: Niches avec 50+ produits peuvent timeout
- **Workaround**: Limite a 20 produits par defaut

---

## Limitations Connues

### Strategies de Recherche

| Strategie | Status | Notes |
|-----------|--------|-------|
| Textbook Standard | Fonctionnel | BSR 100k-250k, prix $40-150 |
| Textbook Patience | Non teste exhaustivement | Meme code que Standard |
| Smart Velocity | Fixes appliques | A valider en production |

### API Keepa

- **Rate limiting**: 10 requetes/seconde
- **Tokens**: ~50 tokens par produit avec offers
- **Cache**: 1 heure par defaut

---

## Pages UI Manquantes

A construire dans les prochaines phases:

1. **Dashboard** - Vue d'ensemble des metriques
2. **Mes Niches** - Gestion des niches sauvegardees
3. **AutoScheduler** - Planification des recherches automatiques
4. **Stock Estimates** - Estimation des stocks
5. **Configuration** - Parametres utilisateur

---

## Prochaines Etapes

1. [ ] Valider Smart Velocity en production avec test E2E
2. [ ] Construire pages UI manquantes
3. [ ] Phase de polish finale
4. [ ] Tests de regression complets

---

*Derniere mise a jour: 2025-12-25*
