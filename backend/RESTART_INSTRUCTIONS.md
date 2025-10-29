# Instructions de Redémarrage - Phase 3 Day 7

## Contexte
Le router `products` a été monté dans `app/main.py` (ligne 22 import, ligne 81 mount).
Le serveur doit être redémarré pour charger cette nouvelle configuration.

## Étape 1 : Redémarrer le Serveur

### Option A : Utiliser le Script Batch (Recommandé)
```bash
cd C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend
restart_server.bat
```

**Instructions** :
1. Si un serveur est déjà en cours, appuyez sur `Ctrl+C` dans la fenêtre PowerShell du serveur existant
2. Appuyez sur une touche dans la fenêtre du script batch pour démarrer le nouveau serveur
3. Attendez le message "Application startup complete"

### Option B : Redémarrage Manuel
**Terminal existant du serveur** :
1. Appuyez sur `Ctrl+C` pour arrêter le serveur
2. Exécutez à nouveau :
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

**Nouveau terminal** (si l'ancien n'est plus accessible) :
```powershell
cd C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Étape 2 : Vérifier les Endpoints

Une fois le serveur redémarré, tester l'accessibilité :

```bash
# Health check du router products
curl http://localhost:8000/api/v1/products/health

# Vérifier OpenAPI schema
curl http://localhost:8000/openapi.json | findstr "products/discover"
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "service": "Product Finder",
  "api_key_configured": true,
  "endpoints": [...]
}
```

## Étape 3 : Exécuter les Tests E2E

Une fois le serveur opérationnel :

```bash
cd C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend
python test_discovery_e2e_validation.py
```

## Résultat Attendu

**9 tests doivent passer** :
1. ✅ Health Check
2. ✅ Discover ASINs Only
3. ✅ Cache Hit Validation
4. ✅ Discover with Scoring
5. ✅ Edge Case - Empty Results
6. ✅ Edge Case - Invalid Category
7. ✅ Frontend Zod Compatibility
8. ✅ Cache Performance 10x
9. ✅ Bonus - Top 3 Products

**Métriques cibles** :
- Cache hit : < 500ms
- API call : < 15s
- Cache speedup : ≥ 10x
- Tous les champs Pydantic/Zod validés

## Modifications Effectuées

### backend/app/main.py
```python
# Ligne 22
from app.api.v1.endpoints import products

# Ligne 81
app.include_router(products.router, prefix="/api/v1/products", tags=["Product Discovery"])
```

### backend/.env
```bash
# Driver async corrigé (ligne 7)
DATABASE_URL=postgresql+psycopg://neondb_owner:...
```

### Dépendances installées
```bash
pip install "psycopg[binary]" psycopg-pool
```

## Dépannage

### Erreur : "HTTP 404 Not Found"
- Serveur pas redémarré → Relancer uvicorn
- Router pas monté → Vérifier `app/main.py` ligne 22 et 81

### Erreur : "Connection refused"
- Serveur pas démarré → Lancer `uvicorn app.main:app`
- Port 8000 occupé → Changer de port avec `--port 8001`

### Erreur : "asyncio extension requires async driver"
- Driver sync utilisé → Vérifier `.env` utilise `postgresql+psycopg://`
- psycopg pas installé → `pip install "psycopg[binary]" psycopg-pool`

## Prochaines Étapes

Après validation tests E2E :
1. Intégrer cache tables (ProductDiscoveryCache, ProductScoringCache)
2. Frontend Day 7 : Connecter React hooks aux endpoints validés
3. Tests E2E UI avec vraies données Keepa
