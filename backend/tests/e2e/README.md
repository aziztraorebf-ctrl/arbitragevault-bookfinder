# Tests End-to-End (E2E)

## Description

Ce répertoire contient les tests end-to-end qui valident le fonctionnement complet du backend ArbitrageVault avec un serveur en cours d'exécution.

## Fichiers de tests

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

## Pourquoi sont-ils skippés par défaut ?

Ces tests nécessitent :
1. Un serveur backend FastAPI en cours d'exécution sur `http://localhost:8000`
2. Une base de données PostgreSQL configurée et accessible
3. Une clé API Keepa valide (pour certains tests)

Ils sont automatiquement skippés lors des tests unitaires pour ne pas bloquer le CI/CD.

## Comment exécuter ces tests

### Prérequis

1. Démarrer le backend :
```bash
cd backend
uvicorn app.main:app --reload
```

2. Vérifier que le serveur répond :
```bash
curl http://localhost:8000/health
```

### Exécuter les tests E2E

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
