# Phase 8 - Business Thresholds Documentation

Ce document explique les seuils utilises dans les services Phase 8 Advanced Analytics.

## 1. Dead Inventory Thresholds (BSR)

| Categorie | Seuil BSR | Justification |
|-----------|-----------|---------------|
| books | 50,000 | Livres au-dela de ce BSR peuvent prendre > 30 jours a vendre |
| textbooks | 30,000 | Textbooks ont un marche plus restreint, seuil plus strict |
| general | 100,000 | Seuil par defaut pour categories non specifiees |

**Source:** Experience empirique du marche Amazon FBA Books. A valider avec donnees historiques de ventes reelles.

**Fichier:** `backend/app/services/advanced_analytics_service.py:18-22`

```python
CATEGORY_DEAD_INVENTORY_THRESHOLDS = {
    'books': 50000,
    'textbooks': 30000,
    'general': 100000,
}
```

---

## 2. Recommendation Thresholds

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| MIN_ROI_THRESHOLD | 30% | ROI minimum pour couvrir les imprevus et garantir profit |
| GOOD_VELOCITY_THRESHOLD | 70 | Score velocity indiquant ventes rapides (< 2 semaines) |
| ACCEPTABLE_RISK_THRESHOLD | 50 | Score risque au-dela duquel prudence necessaire |
| MAX_SALE_CYCLE_DAYS | 45 | Delai max acceptable avant frais stockage long terme |

**Source:** Standards industrie FBA arbitrage. MIN_ROI 30% est un consensus communaute resellers.

**Fichier:** `backend/app/services/recommendation_engine_service.py:22-25`

```python
MIN_ROI_THRESHOLD = 30
GOOD_VELOCITY_THRESHOLD = 70
ACCEPTABLE_RISK_THRESHOLD = 50
MAX_SALE_CYCLE_DAYS = 45
```

---

## 3. Risk Scoring Weights

| Composant | Poids | Justification |
|-----------|-------|---------------|
| dead_inventory | 35% | Risque principal: produit qui ne se vend pas |
| competition | 25% | Beaucoup de vendeurs = guerre des prix |
| amazon_presence | 20% | Amazon sur listing = tres difficile de gagner BuyBox |
| price_stability | 10% | Prix volatils = marges imprevisibles |
| category | 10% | Certaines categories plus risquees |

**Source:** Ponderation basee sur impact relatif sur profitabilite. Dead inventory est le risque #1 car un produit invendu = perte totale.

**Fichier:** `backend/app/services/risk_scoring_service.py:14-20`

```python
RISK_WEIGHTS = {
    'dead_inventory': 0.35,
    'competition': 0.25,
    'amazon_presence': 0.20,
    'price_stability': 0.10,
    'category': 0.10
}
```

---

## 4. Amazon Risk Values

| Scenario | Score | Justification |
|----------|-------|---------------|
| Amazon present | 95 | Quasi-impossible de concurrencer Amazon sur ses listings |
| Amazon absent | 5 | Risque residuel (Amazon peut revenir a tout moment) |

**Fichier:** `backend/app/services/risk_scoring_service.py:162-164`

---

## 5. Category Risk Factors

| Categorie | Score Risque | Justification |
|-----------|--------------|---------------|
| technical | 30 | Livres techniques: audience stable, moins de mode |
| fiction | 35 | Fiction: relativement stable mais sensible aux tendances |
| nonfiction | 40 | Non-fiction: variable selon sujet |
| textbooks | 45 | Textbooks: risque editions, cycles scolaires |
| general | 50 | Defaut pour categories inconnues |

**Fichier:** `backend/app/services/risk_scoring_service.py:22-28`

---

## 6. Competition Risk Scale

| Nombre Vendeurs | Score Risque | Interpretation |
|-----------------|--------------|----------------|
| 0-2 | 10 | Faible competition, opportunite |
| 3-5 | 25 | Competition moderee |
| 6-15 | 45 | Competition elevee |
| 16-30 | 65 | Competition intense |
| 31+ | 80+ | Guerre des prix probable |

**Fichier:** `backend/app/services/risk_scoring_service.py:145-159`

---

## 7. Velocity Score Interpretation

| Score | Interpretation | BSR Approximatif |
|-------|----------------|------------------|
| 80-100 | Excellent (vente en jours) | < 10,000 |
| 60-79 | Bon (vente en 1-2 semaines) | 10,000-30,000 |
| 40-59 | Moyen (vente en 2-4 semaines) | 30,000-75,000 |
| 20-39 | Faible (vente en 1-2 mois) | 75,000-150,000 |
| 0-19 | Tres faible (vente incertaine) | > 150,000 |

---

## 8. Recommendation Tiers

| Tier | Criteres Passes | Action Suggeree |
|------|-----------------|-----------------|
| STRONG_BUY | 6/6 | Acheter immediatement |
| BUY | 5/6 | Acheter a ce prix ou mieux |
| CONSIDER | 4/6 | Recherche supplementaire |
| WATCH | 3/6 | Surveiller, attendre baisse prix |
| SKIP | 0-2/6 | Chercher alternatives |
| AVOID | Override | Ne jamais acheter (ex: Amazon BuyBox) |

**Les 6 criteres:**
1. ROI >= 30%
2. Velocity >= 70
3. Risk < 50
4. Breakeven <= 45 jours
5. Amazon absent
6. Price stable (>= 50)

---

## 9. Special Override Rules

Ces regles FORCENT une recommendation quel que soit les autres indicateurs:

| Condition | Recommendation Forcee | Raison |
|-----------|----------------------|--------|
| Amazon a le BuyBox | AVOID | Impossible de gagner le BuyBox |
| ROI < 15% | SKIP | Marge insuffisante |
| Risk > 85 | SKIP | Risque trop eleve |

**Fichier:** `backend/app/services/recommendation_engine_service.py:203-232`

---

## 10. Recommendations pour validation future

1. **Collecter donnees reelles**: Tracker les ventes reelles vs predictions pour valider les seuils
2. **A/B testing**: Tester differents seuils sur un sous-ensemble de recommandations
3. **Feedback utilisateur**: Permettre aux utilisateurs de reporter si une recommandation etait correcte
4. **Revue trimestrielle**: Revoir les seuils tous les 3 mois avec nouvelles donnees

---

## Historique des modifications

| Date | Modification | Auteur |
|------|--------------|--------|
| 2025-12-25 | Documentation initiale des seuils Phase 8 | Claude Code Senior Review |
