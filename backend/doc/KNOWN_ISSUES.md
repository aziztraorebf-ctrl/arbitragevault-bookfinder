# Known Issues - ArbitrageVault Backend

## Windows Local Development - ProactorEventLoop Incompatibility

**Status**: Known limitation, non-bloquant pour production
**Date**: 2025-11-01
**Impact**: Développement Windows local uniquement

### Symptôme
```
(psycopg.InterfaceError) Psycopg cannot use the 'ProactorEventLoop' to run in async mode.
Please use a compatible event loop, for instance by running 'asyncio.run(..., loop_factory=asyncio.SelectorEventLoop(selectors.SelectSelector()))'
```

### Cause Racine
- **Windows** : Utilise `ProactorEventLoop` par défaut (Python 3.8+)
- **psycopg3 async** : Incompatible avec `ProactorEventLoop`, requiert `SelectorEventLoop`
- **Uvicorn** : Crée de nouveaux event loops pendant son cycle de vie (startup/shutdown)
- Même avec `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())`, Uvicorn peut créer des `ProactorEventLoop` pour certains contextes

### Impact Production
✅ **AUCUN** - Linux (Render) utilise `SelectorEventLoop` par défaut
✅ Pas d'incompatibilité psycopg3 sur systèmes Unix

### Solutions Implémentées

#### 1. Wrapper Synchrone (niche_templates.py)
```python
# Détecte ProactorEventLoop et exécute dans SelectorEventLoop isolé
if sys.platform == "win32" and "Proactor" in type(loop).__name__:
    return await _run_in_selector_loop(...)
```

#### 2. Event Loop Policy (main.py, start_server_no_console.py)
```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Workaround Développement Local Windows

**Option A** : Utiliser WSL2 (Windows Subsystem for Linux)
```bash
wsl
cd /mnt/c/Users/azizt/Workspace/arbitragevault_bookfinder/backend
python start_server_no_console.py
```

**Option B** : Tests directs sur Render (production)
- Backend déployé sur Render (Linux) fonctionne normalement
- Frontend Netlify → API Render = Aucun problème

**Option C** : Accepter l'erreur locale, tester en production
- Développement backend local limité sur Windows
- Validation complète via déploiements Render

### Références
- GitHub Issue psycopg: https://github.com/psycopg/psycopg/issues/554
- Python asyncio: https://docs.python.org/3/library/asyncio-platforms.html#windows
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

### Audit Futur
Si nécessaire, envisager :
1. Migration vers psycopg2 (synchrone, compatible ProactorEventLoop)
2. Utilisation de anyio pour abstraction event loop
3. Configuration Docker local pour environnement Linux identique à production

---

**Dernière mise à jour** : 2025-11-01
**Phase** : Phase 4 - Backlog Cleanup
