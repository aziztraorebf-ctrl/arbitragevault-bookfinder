# ArbitrageVault - Règles et Spécifications Projet

## PHASE PRODUCTION RÉUSSIE - Architecture Déployée et Validée

### Contexte Actuel - DÉPLOIEMENT PRODUCTION COMPLET ✅
**Backend Status:** v1.6.3 - UV + Python 3.12.8 + SQLAlchemy 2.0 Async + asyncpg
**Frontend Status:** ✅ DÉPLOYÉ - React 18 + TypeScript + Vite 
**Production:** Render Blueprint monorepo - DÉPLOIEMENT RÉUSSI
**URLs Live:** Frontend + Backend accessibles publiquement sur Render
**Développement:** Méthodologie Documentation-First établie et validée

### Méthodologie Documentation-First - APPROCHE VALIDÉE EN PRODUCTION

#### Pattern de Résolution Problèmes - MÉTHODOLOGIE ÉTABLIE
**Approche systémique validée (élimination whack-a-mole) :**
1. **Documentation Research** → Consulter docs officielles AVANT corrections
2. **Root Cause Analysis** → Identifier problème central (pas symptômes)
3. **Systematic Solutions** → Corrections architecturales complètes
4. **Complete Validation** → Solutions groupées vs fixes ponctuels
5. **Build-Test-Validate** → Cycles itératifs avec validation immédiate

#### Error Resolution Priority - HIÉRARCHIE VALIDÉE
**Ordre résolution (critique → cosmétique) :**
1. **Build errors** → Empêchent compilation (bloquants)
2. **Runtime errors** → Empêchent startup (critiques)  
3. **Configuration errors** → Architecture/dependencies (systémiques)
4. **Type warnings** → N'empêchent pas fonctionnement (ignorables temporairement)
5. **Linting issues** → Qualité code (post-deployment)

### Configuration Render Production - STACK VALIDÉ

#### UV Package Manager - SUPPORT OFFICIEL CONFIRMÉ
**Configuration UV validée en production :**
```yaml
services:
  - runtime: python
    rootDir: backend
    buildCommand: uv sync --frozen  # ✅ Lockfile exact
    startCommand: uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Fichiers critiques requis :**
```
/.python-version     # ✅ Python 3.12.8 (priorité maximale)
/uv.lock            # ✅ Dependencies lockfile (root requis)
/backend/pyproject.toml  # ✅ Project configuration
```

#### PostgreSQL Async Stack - CONFIGURATION VALIDÉE
**Driver PostgreSQL pour SQLAlchemy Async :**
```toml
dependencies = [
    "asyncpg>=0.29.0,<0.30.0",  # ✅ Driver async dédié
    # PAS psycopg2-binary (sync-only, incompatible)
]
```

**URL Transformation automatique :**
```python
@validator("database_url", pre=True)
def transform_database_url_for_asyncpg(cls, v):
    # Render: postgresql://user:pass@host:port/db
    # SQLAlchemy: postgresql+asyncpg://user:pass@host:port/db
    if v.startswith("postgresql://") and "asyncpg" not in v:
        return v.replace("postgresql://", "postgresql+asyncpg://", 1)
```

#### Dependencies Management - PATTERNS CRITIQUES VALIDÉS
**Structure dependencies production :**
```toml
[project]
dependencies = [
    # Core Framework
    "fastapi>=0.104.0,<0.105.0",
    "uvicorn[standard]>=0.24.0,<0.25.0",
    
    # Database Async Stack
    "sqlalchemy[asyncio]>=2.0.23,<2.1.0",
    "asyncpg>=0.29.0,<0.30.0",  # ✅ Async PostgreSQL driver
    "alembic>=1.13.0,<1.14.0",
    
    # Data Validation
    "pydantic>=2.11.0,<3.0.0",  # ✅ Core library (pas seulement pydantic-settings)
    "pydantic-settings>=2.1.0,<2.2.0",
    
    # HTTP & Networking
    "httpx>=0.25.0,<0.26.0",    # ✅ Production HTTP client
    "tenacity>=8.2.0,<9.0.0",  # ✅ Retry patterns
    
    # Utilities
    "jsonpatch>=1.33,<2.0.0",  # ✅ JSON operations
    "structlog>=23.2.0,<24.0.0",
    "keyring>=24.3.0,<25.0.0",
    "keepa>=1.3.0,<2.0.0",
    
    # Security & Auth
    "python-jose[cryptography]>=3.3.0,<3.4.0",
    "passlib[argon2,bcrypt]>=1.7.4,<1.8.0",
    "python-multipart>=0.0.6,<0.1.0",
]
```

**ERREUR CRITIQUE ÉVITÉE :**
```toml
# ❌ ERREUR : Dependencies production en dev
[project.optional-dependencies]
dev = [
    "httpx",     # ❌ Utilisé en production (keepa_service.py)
    "tenacity",  # ❌ Utilisé en production (retry patterns)
    "pydantic",  # ❌ Utilisé partout en production
]
```

### Technology Stack Production - VALIDÉ EN DÉPLOIEMENT

#### Python Stack Final - PRODUCTION-READY
```python
# Python 3.12.8              # ✅ Package compatibility optimal
# UV + uv.lock               # ✅ Official Render support
# SQLAlchemy>=2.0.0 ASYNC    # ✅ create_async_engine()
# asyncpg>=0.29.0            # ✅ Async PostgreSQL driver
# Pydantic>=2.0.0            # ✅ v2 flat config + core validation
# FastAPI>=0.104.0           # ✅ Compatible async stack
```

#### Frontend Stack Final - PRODUCTION-READY  
```json
{
  "dependencies": {
    "react": "^19.1.1",       // ✅ Latest stable
    "typescript": "latest",   // ✅ Strict mode Render
    "vite": "latest"          // ✅ Build optimisé
  },
  "devDependencies": {
    "@types/node": "^20.0.0"  // ✅ OBLIGATOIRE Render (process.env types)
  }
}
```

### Render Deployment Patterns - VALIDÉS EN PRODUCTION

#### Monorepo Structure - DÉPLOIEMENT RÉUSSI
```
/
├── .python-version          # ✅ Python version control (priorité max)
├── uv.lock                  # ✅ UV dependency lockfile (root requis)
├── render.yaml              # ✅ Blueprint configuration monorepo
├── backend/                 # rootDir backend
│   ├── app/
│   │   ├── core/settings.py # ✅ Pydantic v2 + URL transformation
│   │   └── models/          # SQLAlchemy 2.0 async syntax
│   └── pyproject.toml       # ✅ UV project config + dependencies complètes
└── frontend/                # rootDir frontend  
    ├── src/                 # React + TypeScript Render-compatible
    └── package.json         # @types/node included
```

#### Environment Variables - RENDER PRODUCTION
```yaml
# Backend envVars validés
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: arbitragevault-db
      property: connectionString  # ✅ Auto-transformé par validator
  - key: KEEPA_API_KEY
    sync: false                # ✅ User input required
```

### Troubleshooting Methodology - DOCUMENTATION-FIRST VALIDÉE

#### Dependency Analysis Systémique - MÉTHODOLOGIE ÉTABLIE
**Avant corrections, analyser TOUTES les dépendances :**
```python
# Analyser imports vs dependencies déclarées
import re
from pathlib import Path

def analyze_imports(directory):
    """Analyser tous les imports dans le répertoire backend."""
    imports = set()
    for py_file in Path(directory).rglob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()
        import_lines = re.findall(r'^(?:import|from)\s+([a-zA-Z][a-zA-Z0-9_]*)', content, re.MULTILINE)
        for imp in import_lines:
            if not imp.startswith('app') and imp not in BUILTIN_MODULES:
                imports.add(imp)
    return sorted(imports)
```

#### Error Classification - PATTERNS VALIDÉS
**Build vs Runtime vs Configuration :**
- **Build Errors** : Dependencies manquantes, syntax errors → Bloquent compilation
- **Runtime Errors** : Import errors, configuration → Post-compilation
- **Configuration Errors** : Driver incompatibility, URL format → Architecturaux

**Resolution approach :** Résoudre par ordre de priorité, pas par ordre d'apparition.

### Git Workflow Production - CONVENTIONS ÉTABLIES

#### Commit Patterns - VALIDÉS
```bash
# ✅ TOUJOURS depuis ROOT projet
cd PROJECT_ROOT
git add backend/file.py      # Path complet depuis root
git commit -m "fix: Description systémique du problème résolu"

# Messages de commit avec contexte
"fix: Add ALL missing production dependencies - Documentation-First approach"
"fix: Complete async PostgreSQL solution - asyncpg + URL transformation"
```

#### Repository Management - PATTERNS CRITIQUES
**Éviter repos dupliqués :**
- `arbitragevault_bookfinder` (underscore) → Repo obsolète
- `arbitragevault-bookfinder` (tiret) → Repo principal actif

### Performance Production - BENCHMARKS VALIDÉS

#### Déploiement Times - PRODUCTION CONFIRMÉS
- **Frontend** : 1-2 minutes (TypeScript + Vite)
- **Backend** : 3-5 minutes (UV dependencies + Python setup)
- **Database** : Instantané (PostgreSQL managed)

#### Stack Performance - VALIDÉ
- **asyncpg** : 2-5x plus rapide que psycopg2 sync
- **UV** : 10-100x plus rapide que pip
- **SQLAlchemy Async** : Concurrent requests optimisées

### Development Methodology - BUILD-TEST-VALIDATE APPLIQUÉ

#### Documentation-First Development - VALIDÉE
**Quand rencontrer erreurs deployment :**
1. **Rechercher documentation officielle** (platform + libraries)
2. **Analyser systémiquement** (toutes dépendances, pas une par une)
3. **Identifier root cause** (architecture vs symptômes)
4. **Appliquer solutions complètes** (pas patches ponctuels)
5. **Commit atomique** + test immédiat

#### Build-Test-Validate Cycles - MÉTHODOLOGIE ÉTABLIE
**Per iteration :**
- **Build** : Configuration + dependencies setup complet
- **Test** : Deployment logs + error analysis systémique
- **Validate** : Application accessibility + core functions

### Lessons Learned - PRODUCTION DEPLOYMENT

#### Technology Choices Trade-offs - VALIDÉS
**UV Package Manager :**
- ✅ **Avantages** : Performance, lockfile déterministe, support officiel Render
- ⚠️ **Complexité** : Documentation récente, patterns pas établis
- 🎯 **Recommandation** : Excellent pour projets avancés, équipes expérimentées

**SQLAlchemy Async :**
- ✅ **Avantages** : Performance supérieure, concurrent requests
- ⚠️ **Complexité** : Driver spécifique (asyncpg), configuration avancée
- 🎯 **Recommandation** : Justifié pour applications high-throughput

**Monorepo :**
- ✅ **Avantages** : Code sharing, déploiement coordonné
- ⚠️ **Complexité** : Configuration Render Blueprint, CORS management
- 🎯 **Recommandation** : Excellent si bien configuré

#### Render Platform Insights - PRODUCTION VALIDÉS
**"One-click" deployment fonctionne pour :**
- pip + requirements.txt (pas UV)
- SQLAlchemy synchrone (pas async)
- Configuration simple (pas monorepo)

**Configurations avancées nécessitent :**
- Documentation-first approach
- Systematic dependency analysis
- Architecture-level solutions

### Next Steps - POST-DEPLOYMENT

#### Phase 1: Validation & Monitoring (Immédiat)
- 📊 **Health Checks** : Vérifier endpoints critiques
- 🚨 **Monitoring Setup** : Render dashboard, alertes
- ⏱️ **Performance Baseline** : Mesurer response times

#### Phase 2: Sécurité & Production Hardening (1-2 semaines)
- 🔒 **Environment Variables** : JWT_SECRET, CORS restrictif
- 💾 **Backup Strategy** : Database backups, disaster recovery
- 🛡️ **Security Hardening** : Rate limiting, custom domain

#### Phase 3: Features & Business Value (2-4 semaines)
- 📊 **Keepa Integration** : Tester avec vraies données
- 🔍 **Core Features** : Book analysis, dashboard
- 📈 **Scaling Preparation** : Caching, analytics, user management

---

**Dernière mise à jour :** 19 janvier 2025 - DÉPLOIEMENT PRODUCTION RÉUSSI ✅
**Status :** Frontend + Backend déployés et accessibles publiquement
**Méthode validée :** Documentation-First + UV + asyncpg + systematic dependency analysis
**Achievement :** Transformation whack-a-mole → architecture production-ready complète