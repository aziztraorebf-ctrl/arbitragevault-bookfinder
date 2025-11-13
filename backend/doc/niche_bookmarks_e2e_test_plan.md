# Plan de Tests E2E - Niche Bookmarks Flow

**Date** : 2025-11-03
**Phase** : Phase 5 - Bookmarks & Re-run Analysis
**Environnement** : Local frontend (http://localhost:5173) + Production backend

---

## Configuration

### Frontend
- URL : `http://localhost:5173`
- Mode : Development (Vite dev server)
- Backend : Production (`https://arbitragevault-backend-v2.onrender.com`)

### Backend
- URL : `https://arbitragevault-backend-v2.onrender.com`
- Déploiement : `dep-d440qe2dbo4c73br2u3g` (live)
- Version : Commit `00ff975` (force_refresh support)

### Base de Données
- Provider : Neon PostgreSQL
- Project : wild-poetry-07211341
- Migration : `008835e8f328` (saved_niches table)

---

## Scénarios de Test

### Scénario 1 : Découverte et Sauvegarde de Niche

**Objectif** : Valider le flow complet de découverte → sauvegarde

**Étapes** :
1. Naviguer vers `/niche-discovery`
2. Cliquer sur "Auto Discovery" ou sélectionner une niche
3. Vérifier l'affichage des niches découvertes (NicheCard)
4. Cliquer sur le bouton "Sauvegarder" avec icône Bookmark
5. **Vérifier** : Toast success "Niche sauvegardée avec succès"

**Résultat attendu** :
- ✅ NicheCard affiche bouton Sauvegarder
- ✅ Bouton disabled pendant sauvegarde (isSaving=true)
- ✅ Toast de succès après sauvegarde
- ✅ Requête POST `/api/v1/bookmarks/niches` réussit (201)

**Critères de validation** :
- Status HTTP 201
- Réponse contient `id`, `niche_name`, `filters`, `created_at`
- Base de données contient nouvelle entrée dans `saved_niches`

---

### Scénario 2 : Affichage Liste "Mes Niches"

**Objectif** : Valider l'affichage des niches sauvegardées

**Étapes** :
1. Cliquer sur "Mes Niches" dans la navigation
2. **Vérifier** : Page `/mes-niches` charge
3. **Vérifier** : Liste des niches sauvegardées affichée
4. **Vérifier** : Chaque niche affiche :
   - Nom de la niche
   - Catégorie
   - Score (si disponible)
   - Date de création
   - Boutons "Relancer" et "Supprimer"

**Résultat attendu** :
- ✅ Requête GET `/api/v1/bookmarks/niches` réussit (200)
- ✅ Niches affichées avec NicheListItem
- ✅ Format date correct (relatif : "Il y a 2 minutes")
- ✅ Empty state si aucune niche sauvegardée

**Critères de validation** :
- Liste non vide après Scénario 1
- Toutes les niches sauvegardées visibles
- Score coloré selon valeur (vert si >70, orange si >40, gris sinon)

---

### Scénario 3 : Suppression de Niche

**Objectif** : Valider la suppression d'une niche sauvegardée

**Étapes** :
1. Sur page "Mes Niches", cliquer sur "Supprimer" pour une niche
2. **Vérifier** : Dialog de confirmation apparaît
3. Confirmer la suppression
4. **Vérifier** : Toast success "Niche supprimée"
5. **Vérifier** : Niche disparaît de la liste

**Résultat attendu** :
- ✅ Confirmation via `window.confirm()` avant suppression
- ✅ Requête DELETE `/api/v1/bookmarks/niches/{id}` réussit (204)
- ✅ Liste actualisée automatiquement (React Query invalidation)
- ✅ Toast de succès affiché

**Critères de validation** :
- Niche supprimée de la base de données
- Liste locale mise à jour sans refresh manuel
- Aucune erreur dans la console

---

### Scénario 4 : Relancer Analyse (avec force_refresh)

**Objectif** : Valider le re-run analysis avec refresh Keepa

**Prérequis** : Au moins une niche sauvegardée avec filtres

**Étapes** :
1. Sur page "Mes Niches", cliquer sur "Relancer" pour une niche
2. **Vérifier** : Bouton affiche spinner (isRerunning=true)
3. **Vérifier** : Requête GET `/api/v1/bookmarks/niches/{id}/filters` réussit
4. **Vérifier** : Requête POST `/api/v1/products/discover-with-scoring` avec `force_refresh: true`
5. **Vérifier** : Navigation vers `/niche-discovery` avec résultats
6. **Vérifier** : Titre "Analyse relancée : [nom de la niche]"
7. **Vérifier** : Produits affichés avec données fraîches
8. **Vérifier** : Toast success "Analyse relancée pour [nom]"

**Résultat attendu** :
- ✅ Filtres originaux récupérés depuis backend
- ✅ Parameter `force_refresh: true` envoyé au backend
- ✅ Backend bypass cache Discovery + Scoring
- ✅ Logs backend : "[DISCOVERY] FORCE REFRESH - bypassing cache"
- ✅ Navigation avec `location.state` contient rerunResults
- ✅ NicheDiscovery affiche résultats avec titre personnalisé

**Critères de validation** :
- Balance Keepa consommée (~50-150 tokens selon discovery)
- Données produits différentes du cache (si prix/BSR ont changé)
- Console logs backend montrent "FORCE REFRESH"
- Frontend reçoit `cache_hit: false` dans la réponse

---

### Scénario 5 : Gestion des Erreurs

**Objectif** : Valider les error handlers

**Cas de test** :

#### 5.1 - Sauvegarde échoue (backend down)
- **Action** : Arrêter backend, tenter sauvegarde
- **Attendu** : Toast error "Erreur: Impossible de sauvegarder"

#### 5.2 - Suppression échoue (niche inexistante)
- **Action** : Supprimer manuellement en DB, tenter suppression UI
- **Attendu** : Toast error + message détaillé du backend

#### 5.3 - Re-run échoue (tokens insuffisants)
- **Action** : Épuiser balance Keepa, tenter re-run
- **Attendu** : Toast error "Erreur: Insufficient tokens"

#### 5.4 - Empty state
- **Action** : Supprimer toutes les niches
- **Attendu** : Message "Aucune niche sauvegardée" avec lien vers Niche Discovery

**Résultat attendu** :
- ✅ Tous les cas d'erreur gérés gracefully
- ✅ Messages utilisateur clairs et actionnables
- ✅ Pas de crash application
- ✅ Console logs pour debugging

---

## Validation Technique

### API Endpoints (Backend)

Tester manuellement avec curl ou Postman :

```bash
# 1. Create bookmark (nécessite auth token)
curl -X POST https://arbitragevault-backend-v2.onrender.com/api/v1/bookmarks/niches \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{
    "niche_name": "Test Niche E2E",
    "category_id": 3617,
    "category_name": "Books",
    "filters": {"bsr_range": [10000, 50000], "price_range": [15, 40]},
    "last_score": 85.5
  }'

# 2. List bookmarks
curl -X GET https://arbitragevault-backend-v2.onrender.com/api/v1/bookmarks/niches \
  -H "Authorization: Bearer {TOKEN}"

# 3. Get filters
curl -X GET https://arbitragevault-backend-v2.onrender.com/api/v1/bookmarks/niches/{ID}/filters \
  -H "Authorization: Bearer {TOKEN}"

# 4. Delete bookmark
curl -X DELETE https://arbitragevault-backend-v2.onrender.com/api/v1/bookmarks/niches/{ID} \
  -H "Authorization: Bearer {TOKEN}"
```

**Note** : Authentification JWT requise pour tous les endpoints. Obtenir token via `/api/v1/auth/login`.

### Base de Données

Vérifier intégrité des données :

```sql
-- Count saved niches
SELECT COUNT(*) FROM saved_niches;

-- Check structure
SELECT id, niche_name, category_name, last_score, created_at, updated_at
FROM saved_niches
ORDER BY created_at DESC
LIMIT 5;

-- Verify filters JSON
SELECT niche_name, filters
FROM saved_niches
WHERE filters IS NOT NULL;
```

### Keepa Balance

Surveiller consommation tokens :

```bash
# Check balance before tests
curl -X GET https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/health

# Expected: balance > 100 tokens pour tests sûrs
```

---

## Critères de Succès Globaux

### Fonctionnalité
- ✅ Toutes les 5 phases implémentées et testées
- ✅ Backend + Frontend synchronisés
- ✅ Aucun crash ou erreur 500
- ✅ UX fluide avec loading states

### Performance
- ✅ Discovery sans cache : <5s pour 20 produits
- ✅ Discovery avec cache : <1s
- ✅ Sauvegarde bookmark : <500ms
- ✅ Chargement liste : <1s

### Qualité Code
- ✅ Aucun emoji dans code TypeScript/Python
- ✅ Build TypeScript : 0 erreurs
- ✅ Build Python : py_compile validé
- ✅ Commits clairs avec co-author

### Documentation
- ✅ Plan implémenté (`2025-11-02-niche-bookmarks-flow.md`)
- ✅ Rapport validation créé
- ✅ Changelogs à jour

---

## Prochaines Étapes (Post-Validation)

Si tous les tests passent :

1. **Mise à jour documentation**
   - Mettre à jour `compact_current.md` avec status Phase 5
   - Ajouter screenshots UX dans `doc/`
   - Créer user guide pour bookmarks

2. **Optimisations possibles**
   - Pagination pour "Mes Niches" si >50 bookmarks
   - Filtres/recherche dans liste bookmarks
   - Export CSV des niches sauvegardées
   - Partage de niches entre utilisateurs

3. **Monitoring production**
   - Ajouter métriques Sentry pour bookmarks
   - Surveiller balance Keepa avec force_refresh
   - Logs performance re-run analysis

---

## Notes

- **Environnement local only** : Netlify pas encore configuré, validation locale pour l'instant
- **Authentication** : Tous les endpoints bookmarks nécessitent JWT token
- **Keepa balance** : Actuellement ~1200 tokens, suffisant pour tests
- **Cache TTL** : Discovery cache = 6h, Scoring cache = 24h

---

**Status** : Prêt pour tests manuels
**Assigné** : Utilisateur final
**Deadline** : Validation avant déploiement Netlify
