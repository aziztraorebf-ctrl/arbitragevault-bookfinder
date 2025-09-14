# ArbitrageVault - Règles et Spécifications Projet

## PHASE DÉPLOIEMENT RENDER - Architecture Production Validée

### Contexte Actuel - DÉPLOIEMENT PRODUCTION EN COURS
**Backend Status:** v1.6.1 - Configuration SQLAlchemy 2.0 + Pydantic v2 compatible
**Frontend Status:** React 18 + TypeScript + Vite - Structure minimale déployée
**Production:** Déploiement Render Blueprint avec monorepo structure
**Développement:** Migration complète local → production, workflow établi

### Configuration Render Critique - LEÇONS PRODUCTION

#### Render Blueprint Syntax - DOCUMENTATION VALIDÉE
**Structure monorepo validée:**
```yaml
services:
  - type: web
    name: arbitragevault-backend
    runtime: python                    # ✅ PAS python3
    rootDir: backend                    # ✅ Évite cd commands
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    
  - type: web  
    name: arbitragevault-frontend
    runtime: static
    rootDir: frontend                   # ✅ Évite cd commands
    staticPublishPath: dist             # ✅ Relatif à rootDir
```

**Pattern de résolution problèmes Render:**
1. Documentation officielle AVANT correction (render.com/docs/blueprint-spec)
2. Errors logs précis → corrections ciblées
3. Commits atomiques pour chaque fix
4. Test immédiat après chaque correction

#### SQLAlchemy 2.0 Migration - BREAKING CHANGES CRITIQUES
**Imports v1→v2:**
```python
# ❌ OBSOLÈTE (SQLAlchemy 1.x)
from sqlalchemy import Decimal

# ✅ CORRECT (SQLAlchemy 2.0)
from decimal import Decimal
from sqlalchemy import Numeric
Column(Numeric(10, 2))  # Pour colonnes décimales
```

**Pattern de migration identifié:**
- SQLAlchemy 2.0 supprime imports directs de types Python standard
- Utiliser types Python natifs + types SQLAlchemy SQL pour colonnes
- Vérifier documentation type hierarchy avant imports

#### Pydantic v2 Configuration - BREAKING CHANGES
**Configuration v1→v2:**
```python
# ❌ OBSOLÈTE (Pydantic v1)
class Config:
    env_file = ".env"
    allow_population_by_field_name = True

# ✅ CORRECT (Pydantic v2)
model_config = {
    "env_file": ".env", 
    "populate_by_name": True,
}
```

### Workflow Développement Production - ÉTABLI

#### Local → Production Pattern
1. **Développement Local:** Modifications frontend/backend localement
2. **Test Local:** Validation fonctionnelle sur localhost
3. **Git Push:** Commits atomiques avec descriptions détaillées
4. **Auto-Deploy Render:** Déploiement automatique depuis GitHub
5. **Validation Production:** Test sur URL .onrender.com

#### Debug Deployment Pattern - MÉTHODOLOGIE VALIDÉE
**Approche systématique:**
1. **Logs Analysis:** Identifier l'erreur précise dans deployment logs
2. **Documentation Research:** Consulter documentation officielle
3. **Targeted Fix:** Correction ciblée sans sur-engineering
4. **Preventive Analysis:** Anticiper problèmes similaires
5. **Commit & Test:** Push immédiat + validation

### Configuration Technologies - STACK VALIDÉ

#### Frontend React Minimal
**Structure TypeScript + Vite validée:**
```
frontend/
├── package.json              # React 18 + @types/node requis
├── vite.config.ts            # Pas de terser (utiliser esbuild)
├── tsconfig.app.json         # types: ["vite/client"] requis
├── src/vite-env.d.ts         # Types import.meta.env
└── src/App.tsx               # Backend connectivity check
```

**Patterns TypeScript Render:**
- `@types/node` requis pour Buffer, NodeJS types
- `vite/client` types pour import.meta.env
- Éviter terser minifier (dependencies extra)

#### Backend FastAPI Production
**Dependencies critiques production:**
```
sqlalchemy>=2.0.0            # v2 syntax obligatoire
pydantic>=2.0.0               # v2 config syntax
pydantic-settings>=2.0.0      # BaseSettings séparé
keyring>=24.0.0               # Production secrets
psycopg2-binary>=2.9.0        # PostgreSQL Render
```

### Architecture Monorepo - PATTERNS VALIDÉS

#### Structure Projet Production
```
/
├── render.yaml               # Blueprint configuration
├── backend/                  # rootDir backend
│   ├── app/
│   │   ├── core/settings.py  # ✅ Pydantic v2 principal
│   │   ├── config/settings.py # ✅ Compatibility redirect
│   │   └── models/           # SQLAlchemy 2.0 syntax
│   └── requirements.txt      
└── frontend/                 # rootDir frontend
    ├── src/                  # React + TypeScript
    └── package.json          # @types/node included
```

#### Import Compatibility Pattern
**Backward compatibility strategy:**
```python
# config/settings.py (compatibility)
from ..core.settings import get_settings
settings = get_settings()

# Permet imports existants sans breaking changes
```

### Environment Management Production - RENDER SPECIFIQUE

#### Variables Configuration
```yaml
# render.yaml pattern
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: arbitragevault-db
      property: connectionString
  - key: KEEPA_API_KEY
    sync: false                # User input required
  - key: APP_ENV
    value: production          # Environment detection
```

#### CORS Production
**Configuration auto-adaptive:**
```python
cors_allowed_origins: List[str] = Field(default=[
    "http://localhost:5173",   # Development
    "http://localhost:5174", 
    "*"                        # Production wildcard
])
```

### Troubleshooting Playbook Production - MÉTHODOLOGIE

#### Deployment Failures Pattern
1. **CORS Issues:** Browser blocks, logs vides backend
2. **Import Errors:** Version conflicts libraries (SQLAlchemy, Pydantic)
3. **Path Issues:** Monorepo rootDir vs cd commands
4. **TypeScript:** Missing @types packages ou configurations
5. **Dependencies:** Missing optional dependencies (terser, keyring)

#### Error Resolution Strategy
**Documentation-First Approach:**
- Consulter documentation officielle avant corrections
- Rechercher patterns sur community forums
- Appliquer corrections préventives basées sur bonnes pratiques
- Commits atomiques pour traçabilité

### Performance Production - RENDER CONSTRAINTS

#### Coûts Anticipés
- **Backend Starter:** ~$7/mois (service actif)
- **Database Free:** PostgreSQL 256MB (30 jours limite)
- **Frontend Static:** Gratuit
- **Alternative:** Supabase Free database (économie $6/mois)

#### Scaling Considerations
- **Build Time:** TypeScript + Python dependencies ~2-3 minutes
- **Auto-Deploy:** Trigger sur chaque git push main
- **Resource Limits:** Starter plan 512MB RAM, 0.5 CPU

### Testing Strategy Production - WORKFLOW E2E

#### Validation End-to-End
**Test sequence validé:**
1. **Frontend Health:** Landing page + backend connectivity check
2. **Backend API:** Endpoints health check
3. **Database:** PostgreSQL connection + table creation
4. **Keepa Integration:** API calls avec clés production
5. **Workflow Complet:** Upload → Config → Analysis → Results

#### Monitoring Pattern
**Status checking automatique:**
- Frontend teste backend connectivity via fetch()
- Health endpoints exposés pour monitoring
- Logs centralisés Render dashboard

### Migration Patterns - TECHNOLOGY UPDATES

#### SQLAlchemy 1.x → 2.0
**Breaking changes identifiés:**
- `from sqlalchemy import Decimal` → supprimé
- Utiliser `from decimal import Decimal` + `sqlalchemy.Numeric`
- Settings structure simplifiée (pas database.* nested)

#### Pydantic v1 → v2  
**Breaking changes identifiés:**
- `BaseSettings` déplacé vers `pydantic-settings`
- `class Config:` → `model_config = {}`
- `allow_population_by_field_name` → `populate_by_name`

#### React TypeScript Vite
**Configuration production-ready:**
- `types: ["vite/client"]` pour import.meta.env
- `@types/node` pour Buffer/NodeJS types
- `vite-env.d.ts` pour environment variables

---

**Dernière mise à jour:** 14 septembre 2025 - Déploiement Render en cours  
**Status:** Frontend déployé ✅, Backend corrections SQLAlchemy 2.0 appliquées
**Prochaine étape:** Validation système complet production + test workflow utilisateur