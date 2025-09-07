# GitHub Roadmap - ArbitrageVault BookFinder

## 🎯 STATUS ACTUEL (2025-09-05)

**✅ TERMINÉ - Niche Bookmarking Phase 2 Complete**
- Tag: `v1.6.1` - Keepa Integration Fully Validated - E2E Tests Passing
- Commit: `c145017` - README mis à jour avec fonctionnalité validée
- 11/11 tests unitaires + 6/6 tests intégration Keepa passants
- Backend production-ready avec workflow complet découverte → sauvegarde → relance
- API REST complète : 6 endpoints Niche Bookmarking opérationnels

**✅ PRÉCÉDEMMENT TERMINÉ - Architecture Refactor Major (2025-08-27)**
- Commit: `a405d4e` - Architecture refactor - Harmonisation modèles/services/API  
- 5/5 tests composants réussis
- Backend cohérent et services avec secrets management

## 📋 PHASE 3 EN COURS - FRONTEND NICHE MANAGEMENT UI

### **Phase 3A: Interface "Mes Niches" (Priorité 1)**
**Branch:** `feature/frontend-mes-niches`
**Description:** Interface utilisateur pour gestion des niches bookmarkées
**Status:** 🚧 À démarrer

**Frontend Requirements:**
- Page "Mes Niches" avec liste paginée des niches sauvegardées
- Boutons d'action par niche : Voir | Modifier | Supprimer | **Relancer l'analyse**
- Affichage : Nom, Score, Catégorie, Date création/modification
- Intégration avec NicheDiscoveryService pour relance d'analyse
- Design responsive avec Tailwind CSS

**Backend Ready:** ✅ 6 endpoints API disponibles
**Tests Ready:** ✅ 11/11 unitaires + 6/6 intégration validés

### **Phase 3B: Workflow Integration (Priorité 2)**  
**Description:** Intégration complète découverte ↔ sauvegarde dans UI existante
- Bouton "Sauvegarder cette niche" sur résultats de découverte
- Workflow utilisateur complet dans interface
- Navigation fluide entre découverte et gestion

## 📋 PROCHAINES FEATURES AVANCÉES (Phase 4)

### **Feature 4.1: Target Selling Price**
**Branch:** `feature/target-selling-price`  
**Description:** Calcul automatique du prix de vente cible basé sur ROI souhaité

**Technical Specs:**
```python
# Formule par vue stratégique:
# prix_cible = (buy_price + fba_fee) / ((1 - referral_fee) × (1 - roi_target))

Profit Hunter → 50% ROI target
Velocity → 25% ROI target  
Cashflow Hunter → 35% ROI target
Balanced Score → 40% ROI target
Volume Player → 20% ROI target
```

**Issues à créer:**
- [ ] `#1` Backend: Implement target price calculation service
- [ ] `#2` API: Add target_price field to analysis response
- [ ] `#3` Tests: Unit tests for price calculation logic
- [ ] `#4` Frontend: Display target price in analysis results

**Acceptance Criteria:**
- [ ] Service calcule prix cible selon vue stratégique sélectionnée
- [ ] API retourne target_price dans réponses analyses
- [ ] Tests couvrent tous les ROI targets par vue
- [ ] Frontend affiche prix cible avec explication

---

### **Feature 2: Amazon Retail Filter**
**Branch:** `feature/amazon-retail-filter`
**Description:** Filtrage des produits vendus directement par Amazon

**Technical Specs:**
```python
# AutoSourcing: Exclude `isAmazon = true` by default
# Manual search: Add `excludeAmazonRetail` boolean parameter
# Keepa API data format verification required
```

**Issues à créer:**
- [ ] `#5` Research: Verify Keepa API isAmazon field format
- [ ] `#6` Backend: Implement Amazon retail filtering logic
- [ ] `#7` API: Add excludeAmazonRetail parameter to endpoints
- [ ] `#8` Frontend: Add Amazon retail filter toggle
- [ ] `#9` AutoSourcing: Default exclude Amazon retail

**Acceptance Criteria:**
- [ ] Keepa API isAmazon field mapping confirmed
- [ ] Filtrage fonctionne en AutoSourcing par défaut
- [ ] Option manuelle disponible dans recherche
- [ ] Tests couvrent cas Amazon retail exclusion

## 🧪 TESTING PIPELINE

### **Tests End-to-End Créés**
- ✅ `tests/e2e/test_backend_corrections.py` - Validation corrections
- ✅ `tests/e2e/test_performance_load.py` - Tests charge et performance  
- ✅ `tests/e2e/test_security_integration.py` - Sécurité et secrets
- ✅ `run_full_validation.py` - Script coordinateur

### **Prochains Tests Requis**
- [ ] Tests d'intégration nouvelles features
- [ ] Performance tests avec target pricing
- [ ] Security tests avec filtrage Amazon

## 🚀 DEPLOYMENT & RELEASES

### **Version Actuelle: v1.9.1-alpha**
- Architecture refactor terminé
- Backend harmonisé et cohérent
- Services avec secrets management

### **Prochaine Release: v1.10.0**
**Target:** Fin août 2025
**Features:**
- Target Selling Price calculation
- Amazon Retail filtering  
- Enhanced strategic views
- Performance optimizations

### **Release v2.0.0 (Future)**
- Frontend React complet
- Authentification utilisateur
- Dashboard temps réel
- Export avancé (Google Sheets, Excel)

## 📝 COMMIT CONVENTIONS

**Types:**
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction bug
- `refactor:` Refactoring code sans changement fonctionnel
- `test:` Ajout/modification tests
- `docs:` Documentation
- `style:` Formatage code

**Format:**
```
type(scope): description courte

Détails si nécessaire

🤖 Generated with [Memex](https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
```

## 🔗 BRANCHES STRATEGY

**Main Branches:**
- `main` - Code stable et testé
- `develop` - Intégration features en cours

**Feature Branches:**
- `feature/target-selling-price` - Prix cible calculation
- `feature/amazon-retail-filter` - Filtrage Amazon retail
- `feature/frontend-react` - Frontend React (futur)

**Git Flow:**
1. Feature branch depuis `main`
2. Développement + tests dans feature branch
3. PR vers `main` avec review
4. Merge après validation tests CI/CD

---

**Créé:** 2025-08-27
**Dernière mise à jour:** 2025-08-27
**Responsable:** Architecture + Feature Development