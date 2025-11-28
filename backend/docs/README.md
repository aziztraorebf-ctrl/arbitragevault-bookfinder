# ArbitrageVault - Documentation Backend

> **Base documentaire complète** pour développeurs et architectes

---

## 📚 Index de Documentation

### 🏗️ Architecture & Design

| Document | Description | Statut |
|----------|-------------|--------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture complète backend, patterns, modules Keepa | ✅ Complet |
| [AUTOSOURCING_SAFEGUARDS.md](./AUTOSOURCING_SAFEGUARDS.md) | Safeguards Phase 7.0 AutoSourcing | ✅ Complet |

### 📊 Audits & Validations

| Audit | Description | Date | Statut |
|-------|-------------|------|--------|
| [Phase 1-2-3](./audits/) | Audits migrations, endpoints, services | Nov 2025 | ✅ Passed |

---

## 🎯 Guide de Navigation

### Pour les Nouveaux Développeurs

**Ordre de lecture recommandé** :

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Comprendre la structure globale
   - Architecture en couches
   - Modules Keepa (refactoring SRP)
   - Patterns utilisés
   - Guide "Où ajouter du code"

2. **[AUTOSOURCING_SAFEGUARDS.md](./AUTOSOURCING_SAFEGUARDS.md)** - Comprendre les protections
   - Cost validation
   - Token management
   - Timeout protection

3. **Audits** (optionnel) - Validation qualité
   - Vérifier conformité migrations
   - Tests endpoints production
   - Validation services

### Pour les Architectes

**Focus sur** :

- [ARCHITECTURE.md - Patterns de conception](./ARCHITECTURE.md#patterns-de-conception)
  - Facade Pattern
  - Repository Pattern
  - Circuit Breaker
  - Token Bucket Algorithm
  - Dependency Injection

- [ARCHITECTURE.md - Modules Keepa](./ARCHITECTURE.md#modules-keepa-refactoring-srp)
  - Vue d'ensemble refactoring SRP
  - Diagrammes de flux
  - Breakdown des 10 modules spécialisés

### Pour les DevOps

**Focus sur** :

- [ARCHITECTURE.md - Flux de données](./ARCHITECTURE.md#flux-de-données)
  - AutoSourcing Pipeline complète
  - Ingestion Batch flow

- [AUTOSOURCING_SAFEGUARDS.md](./AUTOSOURCING_SAFEGUARDS.md)
  - Cost limits
  - Token balance checks
  - Performance constraints

---

## 📖 Documentation Externe

### API Keepa

- **Documentation officielle** : https://keepa.com/#!api
- **Product.java (reference)** : https://github.com/keepacom/api_backend
- **Endpoint costs** : Voir [ARCHITECTURE.md - keepa_models.py](./ARCHITECTURE.md#keepa_modelspy---data-models-118-loc)

### FastAPI Ecosystem

- **FastAPI** : https://fastapi.tiangolo.com/
- **Pydantic V2** : https://docs.pydantic.dev/latest/
- **SQLAlchemy 2.0** : https://docs.sqlalchemy.org/en/20/

### Deployment

- **Render** : https://render.com/docs
- **Neon (PostgreSQL)** : https://neon.tech/docs

---

## 🔧 Quick Start Références

### Structure Backend

```
backend/
├── app/
│   ├── api/v1/          # API routers
│   ├── services/        # Business logic
│   ├── repositories/    # Data access
│   ├── models/          # SQLAlchemy ORM
│   ├── core/            # Core utilities
│   └── main.py          # App entry point
│
├── docs/                # THIS FOLDER
│   ├── README.md        # (You are here)
│   ├── ARCHITECTURE.md  # Architecture doc
│   └── audits/          # Validation audits
│
├── tests/               # Test suite
├── alembic/             # Database migrations
└── requirements.txt     # Python dependencies
```

### Commandes Utiles

```bash
# Lancer backend local
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Migrations database
alembic upgrade head                    # Apply all migrations
alembic revision --autogenerate -m "..."  # Create new migration

# Tests
pytest tests/ -v                        # Run all tests
pytest tests/test_keepa.py::test_name  # Run specific test

# Vérifier santé backend production
curl https://arbitragevault-api.onrender.com/api/v1/health/ready
```

---

## 🚀 Workflow Développement

### Ajouter une nouvelle feature

1. **Consulter** [ARCHITECTURE.md - Guide développeur](./ARCHITECTURE.md#guide-développeur)
2. **Identifier** la couche appropriée (API/Service/Repository/Core)
3. **Créer** module respectant SRP et naming conventions
4. **Tester** avec vraies données (pas de mocks pour validation finale)
5. **Documenter** dans code (docstrings Google style)
6. **Commit** avec message descriptif

### Pattern de commit

```bash
# Format: <type>(<scope>): <message>
git commit -m "feat(keepa): add competitor analysis endpoint"
git commit -m "fix(cache): resolve TTL expiration bug"
git commit -m "docs(architecture): update Keepa modules diagram"
git commit -m "refactor(service): split KeepaService into sub-modules"
```

**Types** : `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## 📝 Contribuer à la Documentation

### Ajouter un nouveau document

```bash
# Créer fichier dans backend/docs/
touch backend/docs/NEW_DOCUMENT.md

# Ajouter entrée dans ce README.md
# Section appropriée (Architecture/Audits/Guides)

# Commit
git add backend/docs/
git commit -m "docs: add NEW_DOCUMENT.md"
```

### Standards de documentation

**Tous les fichiers `.md` DOIVENT** :

- Utiliser Markdown standard
- Inclure table des matières si >500 lignes
- Utiliser diagrammes ASCII pour visualisations
- Fournir exemples concrets de code
- Inclure date dernière mise à jour
- Emojis AUTORISÉS (contrairement au code)

**Template minimal** :

```markdown
# Titre du Document

> **Brief description**

---

## Table des Matières
...

## Section 1
...

---

**Dernière mise à jour** : YYYY-MM-DD
**Auteur** : Nom
```

---

## 🔍 Recherche dans la Documentation

### Trouver information spécifique

```bash
# Rechercher terme dans toute la doc
grep -r "Circuit Breaker" backend/docs/

# Rechercher dans ARCHITECTURE.md seulement
grep -n "Facade Pattern" backend/docs/ARCHITECTURE.md

# Rechercher code examples
grep -A 5 "```python" backend/docs/ARCHITECTURE.md
```

### Index rapide par mot-clé

| Mot-clé | Document | Section |
|---------|----------|---------|
| Facade Pattern | ARCHITECTURE.md | Patterns de conception |
| Circuit Breaker | ARCHITECTURE.md | Patterns de conception |
| Token Bucket | ARCHITECTURE.md | Patterns de conception |
| Keepa modules | ARCHITECTURE.md | Modules Keepa |
| SRP refactoring | ARCHITECTURE.md | Modules Keepa |
| AutoSourcing | ARCHITECTURE.md | Flux de données |
| Cost validation | AUTOSOURCING_SAFEGUARDS.md | - |
| Migrations | audits/ | Phase 1-2-3 |

---

## 📊 Statistiques Documentation

**Dernière mise à jour**: 28 Novembre 2025

| Métrique | Valeur |
|----------|--------|
| Documents totaux | 4 |
| LOC documentation | ~2,500 |
| Diagrammes ASCII | 8 |
| Exemples code | 40+ |
| Dernière révision | 2025-11-28 |

---

## 🤝 Support

**Questions ou clarifications** ?

- Consulter `.claude/CLAUDE.md` pour instructions projet
- Voir [ARCHITECTURE.md](./ARCHITECTURE.md) pour détails techniques
- Audits dans `backend/docs/audits/` pour validations

---

**Maintenu par** : Équipe ArbitrageVault + Claude Code
**License** : Proprietary
