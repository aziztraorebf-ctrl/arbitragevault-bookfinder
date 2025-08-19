# ArbitrageVault - Bookfinder

## Vue d'Ensemble

ArbitrageVault est un outil d'analyse d'opportunités d'arbitrage de livres qui utilise l'API Keepa pour identifier des offres rentables sur Amazon. L'application traite des listes ISBN/ASIN et présente les résultats via deux vues stratégiques complémentaires.

## Fonctionnalités Principales

- **Analyse Dual-View** : Profit Hunter (focus profit) et Velocity (focus rotation)
- **Intégration Keepa API** : Données temps réel d'Amazon Marketplace
- **IA Shortlist** : Recommandations intelligentes avec raisonnement
- **Export Multi-format** : CSV, Excel, Google Sheets
- **Historique Batch** : Suivi et re-lancement d'analyses précédentes

## Architecture

- **Backend** : FastAPI + PostgreSQL + SQLAlchemy
- **Frontend** : React + TypeScript + Tailwind CSS
- **APIs** : Keepa, OpenAI, Google Sheets
- **Déploiement** : Docker + Docker Compose

## Architecture de Données

### Modèles Implémentés
- **Batch** : Job d'analyse avec métadonnées et suivi de progression
- **Analysis** : Résultats d'analyse individuelle par livre avec métriques financières

### Features Techniques
- Support multi-tenant avec isolation par user_id
- Calculs financiers précis (Decimal) pour ROI et profits
- Migrations Alembic avec compatibilité SQLite/PostgreSQL
- Pattern Repository pour abstraction données
- Logging complet des opérations

## Structure Projet

```
arbitragevault_bookfinder/
├── .memex/
│   └── rules.md                    # Spécifications complètes
├── backend/
│   ├── app/
│   │   ├── models/                 # ✅ Modèles SQLAlchemy
│   │   │   ├── batch.py           # Gestion des jobs d'analyse
│   │   │   └── analysis.py        # Métriques par livre
│   │   ├── repositories/           # ✅ Pattern Repository
│   │   │   ├── batch_repository.py
│   │   │   └── analysis_repository.py
│   │   ├── core/
│   │   │   └── database.py         # Configuration DB
│   │   ├── routers/               # 🚧 Routes FastAPI
│   │   └── api/                   # 🚧 Intégrations externes
│   ├── migrations/                # ✅ Alembic migrations
│   └── requirements.txt
├── frontend/                      # 🚧 Interface React
├── docker-compose.yml
└── README.md
```

## Installation & Setup

### Prérequis
- Python 3.11+
- PostgreSQL 13+
- Git

### Setup Backend
```bash
cd backend

# Créer environnement virtuel
uv venv
.venv\Scripts\activate.bat

# Installer dépendances
uv pip install -r requirements.txt

# Configuration base de données
cp .env.example .env
# Éditer DATABASE_URL et autres variables

# Migrations
alembic upgrade head

# Tests (optionnel)
python -m pytest tests/
```

### Configuration Docker
```bash
# Setup complet avec Docker
docker-compose up -d

# Voir logs
docker-compose logs -f backend
```

## Configuration

Variables d'environnement requises :
- `KEEPA_API_KEY` : Clé API Keepa
- `OPENAI_API_KEY` : Clé API OpenAI
- `DATABASE_URL` : URL PostgreSQL
- `GOOGLE_CLIENT_*` : Credentials Google Sheets

## API Backend Disponible

### Modèles de Données
```python
# Batch : Gestion des jobs d'analyse
- id, user_id, name, total_items
- items_processed, status (PENDING/RUNNING/DONE/FAILED)  
- strategy_snapshot, created_at, updated_at

# Analysis : Métriques par livre
- id, batch_id, isbn, asin
- buy_price, expected_sale_price, fees
- profit, roi_percentage, velocity_score
- keepa_data_raw, created_at
```

### Repositories Disponibles
```python
# BatchRepository
batch_repo.create(batch_data)
batch_repo.get_by_user_id(user_id)
batch_repo.get_batch_stats(batch_id)
batch_repo.update_progress(batch_id, progress)

# AnalysisRepository  
analysis_repo.bulk_create_analyses(analyses_data)
analysis_repo.get_strategic_view(batch_id, "profit"|"velocity")
analysis_repo.filter_by_roi_range(batch_id, min_roi, max_roi)
analysis_repo.get_performance_summary(batch_id)
```

## Usage Prévu (Frontend)

1. Coller liste ISBN/ASIN
2. Sélectionner profil stratégie
3. Lancer analyse
4. Explorer résultats Profit Hunter / Velocity
5. Générer shortlist IA
6. Exporter données

## Documentation

Documentation complète disponible dans `.memex/rules.md`

## Status Développement

🚧 **En cours de développement**

### Couche Données ✅ Complète
- [x] Modèles SQLAlchemy (Batch, Analysis)
- [x] Migrations Alembic avec cross-DB support
- [x] Repositories avec filtrage avancé
- [x] Tests complets et validation
- [x] Support multi-tenant

### Prochaines Étapes 🚧
- [ ] Routes FastAPI pour CRUD opérations
- [ ] Intégration API Keepa
- [ ] Service d'analyse des métriques
- [ ] Interface utilisateur React
- [ ] Authentification et sécurité

### Backend Core 🚧 En cours
- [ ] Routes d'analyse des livres
- [ ] Système de calcul ROI/profit
- [ ] Gestion des erreurs API
- [ ] Export vers formats multiples

### Frontend Interface 🚧 À venir
- [ ] Dashboard principal
- [ ] Vues Profit Hunter / Velocity
- [ ] Générateur de shortlist IA
- [ ] Historique des batchs

## Développement

### Règles Projet
- **Méthodologie** : BUILD-TEST-VALIDATE pour chaque feature
- **Git** : Commits fréquents, branches feature, messages descriptifs
- **Tests** : Validation immédiate après chaque étape
- **Documentation** : Specs complètes dans `.memex/rules.md`

### Base de Données
```bash
# Migration courante
alembic current

# Créer nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head
```

### Tests Backend
```bash
# Tester repositories
python -c "from backend.app.repositories.batch_repository import BatchRepository; print('✅ Repository OK')"

# Valider modèles
python -c "from backend.app.models import Batch, Analysis; print('✅ Models OK')"
```

## Contact

Projet développé avec [Memex](https://memex.tech)