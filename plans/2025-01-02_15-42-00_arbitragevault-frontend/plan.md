# Plan de Construction Front-end ArbitrageVault

## Spec Provenance
- **Créé le** : 2025-01-02 15:42:00 UTC
- **Projet** : ArbitrageVault - Interface utilisateur de recherche d'opportunités d'arbitrage de livres
- **Approche** : Construction page par page avec validation BUILD-TEST-VALIDATE
- **Utilisateur unique** : Pas d'authentification nécessaire initialement

## Spec Header

### Nom du Projet
**Front-end ArbitrageVault** - Interface utilisateur pour l'analyse d'opportunités d'arbitrage de livres

### Smallest Scope (MVP)
1. **Page Dashboard** : Vue d'ensemble et historique des batchs d'analyse
2. **Page Nouvelle Analyse** : Configuration et lancement d'analyses ISBN/ASIN
3. **Page Progression** : Suivi temps réel des analyses en cours
4. **Page Résultats** : Vues Profit Hunter et Velocity avec filtres
5. **Composants Modaux** : Détails item, shortlist IA, export

### Non-Goals (Pour plus tard)
- Système d'authentification multi-utilisateurs
- Application mobile
- Notifications push
- Intégration temps réel avec d'autres plateformes

## Paths to supplementary guidelines
- **Design System** : https://raw.githubusercontent.com/memextech/templates/refs/heads/main/design/dark-modern-professional.md
- **Tech Stack** : https://raw.githubusercontent.com/memextech/templates/refs/heads/main/stack/react_website.md

## Decision Snapshot

### Stack Technique Choisi
- **Framework** : React + TypeScript + Vite
- **Styling** : Tailwind CSS (thème dark-modern-professional)
- **State Management** : @tanstack/react-query + React hooks
- **Animations** : Framer Motion
- **Icons** : Lucide React
- **Charts** : Recharts
- **Déploiement** : Netlify

### Architecture Composants
```
src/
├── components/
│   ├── Dashboard/          # Page principale
│   ├── Analysis/           # Configuration nouvelle analyse
│   ├── Progress/           # Suivi temps réel
│   ├── Results/            # Vues Profit Hunter & Velocity  
│   ├── Modals/            # Détails, IA shortlist, export
│   └── Common/            # Composants partagés
├── hooks/                 # Custom hooks
├── services/             # API calls
├── types/               # TypeScript interfaces
└── utils/              # Fonctions utilitaires
```

## Architecture at a Glance

### Flow Utilisateur Principal
```
Dashboard → Nouvelle Analyse → Progression → Résultats → Actions
    ↑                                            ↓
    ←──── Export/Sauvegarde ←─── Détails Item ←──
```

### Communication Backend
- **Base URL** : `http://localhost:8000/api`
- **Authentification** : Aucune (single user)
- **Format** : JSON REST API
- **Gestion erreurs** : Toast notifications + fallback UI

## Implementation Plan

### 🎯 Phase 1 : Dashboard Principal (Semaine 1)

#### Page: `/dashboard`
**Fonctions Core :**
- Affichage historique des batchs d'analyse
- Cartes de statistiques rapides
- Navigation vers nouvelle analyse
- Actions sur batchs existants (voir résultats, relancer, dupliquer)

**Design Spécifications :**
- **Couleurs** : Fond #0a0a0a, cartes #141414, texte #ffffff
- **Typography** : Inter font, h1 48px bold, body 16px regular
- **Layout** : Grid 12 colonnes, cards 24px padding
- **Animations** : Hover effects sur cartes (scale 1.01x, shadow lift)

**Composants à créer :**
```typescript
// components/Dashboard/
├── DashboardLayout.tsx     # Layout principal
├── StatsCards.tsx          # Cartes statistiques
├── BatchHistoryTable.tsx   # Table historique
├── QuickActions.tsx        # Actions rapides
└── index.tsx              # Export barrel
```

**Backend Integration :**
```typescript
// Endpoints requis
GET /api/batches              # Liste des batchs
GET /api/stats/summary        # Stats dashboard
POST /api/batches/{id}/rerun  # Relancer analyse
DELETE /api/batches/{id}      # Supprimer batch
```

**Validation & Tests :**
- [ ] Table responsive avec tri/filtres
- [ ] Actions batch fonctionnelles
- [ ] Stats en temps réel
- [ ] Navigation fluide

---

### 🎯 Phase 2 : Configuration Nouvelle Analyse (Semaine 2)

#### Page: `/analysis/new`
**Fonctions Core :**
- Zone saisie ISBN/ASIN avec validation
- Upload CSV drag-and-drop
- Sélection profil stratégie (cartes visuelles)
- Configuration options avancées
- Lancement analyse avec estimation temps

**Design Spécifications :**
- **Layout** : Formulaire step-by-step ou sections collapsibles
- **Validation** : Temps réel avec messages d'erreur contextuels  
- **Upload** : Zone drag-drop stylisée avec preview fichiers
- **Profils** : Cards avec icônes et descriptions

**Composants à créer :**
```typescript
// components/Analysis/
├── AnalysisForm.tsx        # Formulaire principal
├── ISBNInput.tsx           # Zone saisie ISBN
├── CSVUpload.tsx           # Upload drag-drop
├── StrategySelector.tsx    # Sélection profils
├── AdvancedOptions.tsx     # Options avancées
└── LaunchButton.tsx        # Bouton lancement
```

**Backend Integration :**
```typescript
POST /api/analyses/start    # Démarrer analyse
GET /api/strategies         # Liste profils disponibles
POST /api/validate/isbn     # Validation ISBN batch
```

---

### 🎯 Phase 3 : Suivi Progression Temps Réel (Semaine 3)

#### Page: `/analysis/progress/{batchId}`
**Fonctions Core :**
- Barre progression visuelle avec pourcentage
- Compteurs temps réel (items traités/total)
- Log d'erreurs extensible avec raisons
- Bouton annulation avec préservation résultats
- Redirection automatique vers résultats à completion

**Design Spécifications :**
- **Progress Bar** : Gradient animé, hauteur 8px, coins arrondis
- **Counters** : Typography mono pour nombres
- **Error Log** : Collapsible avec code couleur (warning/error)
- **Real-time** : WebSocket ou polling 2s

**Composants à créer :**
```typescript
// components/Progress/
├── ProgressDashboard.tsx   # Layout principal
├── ProgressBar.tsx         # Barre progression
├── LiveCounters.tsx        # Compteurs temps réel
├── ErrorLog.tsx           # Log d'erreurs
├── CancelButton.tsx       # Annulation
└── ProgressWebSocket.tsx   # Connexion temps réel
```

---

### 🎯 Phase 4 : Dashboard Résultats - Vues Duales (Semaine 4-5)

#### Page: `/results/{batchId}`
**Fonctions Core :**
- **Vue Profit Hunter** : Table triable ROI/Profit focus
- **Vue Velocity** : Table triable BSR/Rotation focus  
- Toggle entre vues avec data persistée
- Filtres avancés (curseurs, checkboxes)
- Actions par ligne (détails, marquer, export sélection)

**Design Spécifications :**
- **Tables** : Alternating rows, sticky headers, tri sur colonnes
- **Codage couleur** : Vert (acheter), Jaune (considérer), Rouge (passer)  
- **Filtres** : Sidebar collapsible avec range sliders
- **Toggle vues** : Tab switcher avec icons descriptifs

**Composants à créer :**
```typescript
// components/Results/
├── ResultsDashboard.tsx    # Layout principal
├── ViewToggle.tsx          # Switcher Profit/Velocity
├── ResultsTable.tsx        # Table réutilisable
├── AdvancedFilters.tsx     # Sidebar filtres
├── RowActions.tsx          # Actions par ligne
├── SummaryStats.tsx        # Stats résumé
└── TableColumns/           # Définitions colonnes
    ├── ProfitColumns.tsx
    └── VelocityColumns.tsx
```

---

### 🎯 Phase 5 : Modales & Actions Avancées (Semaine 6)

#### Composants Modaux
**Fonctions Core :**
- **Détails Item** : Graphiques historiques, décomposition calculs, facteurs risque
- **Shortlist IA** : Configuration, génération, raisonnement conversationnel
- **Export** : Sélection format, colonnes personnalisables, options filtrage

**Composants à créer :**
```typescript
// components/Modals/
├── ItemDetailsModal.tsx    # Détails complets item
├── PriceHistoryChart.tsx   # Graphiques Recharts
├── AIShortlistModal.tsx    # Générateur IA
├── ExportModal.tsx         # Options export
└── BaseModal.tsx           # Modal réutilisable
```

---

### 🎯 Phase 6 : Polish & Optimisation (Semaine 7)

#### Améliorations Finales
- **Performance** : Lazy loading, code splitting, optimisation images
- **UX** : Animations micro-interactions, loading states
- **Responsive** : Tests mobile/tablet, breakpoints
- **Error Handling** : Boundary components, fallback UI
- **Tests** : Unit tests composants critiques

## Verification & Demo Script

### Tests par Phase

**Phase 1 - Dashboard :**
```bash
# Démarrer dev server
npm run dev

# Tests à effectuer
✓ Affichage table historique avec données mock
✓ Cartes stats responsive 
✓ Actions batch (voir détails, relancer)
✓ Navigation vers nouvelle analyse
✓ Responsive mobile/desktop
```

**Phase 2 - Nouvelle Analyse :**
```bash  
✓ Validation ISBN temps réel
✓ Upload CSV avec preview
✓ Sélection profils visuels
✓ Soumission formulaire vers backend
✓ Gestion erreurs validation
```

**Phase 3 - Progression :**
```bash
✓ Connexion WebSocket fonctionnelle
✓ Mise à jour progression en temps réel
✓ Log d'erreurs extensible
✓ Annulation avec préservation données
✓ Redirection automatique completion
```

**Phases 4-6 - Résultats & Modales :**
```bash
✓ Toggle vues Profit/Velocity sans perte données
✓ Filtres avancés avec state persisté
✓ Modales détails avec graphiques Recharts
✓ Export CSV/Google Sheets fonctionnel
✓ Shortlist IA avec raisonnement affiché
```

### Demo Script Complet
```bash
1. Ouvrir Dashboard → voir historique + stats
2. Cliquer "Nouvelle Analyse" → saisir ISBNs 
3. Sélectionner profil → lancer analyse
4. Observer progression temps réel → completion
5. Explorer résultats vue Profit Hunter
6. Toggle vue Velocity → comparer données
7. Appliquer filtres ROI >35%
8. Cliquer détails item → voir graphiques
9. Générer shortlist IA → voir raisonnement
10. Exporter sélection → vérifier CSV
```

## Deploy

### Configuration Production
```bash
# Build optimisé
npm run build

# Deploy Netlify
npm run deploy

# Variables environnement
VITE_API_URL=https://api.arbitragevault.com
VITE_APP_ENV=production
```

### Monitoring & Analytics
- **Erreurs** : Console logging + toast notifications
- **Performance** : Core Web Vitals tracking  
- **Usage** : Analytics sur actions critiques

---

## Prochaines Étapes

1. **Confirmer l'ordre des phases** - Est-ce que cette séquence vous convient ?
2. **Préciser design preferences** - Autres couleurs ou éléments visuels spécifiques ?
3. **Détailler Phase 1** - Prêt à créer le plan détaillé du Dashboard ?

Le plan respecte votre approche BUILD-TEST-VALIDATE avec une page fonctionnelle complète à chaque phase, tests immédiats et connexions backend validées avant de passer à la suivante.