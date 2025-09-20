# 🚂 Migration vers Railway - Guide Complet

## 📋 Préparation Effectuée

### ✅ Fichiers Supprimés (Render)
- `render.yaml` - Configuration Blueprint Render

### ✅ Fichiers Ajoutés (Railway)
- `railway.json` - Configuration Railway
- `nixpacks.toml` - Configuration build Nixpacks
- `Procfile` - Commande de démarrage
- `.gitignore` mis à jour

## 🚀 Étapes de Migration

### 1. Créer un Compte Railway
- Va sur https://railway.app
- Connecte-toi avec GitHub
- Autoriser l'accès au repository

### 2. Créer un Nouveau Projet
- Cliquer "New Project"
- Sélectionner "Deploy from GitHub repo"
- Choisir `arbitragevault-bookfinder`

### 3. Configuration Automatique
Railway détectera automatiquement :
- ✅ **Python Backend** (via pyproject.toml)
- ✅ **Node.js Frontend** (via package.json)
- ✅ **Monorepo Structure**

### 4. Variables d'Environnement à Configurer

#### Backend Service
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# API Keys
KEEPA_API_KEY=your_keepa_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret

# CORS
FRONTEND_URL=https://your-frontend-domain.railway.app
```

#### Frontend Service
```bash
# API URL
VITE_API_URL=https://your-backend-domain.railway.app
```

### 5. Configuration Base de Données
- Railway propose PostgreSQL intégré
- Ou connecter une base externe
- URL automatiquement générée

## 🔧 Configuration Technique

### Structure Détectée par Railway
```
/
├── backend/          # Service Python (FastAPI + UV)
├── frontend/         # Service Node.js (React + Vite)
├── nixpacks.toml     # Configuration build
├── Procfile          # Commande démarrage
└── railway.json     # Configuration Railway
```

### Commandes de Build
- **Backend:** `cd backend && uv sync --frozen`
- **Frontend:** `cd frontend && npm ci && npm run build`
- **Start:** `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 🎯 Avantages Railway vs Render

### ✅ Debugging Amélioré
- **Logs en temps réel** avec interface claire
- **Stack traces complètes** immédiatement visibles
- **Console intégrée** pour debugging direct
- **Métriques détaillées** (CPU, RAM, requêtes)

### ✅ Déploiement Simplifié
- **Auto-détection** des frameworks
- **Variables d'environnement** plus simples
- **Rollback en un clic**
- **Déploiements plus rapides**

### ✅ Monitoring Supérieur
- **Logs structurés** avec filtres
- **Alertes configurables**
- **Métriques de performance**
- **Health checks automatiques**

## 🚨 Points d'Attention

### Migration Base de Données
Si tu utilises une base Render :
1. **Exporter les données** depuis Render
2. **Créer nouvelle base** sur Railway
3. **Importer les données**

### URLs à Mettre à Jour
- **Frontend URL:** `https://your-app.railway.app`
- **Backend URL:** `https://your-api.railway.app`
- **Mettre à jour CORS** dans le backend

### Variables d'Environnement
- **Reconfigurer toutes** les variables
- **Tester les API keys**
- **Vérifier les connexions**

## 🎉 Résultat Attendu

Après migration :
- ✅ **Logs détaillés** pour identifier l'erreur filter()
- ✅ **Debugging plus rapide**
- ✅ **Interface plus intuitive**
- ✅ **Déploiements plus fiables**

## 📞 Support

En cas de problème :
- **Railway Docs:** https://docs.railway.app
- **Discord Railway:** Support communautaire
- **GitHub Issues:** Pour problèmes spécifiques

---
**Préparé le :** 19 septembre 2025
**Status :** ✅ PRÊT POUR MIGRATION