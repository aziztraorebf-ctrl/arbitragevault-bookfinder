# Audit Backend API - Phase 1 Jour 1

**Date**: 2025-10-24T09:15:53.737369
**URL**: https://arbitragevault-backend-v2.onrender.com

## 📊 Résumé
- **Total endpoints**: 29
- **✅ Success**: 17
- **⚠️ Warning**: 5
- **❌ Error**: 7

## Health

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /health` | ✅ | 200 | 1.928s | Endpoint santé basique |
| `GET /api/v1/health/ready` | ✅ | 200 | 2.585s | Readiness check avec DB |
| `GET /api/v1/health/live` | ✅ | 200 | 1.874s | Liveness check |
| `GET /api/v1/keepa/health` | ✅ | 200 | 2.707s | Health check Keepa service |
| `GET /api/v1/autosourcing/health` | ✅ | 200 | 2.519s | Health check AutoSourcing |

## Keepa

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/keepa/0593655036/metrics` | ✅ | 200 | 3.296s | Metrics pour ASIN facile (0593655036) |
| `GET /api/v1/keepa/0593655036/raw` | ❌ | 500 | 3.809s | Raw data pour ASIN facile |
| `GET /api/v1/keepa/B08N5WRWNW/metrics` | ✅ | 200 | 2.499s | Metrics pour ASIN moyen (B08N5WRWNW) |
| `GET /api/v1/keepa/B08N5WRWNW/raw` | ✅ | 200 | 5.179s | Raw data pour ASIN moyen |
| `GET /api/v1/keepa/B00FLIJJSA/metrics` | ✅ | 200 | 4.084s | Metrics pour ASIN difficile (B00FLIJJSA) |
| `GET /api/v1/keepa/B00FLIJJSA/raw` | ❌ | 500 | 4.876s | Raw data pour ASIN difficile |
| `GET /api/v1/keepa/INVALID123/metrics` | ⚠️ | 404 | 3.642s | Test ASIN invalide |
| `GET /api/v1/keepa/test` | ✅ | 200 | 3.925s | Test connexion Keepa API |

## Analyses

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/analyses` | ✅ | 200 | 2.608s | Liste analyses paginées |
| `GET /api/v1/analyses/top` | ✅ | 200 | 2.763s | Top analyses d'un batch |

## Batches

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/batches` | ✅ | 200 | 2.882s | Liste batches |

## Config

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/config/` | ✅ | 200 | 2.75s | Config effective books US |
| `GET /api/v1/config/changes` | ✅ | 200 | 2.312s | Historique changements config |
| `GET /api/v1/config/stats` | ✅ | 200 | 1.97s | Statistiques config service |

## Views

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/views` | ✅ | 200 | 2.945s | Liste des vues disponibles |
| `POST /api/v1/views/mes_niches` | ⚠️ | 403 | 1.884s | Scoring view Mes Niches |

## AutoSourcing

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/autosourcing/latest` | ❌ | 500 | 2.608s | Derniers résultats AutoSourcing |
| `GET /api/v1/autosourcing/jobs` | ❌ | 500 | 2.657s | Jobs AutoSourcing récents |
| `GET /api/v1/autosourcing/profiles` | ❌ | 500 | 2.56s | Profils AutoSourcing sauvegardés |

## Products

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/v1/products/0593655036/stock-estimate` | ❌ | 500 | 2.539s | Estimation stock produit |

## Auth

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `POST /api/v1/auth/register` | ❌ | 501 | 1.981s | Register endpoint (placeholder) |
| `GET /api/v1/auth/me` | ⚠️ | 401 | 2.049s | Current user (auth required) |

## Niche

| Endpoint | Status | Code | Time | Notes |
|----------|--------|------|------|-------|
| `GET /api/niche-discovery/categories` | ⚠️ | 401 | 2.046s | Categories disponibles pour niches |
| `GET /api/niche-discovery/stats` | ⚠️ | 401 | 1.793s | Stats service Niche Discovery |

## 🔍 Problèmes Identifiés

### ❌ Erreurs Critiques

**`GET /api/v1/keepa/0593655036/raw`**
- Error: None

**`GET /api/v1/keepa/B00FLIJJSA/raw`**
- Error: None

**`GET /api/v1/autosourcing/latest`**
- Error: None

**`GET /api/v1/autosourcing/jobs`**
- Error: None

**`GET /api/v1/autosourcing/profiles`**
- Error: None

**`GET /api/v1/products/0593655036/stock-estimate`**
- Error: None

**`POST /api/v1/auth/register`**
- Error: None

### ⚠️ Warnings

**`GET /api/v1/keepa/INVALID123/metrics`**
- Status Code: 404
- Response: Not Found

**`POST /api/v1/views/mes_niches`**
- Status Code: 403
- Response: {"detail":"View-specific scoring not enabled. Set 'view_specific_scoring: true' in config."}

**`GET /api/v1/auth/me`**
- Status Code: 401
- Response: {"detail":"Not authenticated"}

**`GET /api/niche-discovery/categories`**
- Status Code: 401
- Response: {"detail":"Not authenticated"}

**`GET /api/niche-discovery/stats`**
- Status Code: 401
- Response: {"detail":"Not authenticated"}

## 💡 Recommandations

1. **Endpoints Critiques à Fixer**:
   - GET /api/v1/keepa/0593655036/raw
   - GET /api/v1/keepa/B00FLIJJSA/raw
   - GET /api/v1/autosourcing/latest
   - GET /api/v1/autosourcing/jobs
   - GET /api/v1/autosourcing/profiles
   - GET /api/v1/products/0593655036/stock-estimate
   - POST /api/v1/auth/register

2. **Endpoints à Surveiller**:
   - GET /api/v1/keepa/INVALID123/metrics
   - POST /api/v1/views/mes_niches
   - GET /api/v1/auth/me
   - GET /api/niche-discovery/categories
   - GET /api/niche-discovery/stats