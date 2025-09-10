# ArbitrageVault - Règles et Spécifications Projet

## Frontend Development Phase - Complete System Architecture

### Contexte Actuel
**Backend Status:** v1.6.1 - Production ready avec toutes les fonctionnalités core implémentées
**Frontend Phase:** Démarrage développement interface utilisateur complète
**Approche:** BUILD-TEST-VALIDATE avec développement local + deploy tests périodiques sur Render

### Architecture Backend Complète (Validée)

#### Modules Fonctionnels Implémentés
1. **Niche Discovery Service (v1.6.1)**
   - Découverte automatique de niches rentables via analyse Keepa
   - Scoring intelligent avec métriques (BSR, marge, concurrence, stabilité)
   - APIs: `/api/niche-discovery/analyze`, `/api/niche-discovery/categories`
   - Export vers CSV et AutoSourcing

2. **Niche Bookmarking System (v1.6.1)** 
   - Sauvegarde niches prometteuses avec paramètres complets
   - CRUD complet avec pagination et gestion utilisateur
   - APIs: `/api/bookmarks/niches/*` (6 endpoints)
   - Workflow: Découverte → Bookmark → "Mes Niches" → Relance analyse

3. **AutoScheduler Module (v1.7.0)**
   - Automation programmée (8h/15h/20h) avec contrôle temps réel
   - APIs: 8 endpoints de contrôle et monitoring
   - Configuration JSON dynamique, métriques performance

4. **AutoSourcing Discovery (v1.6.0)**
   - Discovery automatique produits avec Keepa Product Finder
   - 13 endpoints, profiles système, action workflow (Buy/Favorite/Ignore)
   - "Opportunity of the Day" avec prioritisation intelligente

5. **Stock Estimate Module (v1.8.0)**
   - Évaluation stock en 2 secondes avec price-targeted analysis
   - Smart caching 24h TTL, 3 endpoints

6. **Strategic Views Service (v1.9.1)**
   - 5 vues stratégiques: Profit Hunter, Velocity, Cashflow Hunter, Balanced Score, Volume Player
   - Advanced scoring 6 dimensions (0-100 scale)

7. **Analyse Manuelle (Core)**
   - Upload CSV ou saisie ASINs manuels
   - Multi-strategy analysis avec critères personnalisables
   - APIs: `/api/v1/keepa/analyze`, `/api/v1/keepa/batch-analyze`

### Stack Technique Frontend (Décidé)

#### Technologies Core
- **Framework:** React + TypeScript + Vite
- **Styling:** Tailwind CSS (Light Modern Professional theme)
- **State Management:** @tanstack/react-query + React hooks
- **Icons:** Lucide React (pas d'images de couvertures livres)
- **Charts:** Recharts pour visualisations
- **Animations:** Framer Motion
- **Déploiement:** Render (full-stack avec backend)

#### Configuration Deployment-Ready
```yaml
# render.yaml structure validée
services:
  - frontend (Node.js + Vite)
  - backend (Python + FastAPI)
  - database (PostgreSQL)
```

#### Environment Management Pattern
```typescript
// Configuration automatique local ↔ production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

### Stratégie Développement Hybride

#### Approche Validée : Local Development + Render Deploy Tests
- **90% Local Development:** Développement quotidien sur localhost (performance max)
- **10% Deploy Tests:** Tests périodiques sur Render (validation production)
- **Séquence:** Week 1-2 local → Deploy test → Week 3-4 local → Deploy test → etc.

#### Workflow Développement
```bash
# Daily (Local)
npm run dev  # Frontend localhost:5173
uvicorn app.main:app --reload  # Backend localhost:8000

# Weekly (Render Test)
npm run build && git push origin main
# Test production URL → Noter issues → Continue local
```

### Architecture Frontend (Structure Complète)

#### Navigation Principale
```
🏠 Dashboard (Hub central)
├── 📋 Analyse Manuelle      ← Upload CSV/ASINs (PRIORITÉ 1)
├── 🔍 Niche Discovery       ← Découverte automatique niches
├── 📚 Mes Niches           ← Bookmarking & gestion
├── 🤖 AutoScheduler        ← Contrôle automation
├── 📊 AutoSourcing         ← Résultats discovery
├── 📈 Analyse Stratégique  ← 5 vues stratégiques
├── 📦 Stock Estimates      ← Vérification disponibilité
└── ⚙️ Configuration       ← Paramètres système
```

#### Composants Architecture
```
src/components/
├── Dashboard/              # Hub central + navigation
├── ManualAnalysis/         # Upload CSV/ASINs + critères
├── NicheDiscovery/         # Configuration + résultats discovery
├── NicheBookmarking/       # "Mes Niches" + CRUD operations
├── AutoScheduler/          # Control center automation
├── AutoSourcing/           # Résultats produits + actions
├── StrategicAnalysis/      # 5 vues (Profit/Velocity/etc.)
├── StockEstimate/          # Validation disponibilité
└── Common/                 # Composants partagés
```

### Workflow Utilisateur Complet (Validé)

#### Flow Principal: Analyse → Découverte → Sauvegarde → Automation → Exploitation
1. **Analyse Manuelle:** Upload CSV/ASINs → Validation directe ROI
2. **Niche Discovery:** Découverte automatique niches rentables
3. **Bookmarking:** Sauvegarde niches avec paramètres complets
4. **AutoScheduler:** Automation programmée sur niches sauvées
5. **AutoSourcing:** Exploitation résultats avec actions (Buy/Favorite)
6. **Strategic Views:** Analyse multi-dimensionnelle (5 vues)
7. **Stock Estimate:** Validation scalabilité opportunités

#### Profils Utilisateurs Types
- **Débutant (Sarah):** 20h/semaine → Analyse manuelle + quelques niches
- **Expérimenté (Marc):** 40h/semaine → Pipeline automatisé 400+ ASINs/semaine
- **Équipe (Julie):** Industriel → 1000+ ASINs/semaine, 47 niches sous surveillance

### Design System (Icon-Based)

#### Décision Critique: Pas d'Images Couvertures Livres
- **Problème:** Complexité APIs images (Amazon/Open Library)
- **Solution:** Interface icon-based avec Lucide React
- **Avantage:** Développement 3x plus rapide, performance max, look professionnel

#### Theme: Light Modern Professional
- **Couleurs:** Fond blanc #ffffff, cartes blanches avec shadows, gradients bleu/violet
- **Palette:** Primary #3B82F6 (blue), Success #10B981 (green), Accent #8B5CF6 (violet)
- **Typography:** Inter font, texte sombre pour lisibilité
- **Layout:** Cards blanches shadow-lg, backgrounds colorés, tables responsive
- **Animations:** Subtle micro-interactions, hover effects modernes
- **Style:** Clean, accessible, business-focused avec touches colorées

### Séquence Développement (Finalisée)

#### Phase 1: Analyse Manuelle (Week 1-2) - PRIORITÉ
- Upload CSV/ASINs avec drag & drop
- Configuration stratégies + critères personnalisables  
- Progress tracking + résultats multi-vues
- Export fonctionnel + validation stock

#### Phase 2: Niche Discovery (Week 3-4)
- Interface configuration critères discovery
- Sélection catégories Keepa + progression temps réel
- Résultats scorés + actions sauvegarde

#### Phase 3: Niche Bookmarking (Week 5-6)
- "Mes Niches" avec CRUD complet + pagination
- Modal "Relancer analyse" avec paramètres restaurés
- Suivi évolution scores dans le temps

#### Phase 4: AutoScheduler Control (Week 7-8)
- Dashboard contrôle avec enable/disable temps réel
- Configuration horaires + skip dates
- Métriques performance + logs système

#### Phase 5: AutoSourcing Results (Week 9-10)
- Interface résultats avec filtres avancés
- Actions par produit (Buy/Favorite/Ignore/Analyze)
- "Opportunity of the Day" + management

#### Phase 6: Strategic Analysis (Week 11-12)
- 5 vues stratégiques complètes avec toggle
- Breakdown scoring détaillé par dimension
- Export par vue + comparaisons

### API Integration Patterns

#### Backend Connections (Par Module)
```typescript
// Analyse Manuelle
POST /api/v1/keepa/batch-analyze
POST /api/v1/strategic-views/analyze

// Niche Discovery  
POST /api/niche-discovery/analyze
GET /api/niche-discovery/categories

// Bookmarking
POST /api/bookmarks/niches
GET /api/bookmarks/niches
GET /api/bookmarks/niches/{id}/filters

// AutoScheduler
GET/POST /api/v1/autoscheduler/*

// AutoSourcing
GET /api/v1/autosourcing/latest
POST /api/v1/autosourcing/run-custom

// Stock Estimate
GET /api/v1/products/{asin}/stock-estimate
```

### Conventions Code Frontend

#### Structure Composants
- **Taille max:** <50 lignes par composant
- **Pattern:** Un fichier par composant majeur
- **Types:** Interfaces TypeScript pour toutes props
- **State:** React Query pour server state, useState pour local

#### Error Handling
- **Toast notifications** pour feedback utilisateur
- **Error boundaries** pour composants critiques  
- **Fallback UI** pour états de chargement
- **Retry logic** pour appels API

#### Testing Strategy
- **Unit tests** pour logique critique
- **Integration tests** pour workflows complets
- **E2E validation** avant chaque deploy test

### Déploiement Render (Production)

#### Configuration Validée
- **Auto-deploy** via GitHub push
- **Environment variables** automatiques via fromService
- **Database** PostgreSQL managée incluse
- **Scaling** automatique pour pics de charge
- **Monitoring** health checks intégrés

#### Performance Targets
- **Single Analysis:** <2s response time
- **Batch Processing:** 50 produits <30s
- **UI Responsiveness:** <100ms interactions
- **Build Time:** <3 minutes deploy complet

### Secrets Management

#### Pattern Established
- **Keyring usage:** KEEPA_API_KEY via Memex secrets
- **Variations:** ALL_CAPS, lowercase, mixed case testing
- **Security:** Jamais d'affichage secrets dans logs/output
- **Validation:** Format verification avant usage

### Business Logic Integration

#### Data Flows Validés
- **Prix:** Division par 100 (centimes → euros)
- **BSR:** Extraction via csv[3] (champ SALES)  
- **Categories:** IDs Keepa standards (4142 = Engineering)
- **Scoring:** Échelle 0-100 normalisée sur 6 dimensions

### Version Control Patterns

#### Commit Strategy
- **Atomic commits** par fonctionnalité
- **Messages descriptifs** avec contexte business
- **Signature Memex:** "Generated with [Memex](https://memex.tech)"
- **Branching:** Direct main pour features complètes (approche pragmatique)

---

**Dernière mise à jour:** 9 janvier 2025 - Design System mis à jour vers Light Theme moderne
**Status:** Backend v1.6.1 production ready, Frontend Phase 1 ready to start
**Prochaine étape:** Lancement développement Phase 1 (Analyse Manuelle)