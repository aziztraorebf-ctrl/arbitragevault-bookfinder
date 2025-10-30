# Backend - Guide Windows

## Lancement du Serveur Backend (Windows)

⚠️ **IMPORTANT** : Sur Windows, utiliser `run_server.py` au lieu de `uvicorn` directement.

### Pourquoi ?

Windows utilise `ProactorEventLoop` par défaut, incompatible avec `psycopg3` (driver PostgreSQL async).
Le script `run_server.py` configure `SelectorEventLoop` avant de lancer uvicorn.

### Commande de Lancement

```bash
cd backend
python run_server.py
```

### ❌ Ne PAS utiliser

```bash
# Ne fonctionne PAS sur Windows avec async PostgreSQL
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Vérification

Backend disponible sur : http://127.0.0.1:8000

Health check : http://127.0.0.1:8000/api/v1/health/live

## Production (Linux/Render)

Sur Linux, pas de problème d'event loop. Utiliser uvicorn normalement :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Problèmes Connus (Windows Uniquement)

### Erreur d'encodage emoji dans les logs

```
'charmap' codec can't encode character '\u274c'
```

**Impact** : Aucun, juste affichage logs console.
**Solution** : Ignorer ou utiliser terminal UTF-8.
