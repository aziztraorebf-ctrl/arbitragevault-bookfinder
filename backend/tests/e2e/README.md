# Tests End-to-End (E2E)

## Description

Ce répertoire contient les tests end-to-end qui valident le fonctionnement complet du backend et frontend ArbitrageVault en production.

## Types de tests

### Tests Playwright (Frontend + Backend integration)
Tests E2E complets simulant des utilisateurs réels interagissant avec l'application déployée.

### Tests Python (Backend API)
Tests E2E du backend seul nécessitant un serveur local en cours d'exécution.

## Fichiers de tests

### Tests Playwright (tests/*.spec.js)

- **01-health-monitoring.spec.js** - Tests de santé et monitoring
- **02-token-control.spec.js** - Contrôle des tokens Keepa
- **03-niche-discovery.spec.js** - Découverte de niches
- **04-manual-search-flow.spec.js** - Recherche manuelle
- **05-autosourcing-flow.spec.js** - AutoSourcing
- **06-token-error-handling.spec.js** - Gestion erreurs tokens
- **07-navigation-flow.spec.js** - Navigation entre pages
- **08-autosourcing-safeguards.spec.js** - Protections AutoSourcing
- **09-phase-8-decision-system.spec.js** - Système de décision
- **10-robustness-randomized.spec.js** - Tests de robustesse
- **11-phase7-autosourcing-audit.spec.js** - Audit AutoSourcing
- **12-source-price-factor-verification.spec.js** - Vérification facteurs prix
- **13-bookmarks-flow.spec.js** (Phase 5 - NEW) - Tests bookmarks :
  - should display empty state when no bookmarks
  - should navigate to niche discovery from empty state
  - should save a niche from discovery results
  - should list saved bookmarks
  - should delete a bookmark with confirmation
  - should re-run analysis from saved bookmark

### Tests Python (Backend API)

- **test_backend_corrections.py** (9 tests)
  - Validation des corrections majeures backend
  - Vérification que les endpoints utilisent la BDD réelle (pas de stubs)
  - Tests de cohérence données BDD ↔ API

- **test_performance_load.py** (6 tests)
  - Tests de performance et charge
  - Temps de réponse baseline
  - Requêtes concurrentes
  - Performance création de batches
  - Stabilité mémoire

- **test_security_integration.py** (8 tests)
  - Tests de sécurité et intégration
  - Validation clés API Keepa
  - Vérification exposition données sensibles
  - Tests d'injection et validation
  - Configuration CORS

## Comment exécuter ces tests

### Tests Playwright (Production E2E)

Les tests Playwright s'exécutent contre les environnements de production déployés :
- Frontend : https://arbitragevault.netlify.app
- Backend : https://arbitragevault-backend-v2.onrender.com

**Installer les dépendances** :
```bash
cd backend/tests/e2e
npm install
npx playwright install chromium
```

**Exécuter tous les tests** :
```bash
npx playwright test
```

**Exécuter un test spécifique** :
```bash
npx playwright test 13-bookmarks-flow.spec.js
```

**Exécuter avec interface UI** :
```bash
npx playwright test --ui
```

**Exécuter en mode headed (voir le navigateur)** :
```bash
npx playwright test --headed
```

**Voir le rapport HTML** :
```bash
npx playwright show-report
```

**Notes importantes** :
- Les tests utilisent les environnements de production
- Certains tests peuvent échouer si les tokens Keepa sont épuisés (429 errors)
- Les tests incluent des cleanups automatiques (suppression des données de test)
- Le seed de randomisation garantit la reproductibilité

### Tests Python (Backend API local)

Ces tests nécessitent :
1. Un serveur backend FastAPI en cours d'exécution sur `http://localhost:8000`
2. Une base de données PostgreSQL configurée et accessible
3. Une clé API Keepa valide (pour certains tests)

Ils sont automatiquement skippés lors des tests unitaires pour ne pas bloquer le CI/CD.

**Prérequis pour tests Python** :

1. Démarrer le backend :
```bash
cd backend
uvicorn app.main:app --reload
```

2. Vérifier que le serveur répond :
```bash
curl http://localhost:8000/health
```

**Exécuter les tests Python E2E** :

**Option 1 : Tous les tests E2E**
```bash
pytest tests/e2e/ --run-e2e -v
```

**Option 2 : Un fichier spécifique**
```bash
pytest tests/e2e/test_backend_corrections.py --run-e2e -v
pytest tests/e2e/test_performance_load.py --run-e2e -v
pytest tests/e2e/test_security_integration.py --run-e2e -v
```

**Option 3 : Un test spécifique**
```bash
pytest tests/e2e/test_backend_corrections.py::test_complete_workflow --run-e2e -v
```

### Note sur le flag --run-e2e

Le flag `--run-e2e` est actuellement simulé par le skip decorator. Pour une vraie implémentation, il faudrait :

1. Ajouter dans `conftest.py` :
```python
def pytest_addoption(parser):
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests that require a running backend server"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as E2E (requires running server)")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-e2e"):
        skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
```

2. Remplacer `pytestmark = pytest.mark.skip(...)` par `pytestmark = pytest.mark.e2e`

## Résultats attendus

Quand le backend est en cours d'exécution, tous les tests doivent passer :
```
tests/e2e/test_backend_corrections.py::test_complete_workflow PASSED
tests/e2e/test_performance_load.py::test_complete_performance_suite PASSED
tests/e2e/test_security_integration.py::test_complete_security_suite PASSED

======================== 23 passed in 45.23s ========================
```

## Maintenance

Ces tests sont maintenus mais nécessitent un serveur backend actif. Si le backend change significativement :

1. Mettre à jour les endpoints testés
2. Ajuster les assertions selon les nouveaux formats de réponse
3. Vérifier que les timeouts sont appropriés
4. Valider que les données de test (ISBNs/ASINs) sont toujours valides

## Troubleshooting

**Erreur : Connection refused**
- Le serveur backend n'est pas démarré sur `http://localhost:8000`
- Solution : `uvicorn app.main:app --reload`

**Erreur : Database connection**
- La base de données n'est pas accessible
- Solution : Vérifier `DATABASE_URL` dans `.env`

**Erreur : Keepa API**
- Clé API Keepa manquante ou invalide
- Solution : Configurer `KEEPA_API_KEY` dans l'environnement

**Tests lents**
- Certains tests Keepa peuvent prendre 10-30 secondes
- C'est normal, ils font de vraies requêtes API
- Augmenter `PERFORMANCE_TIMEOUT` si nécessaire
