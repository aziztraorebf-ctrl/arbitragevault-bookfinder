# 🚂 Migration vers Railway - Guide Complet

## 📋 Préparation Effectuée

### ✅ Fichiers Supprimés (Render)
- `render.yaml` - Configuration Blueprint Render

### ✅ Fichiers Ajoutés (Railway)
- `railway.json` - Configuration Railway
- `nixpacks.toml` - Configuration build Nixpacks
- `Procfile` - Commande de démarrage
- `.gitignore` mis à jour

## 🚀 Étapes de Migration - CONFIGURATION CORRIGÉE

### 1. Créer un Compte Railway
- Va sur https://railway.app
- Connecte-toi avec GitHub
- Autoriser l'accès au repository

### 2. Créer DEUX Services Séparés (Monorepo Isolé)

#### Service Backend :
- Cliquer "New Project" → "Deploy from GitHub repo"
- Choisir `arbitragevault-bookfinder`
- Dans Settings → **Root Directory** : `backend`
- Railway détectera automatiquement UV via `uv.lock`

#### Service Frontend :
- Dans le même projet, cliquer "+" → "GitHub Repo"
- Choisir le même repo `arbitragevault-bookfinder`
- Dans Settings → **Root Directory** : `frontend`
- Railway détectera automatiquement React via `package.json`

### 3. Configuration Automatique
Railway détectera automatiquement :
- ✅ **Backend** : Python 3.12 + UV + FastAPI (via backend/pyproject.toml + uv.lock)
- ✅ **Frontend** : Node.js 20 + React + Vite (via frontend/package.json)
- ✅ **Monorepo Isolé** : Services séparés avec Root Directory

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

### Structure Détectée par Railway (Services Séparés)
```
/
├── backend/                    # SERVICE 1 - Root Directory: backend/
│   ├── pyproject.toml         # ✅ Détection Python + UV
│   ├── uv.lock               # ✅ UV package manager
│   ├── nixpacks.toml         # ✅ Configuration build backend
│   └── app/main.py           # ✅ FastAPI app
├── frontend/                  # SERVICE 2 - Root Directory: frontend/
│   ├── package.json          # ✅ Détection Node.js + React
│   ├── nixpacks.toml         # ✅ Configuration build frontend
│   └── src/                  # ✅ React app
├── Procfile                  # ✅ Fallback start command
└── railway.json             # ✅ Configuration Railway globale
```

### Commandes de Build (Automatiques)
- **Backend:** `uv sync --no-dev --frozen` (détecté via uv.lock)
- **Frontend:** `npm ci && npm run build` (détecté via package.json)
- **Start Backend:** `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Start Frontend:** `serve -s dist -l $PORT` (serveur statique pour React)

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