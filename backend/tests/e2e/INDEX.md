# Index - Tests E2E ArbitrageVault

## Navigation rapide

### Documentation
- **README.md** - Guide principal pour executer les tests E2E
- **CLEANUP_SUMMARY.md** - Resume du nettoyage effectue (2025-11-28)
- **FUTURE_ENHANCEMENTS.md** - Options pour ameliorer la gestion des tests E2E

### Fichiers de tests
- **test_backend_corrections.py** - 9 tests de validation corrections backend
- **test_performance_load.py** - 6 tests de performance et charge
- **test_security_integration.py** - 8 tests de securite et integration

## Quick Start

### Pour executer les tests E2E

1. Demarrer le backend:
```bash
uvicorn app.main:app --reload
```

2. Verifier que le serveur repond:
```bash
curl http://localhost:8000/health
```

3. Les tests sont actuellement skippes par defaut.
   Voir README.md pour plus d'informations.

## Statut actuel

- Total tests: 23
- Tests skippes: 23 (100%)
- Tests failed: 0 (0%)
- Raison: Necessitent serveur backend en cours d'execution

## Structure

```
tests/e2e/
├── README.md                          # Documentation principale
├── CLEANUP_SUMMARY.md                 # Resume du cleanup
├── FUTURE_ENHANCEMENTS.md             # Guide ameliorations futures
├── INDEX.md                           # Ce fichier
├── test_backend_corrections.py        # Tests corrections backend (9)
├── test_performance_load.py           # Tests performance (6)
└── test_security_integration.py       # Tests securite (8)
```

## Liens utiles

- [README.md](README.md) - Comment executer les tests
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - Details du nettoyage
- [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) - Ameliorations possibles
