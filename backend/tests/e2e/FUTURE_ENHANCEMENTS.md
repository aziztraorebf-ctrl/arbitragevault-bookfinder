# Future Enhancements for E2E Tests

## Current Implementation

Les tests E2E sont actuellement skippés automatiquement via `pytestmark = pytest.mark.skip(...)` dans chaque fichier de test.

Cette approche simple fonctionne mais nécessite de démarrer manuellement le serveur backend avant d'exécuter les tests.

## Future Enhancement: Pytest CLI Flag

Pour implémenter un vrai flag `--run-e2e` qui contrôle l'exécution des tests E2E, voici les modifications nécessaires :

### 1. Modifier `backend/tests/conftest.py`

Ajouter cette configuration au début du fichier :

```python
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests that require a running backend server"
    )

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as E2E (requires running server)"
    )

def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless --run-e2e is provided."""
    if not config.getoption("--run-e2e"):
        skip_e2e = pytest.mark.skip(
            reason="need --run-e2e option to run"
        )
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
```

### 2. Modifier les fichiers de tests E2E

Remplacer :
```python
# Skip all E2E tests by default unless --run-e2e flag is provided
pytestmark = pytest.mark.skip(reason="Requires running backend server - use pytest --run-e2e to enable")
```

Par :
```python
# Mark all tests in this file as E2E tests
pytestmark = pytest.mark.e2e
```

### 3. Utilisation

Avec cette implémentation, les tests E2E peuvent être exécutés avec :

```bash
# Skip E2E tests (default)
pytest tests/

# Run only E2E tests
pytest tests/e2e/ --run-e2e

# Run all tests including E2E
pytest tests/ --run-e2e

# Run specific E2E test
pytest tests/e2e/test_backend_corrections.py::test_complete_workflow --run-e2e
```

## Future Enhancement: Automatic Server Start

Pour aller plus loin, il serait possible de démarrer automatiquement le serveur backend lors des tests E2E :

### Option A : Fixture pytest

```python
@pytest.fixture(scope="session")
def running_backend():
    """Start backend server for E2E tests."""
    import subprocess
    import time
    import httpx

    # Start server in background
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    for _ in range(30):
        try:
            response = httpx.get("http://localhost:8000/health", timeout=1.0)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(1)
    else:
        process.kill()
        raise RuntimeError("Backend server failed to start")

    yield "http://localhost:8000"

    # Cleanup
    process.kill()
    process.wait()
```

Puis dans les tests :
```python
@pytest.mark.e2e
async def test_server_health(running_backend):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{running_backend}/health")
        assert response.status_code == 200
```

### Option B : Docker Compose

Utiliser `pytest-docker-compose` pour gérer l'environnement complet :

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://test:test@postgres:5432/test

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=test
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=test
```

```python
# conftest.py
pytest_plugins = ["docker_compose"]

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        pytestconfig.rootdir,
        "docker-compose.test.yml"
    )
```

## Avantages / Inconvénients

### Approche actuelle (Skip manuel)
- Avantages : Simple, pas de dépendances
- Inconvénients : Nécessite de démarrer manuellement le serveur

### Flag --run-e2e
- Avantages : Contrôle explicite, intégration CI/CD facile
- Inconvénients : Nécessite toujours de démarrer le serveur manuellement

### Auto-start avec fixture
- Avantages : Tests autonomes, pas d'intervention manuelle
- Inconvénients : Plus complexe, peut être lent, gestion état difficile

### Docker Compose
- Avantages : Environnement complet isolé, reproductible
- Inconvénients : Nécessite Docker, plus lent, overhead

## Recommandation

Pour ArbitrageVault, la solution actuelle (skip manuel) est suffisante car :
1. Les tests E2E sont exécutés manuellement lors de validations majeures
2. Le CI/CD peut facilement démarrer le serveur avant les tests
3. Pas besoin de complexité additionnelle pour l'instant

Si les tests E2E deviennent plus fréquents, implémenter le flag `--run-e2e` serait le prochain step logique.
