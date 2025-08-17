# ArbitrageVault - Règles et Spécifications Projet

## Vue d'Ensemble de l'Application

ArbitrageVault est un outil de recherche d'opportunités d'arbitrage de livres qui se connecte à l'API Keepa pour identifier, filtrer et prioriser les offres de livres rentables. L'application analyse les manuels scolaires et autres livres en traitant des listes ISBN/ASIN, calculant le potentiel de profit et la vélocité de vente, puis présente les opportunités à travers deux vues stratégiques : Profit Hunter (focus profit maximum) et Velocity (focus rotation rapide).

## Architecture Technique

### Stack Technologique
- **Backend** : FastAPI + PostgreSQL + SQLAlchemy
- **Frontend** : React + TypeScript + Tailwind CSS
- **Intégrations** : Keepa API, OpenAI API, Google Sheets API
- **Déploiement** : Docker + Docker Compose

### Structure des Dossiers
```
arbitragevault_bookfinder/
├── .memex/
│   └── rules.md                    # Ce fichier
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # Point d'entrée FastAPI
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py         # Configuration app
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py         # Modèles d'analyse
│   │   │   ├── user.py             # Modèles utilisateur
│   │   │   └── batch.py            # Modèles de batch
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── keepa_integration.py # Intégration Keepa
│   │   │   ├── openai_service.py   # Service OpenAI
│   │   │   └── google_sheets.py    # Service Google Sheets
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── calculations.py     # Logique de calcul
│   │   │   ├── auth.py             # Authentification
│   │   │   └── database.py         # Configuration DB
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── analysis.py         # Routes d'analyse
│   │       ├── auth.py             # Routes auth
│   │       └── export.py           # Routes export
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── Analysis/
│   │   │   ├── Results/
│   │   │   └── Common/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Rôles Utilisateur & Contrôle d'Accès

### Rôle Admin
- Configurer les clés API et connexions système
- Créer et gérer les profils de stratégie avec seuils personnalisés
- Accéder aux métriques de performance système et statistiques d'utilisation
- Voir les logs d'erreur complets et l'historique des batchs
- Définir les critères de scoring par défaut pour l'organisation

### Rôle Sourcer
- Saisir des listes ISBN/ASIN via saisie texte ou upload CSV
- Accéder aux vues d'analyse Profit Hunter et Velocity
- Générer des shortlists alimentées par IA avec raisonnement
- Exporter les résultats filtrés vers CSV ou Google Sheets
- Marquer les opportunités comme Buy/Watch/Pass pour suivi
- Voir l'historique personnel des batchs et relancer des analyses précédentes

## Interface Utilisateur Principale

### 1. Dashboard Principal & Historique des Batchs
- **Vue d'ensemble historique** : Table propre des analyses précédentes
- **Colonnes** : Date, Nom Batch, Items Traités, Taux de Succès, Profil Utilisé, Statut
- **Actions par batch** : "Voir Résultats", "Re-lancer", "Exporter Encore", "Dupliquer"
- **Cartes de stats rapides** : Total analyses du mois, taux moyen succès, opportunités les plus rentables

### 2. Interface Configuration Nouvelle Analyse
- **Section saisie ISBN/ASIN** : Zone de texte large avec validation en temps réel
- **Upload CSV** : Zone drag-and-drop avec validation format
- **Sélection profil stratégie** : Cartes visuelles au lieu de dropdown
- **Contrôles lancement** : Bouton "Démarrer Analyse" avec temps estimé

### 3. Tableau de Bord Progression Temps Réel
- **Barre de progression** : Pourcentage et indicateur visuel de completion
- **Compteurs en direct** : "Traitement item 67 sur 150"
- **Suivi erreurs** : Log d'erreurs extensible avec raisons spécifiques
- **Annulation & récupération** : Bouton "Annuler" qui préserve les résultats complétés

### 4. Dashboard Résultats - Vues Stratégiques Duales

#### Vue Profit Hunter
- **Table triable** : Titre Livre, Prix Buy Box Actuel, Prix Vente Cible, Profit Net, ROI %, Prix Max Achat, Niveau Risque
- **Codage couleur** : Lignes vertes (achat fort), jaunes (considérer), rouges (passer)
- **Filtres avancés** : Curseurs de plage pour ROI Min, Profit Min, Plage Prix
- **Stats résumé** : "Affichage 23 sur 150 items • Profit Potentiel Total : 1 247 $"

#### Vue Velocity
- **Table triable** : Titre Livre, Rang BSR, Probabilité Rotation, Quantité Stock Suggérée, Timeline Liquidation
- **Indicateurs visuels** : Rapide (flèche verte haut), Moyen (cercle jaune), Lent (flèche rouge bas)
- **Filtres spécifiques vélocité** : Probabilité Rotation Min, Jours Liquidation Max
- **Résumé** : "31 items • Liquidation Moy : 28 jours • Mouvements Rapides : 12"

### 5. Détail Item & Transparence Analyse
- **Détails ligne extensible** : Clic sur ligne révèle panneau d'analyse détaillé
- **Graphiques mini** : Historique prix 90 jours, historique BSR avec indicateurs vélocité
- **Décomposition calcul** : "ROI = (24,99 $ vente - 3,50 $ frais - 15,00 $ coût) / 15,00 $ = 43 %"
- **Facteurs de risque** : "Haute volatilité prix", "Historique ventes limité"
- **Actions par item** : Boutons "Acheter", "Surveiller", "Passer"

### 6. Générateur Shortlist IA
- **Configuration shortlist** : Bouton "Générer Shortlist IA" proéminent
- **Options** : "Top 5", "Top 10", "Top 15" opportunités
- **Focus stratégie** : Curseur "Profit Pur" ← → "Équilibré" ← → "Vélocité Pure"
- **Affichage shortlist** : Layout basé cartes avec images couvertures
- **Raisonnement IA** : Ton conversationnel avec scoring de confiance

### 7. Export & Gestion Données
- **Sélection format** : "Téléchargement CSV", "Google Sheets", "Format Excel"
- **Options filtrage contenu** : "Tous Items", "Gagnants Seulement", "Items Marqués"
- **Personnalisation colonnes** : Cases à cocher pour inclure/exclure champs
- **Historique export** : Options re-téléchargement

## Intégrations APIs Tierces

### Intégration API Keepa
**Objectif** : Source de données principale pour analytics marketplace Amazon
**Données Récupérées** :
- Détails produits par recherche ISBN/ASIN
- Données historiques prix (Buy Box, FBA, FBM)
- Historique Best Seller Rank (BSR) et tendances
- Indicateurs vélocité ventes et patterns de demande
- Calculs frais Amazon et estimations coûts FBA

### API OpenAI
**Objectif** : Générer shortlists intelligentes avec raisonnement lisible
**Capacités Requises** :
- Analyser patterns données numériques et identifier top opportunités
- Générer explications concises, orientées business
- Fournir output structuré pour présentation UI cohérente
- Adapter raisonnement selon focus stratégie utilisateur

### Intégration API Google Sheets
**Objectif** : Export direct vers Google Sheets pour workflows collaboratifs
**Fonctionnalités Requises** :
- Authentification OAuth 2.0 pour comptes Google utilisateurs
- Création spreadsheet avec formatage approprié et headers
- Écriture données avec support formules et formatage conditionnel

## Logique de Calcul & Flux de Données

### Calcul Métriques Core

#### Analyse Profit
```
Profit Net = Prix Vente Estimé - Frais Amazon - Coût Achat - Buffer Sécurité
ROI = Profit Net / Coût Achat × 100
Buffer Sécurité = 5-8% du prix de vente (configurable)
Calcul Frais = Frais FBA + frais référence Amazon + coûts stockage
```

#### Scoring Vélocité
```
Probabilité Rotation = Stabilité BSR + patterns ventes historiques + consistance demande
Timeline Liquidation = Jours moyens entre ventes basé sur BSR et catégorie
Stabilité Demande = Volatilité prix + consistance nombre offres + facteurs saisonniers
Suggestion Stock = Quantité conservatrice basée sur vélocité et tolérance risque
```

#### Évaluation Risque
```
Volatilité Prix = Écart-type des prix historiques
Niveau Concurrence = Nombre vendeurs actifs et compétition prix
Consistance Demande = Patterns saisonniers et analyse tendance
Confiance Données = Complétude et fraîcheur des données disponibles
```

## Conventions de Développement

### Modèle BUILD-TEST-VALIDATE
1. **BUILD** : Définir exigences claires avec validation avant codage
2. **TEST** : Construire par petites itérations complètes avec tests immédiats
3. **VALIDATE** : Valider par tests conjoints et retours avant prochaine itération

### Conventions de Code
- **Python** : snake_case pour variables/fonctions, PascalCase pour classes
- **TypeScript** : camelCase pour variables/fonctions, PascalCase pour composants
- **Base de données** : snake_case pour tables et colonnes
- **API** : kebab-case pour endpoints

### Gestion Git
- Branches feature pour nouvelles fonctionnalités
- Commits fréquents et descriptifs
- Messages de commit se terminent par : "\n\n🤖 Generated with [Memex](https://memex.tech)\nCo-Authored-By: Memex <noreply@memex.tech>"

### Tests Requis
- Tests unitaires pour logique de calcul
- Tests d'intégration pour APIs externes
- Tests end-to-end pour workflows principaux
- Validation immédiate après chaque étape de développement

## Workflows Utilisateur Clés

### Workflow Principal : Analyse Standard Livres
1. Navigation dashboard → "Nouvelle Analyse"
2. Coller 75 codes ISBN dans zone saisie
3. Sélectionner profil "Profit Hunter - Équilibré"
4. Ajouter nom batch et cliquer "Démarrer Analyse"
5. Surveiller progression temps réel
6. Voir résultats onglet Profit Hunter
7. Appliquer filtres ROI >35%
8. Examiner détails top 5 opportunités
9. Marquer items comme "Acheter"/"Surveiller"
10. Générer shortlist IA pour validation finale
11. Exporter items marqués vers CSV

### Workflow Secondaire : Comparaison Stratégies
1. Ouvrir batch existant depuis historique
2. Réviser résultats vue Profit Hunter
3. Basculer vue Velocity pour même données
4. Utiliser toggle "Comparer Vues"
5. Créer profil personnalisé mixant approches
6. Lancer nouvelle analyse même liste ISBN
7. Comparer résultats côte à côte
8. Exporter analyse comparative

## Principes Expérience Utilisateur

### Transparence et Contrôle
- Chaque calcul inclut explications claires de dérivation résultats
- Accès toujours possible aux données sous-jacentes
- Interface privilégie clarté visuelle avec codage couleur cohérent
- Indicateurs de progression intuitifs et boutons d'action proéminents

### Système Double Vue
- Évaluer opportunités identiques via différentes lentilles stratégiques
- Compréhension trade-offs profit maximum vs rotation rapide
- Pas de re-analyse coûteuse nécessaire

### Tolérance aux Erreurs
- Échecs API/ISBNs invalides n'empêchent jamais accès résultats items traités avec succès
- Feedback clair sur problèmes + options de récupération
- Tous résultats incluent métadonnées : collecte données, seuils appliqués, niveau confiance

### Intégration Workflow
- Export s'intègre parfaitement workflows achat/gestion inventaire existants
- Fonctionnalité historique batch permet construire sur analyses précédentes
- Suivi processus décisionnel dans le temps

## Variables d'Environnement Requises

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/arbitragevault

# APIs
KEEPA_API_KEY=your_keepa_api_key
OPENAI_API_KEY=your_openai_api_key

# Google Sheets
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Application
SECRET_KEY=your_jwt_secret_key
DEBUG=false
ENVIRONMENT=production
```

## Points de Validation Critiques

### Avant Chaque Itération
- [ ] Fonctionnalité complète testée end-to-end
- [ ] Interface utilisateur validée pour intuitivité
- [ ] Performance API vérifiée sous charge typique
- [ ] Gestion d'erreur testée pour cas limites
- [ ] Export/import fonctionnel avec données réelles

### Tests de Régression
- [ ] Calculs ROI cohérents avec versions précédentes
- [ ] Intégration Keepa API stable et fiable
- [ ] Export données maintient intégrité formatage
- [ ] Authentification utilisateur sécurisée
- [ ] Historique batch préservé correctement

### Métriques de Succès
- Temps de réponse API < 2 secondes pour batches < 100 items
- Taux de succès > 95% pour requêtes Keepa API valides
- Interface utilisateur responsive < 1 seconde interactions
- Export données sans perte informations critiques
- Zéro perte de données lors pannes système

---

**Dernière mise à jour** : 17 août 2025
**Version règles** : 1.0.0