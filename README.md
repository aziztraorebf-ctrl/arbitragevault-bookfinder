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

## Structure Projet

```
arbitragevault_bookfinder/
├── .memex/rules.md         # Spécifications complètes
├── backend/                # API FastAPI
├── frontend/               # Interface React
├── docker-compose.yml      # Configuration déploiement
└── README.md              # Ce fichier
```

## Installation Rapide

```bash
# Cloner et setup
git clone <repo>
cd arbitragevault_bookfinder

# Configurer environnement
cp .env.example .env
# Éditer .env avec tes clés API

# Lancer avec Docker
docker-compose up -d
```

## Configuration

Variables d'environnement requises :
- `KEEPA_API_KEY` : Clé API Keepa
- `OPENAI_API_KEY` : Clé API OpenAI
- `DATABASE_URL` : URL PostgreSQL
- `GOOGLE_CLIENT_*` : Credentials Google Sheets

## Usage Basique

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

- [x] Spécifications définies
- [ ] Backend API core
- [ ] Frontend interface
- [ ] Intégrations APIs
- [ ] Tests et déploiement

## Contact

Projet développé avec [Memex](https://memex.tech)