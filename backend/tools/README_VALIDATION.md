# Phase 1 Validation — ROI V1 vs V2

## Objectif

Valider localement que la Phase 1 (ROI direct avec prix Keepa + auto-sélection stratégie) fonctionne correctement avant de déployer en production.

---

## Prérequis

### 1. Backend Local Running
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Dépendances Python
```bash
pip install requests pandas
```

---

## Utilisation

### Commande de Base
```bash
cd backend/tools
python validate_roi_v1_vs_v2.py \
  --base-url http://localhost:8000 \
  --asins 0134685997,1259573545,0593655036,1982137274,B08N5WRWNW,B00FLIJJSA,B0DFMNSKAX,B07FNW9FGJ
```

### Paramètres

| Paramètre | Description | Défaut | Exemple |
|-----------|-------------|--------|---------|
| `--base-url` | URL backend API | `http://localhost:8000` | `http://localhost:8000` |
| `--asins` | ASINs à tester (séparés par virgule) | **Requis** | `0593655036,1982137274` |
| `--output-dir` | Répertoire outputs | `/tmp` | `./validation_results` |

---

## Jeu d'ASINs Recommandé

### 8 ASINs Couvrant Tous les Cas

```bash
--asins 0134685997,1259573545,0593655036,1982137274,B08N5WRWNW,B00FLIJJSA,B0DFMNSKAX,B07FNW9FGJ
```

| Type | ASIN | Stratégie Attendue | Raison |
|------|------|-------------------|--------|
| Textbook-1 | `0134685997` | textbook | Calculus (prix élevé, BSR modéré) |
| Textbook-2 | `1259573545` | textbook | Business textbook |
| Velocity-1 | `0593655036` | velocity | Bestseller fiction (rotation rapide) |
| Velocity-2 | `1982137274` | velocity | Popular non-fiction |
| Balanced-1 | `B08N5WRWNW` | balanced | Prix bas < $25 |
| Balanced-2 | `B00FLIJJSA` | balanced | Prix OK mais BSR > 250k |
| Edge-1 | `B0DFMNSKAX` | balanced | Prix défectueux (test fallback) |
| Edge-2 | `B07FNW9FGJ` | balanced | BSR manquant |

---

## Outputs

### 1. CSV Détaillé
**Fichier** : `/tmp/roi_validation.csv`

**Colonnes** :
- `asin` : Identifiant produit
- `profile_v2` : Stratégie auto-sélectionnée (textbook/velocity/balanced)
- `method_v2` : Méthode ROI (direct_keepa_prices/inverse_formula_fallback)
- `roi_v1_pct` : ROI calculé avec formule inverse (V1)
- `roi_v2_pct` : ROI calculé avec prix Keepa réels (V2)
- `delta_pct` : Écart relatif `|(V2-V1)/V1| * 100`
- `tolerance_status` : PASS (≤20%) / FAIL (>20%) / SKIP (erreur ou cas spécial)
- `reason` : Raison du statut
- `buy_cost_v2` : Coût achat FBA USED (V2)
- `sell_price_v2` : Prix vente BuyBox USED (V2)
- `error` : Message d'erreur si applicable

### 2. Markdown Summary
**Fichier** : `/tmp/roi_validation_summary.md`

**Sections** :
- **Statistiques globales** : % PASS/FAIL/SKIP, deltas moyens
- **Détail par ASIN** : Tableau complet avec statuts
- **Cas hors tolérance** : Détail des ASINs en FAIL avec causes probables
- **Recommandations** : Prêt pour Phase 2 (OUI/NON)

---

## Règles de Tolérance

### Critères de Succès
**Global** : ≥80% des ASINs testables en PASS

### Règles par Cas
1. **Si `roi_v1 ≈ 0` ET `roi_v2 < 5%`** → PASS (cohérence zéro)
2. **Si `roi_v1 ≈ 0` ET `roi_v2 > 5%`** → SKIP (amélioration attendue)
3. **Si `roi_v1 < 0` ET `roi_v2 > 0`** → PASS (fix bug ROI négatif)
4. **Sinon** : Delta relatif `|Δ%| ≤ 20%` → PASS, sinon FAIL

### ASINs Exclus du Calcul
- **SKIP** : Erreurs réseau, parsing, ou cas spéciaux

---

## Interprétation des Résultats

### ✅ Scénario Idéal (PASS ≥ 80%)
```markdown
📊 Summary:
   PASS: 7/8 (87.5%)
   Status: ✅ READY for Phase 2
```

**Action** : Continuer Phase 2 (Views Integration)

---

### ⚠️ Scénario Limite (PASS 60-80%)
```markdown
📊 Summary:
   PASS: 5/8 (62.5%)
   Status: ⚠️ INVESTIGATE failures
```

**Actions** :
1. Lire `/tmp/roi_validation_summary.md` section "Cas Hors Tolérance"
2. Vérifier si FAIL attendus (ex: textbook avec prix volatile Keepa)
3. Ajuster tolérance si V2 plus précis que V1 (comportement attendu)
4. Décision : GO Phase 2 avec monitoring renforcé

---

### ❌ Scénario Bloquant (PASS < 60%)
```markdown
📊 Summary:
   PASS: 3/8 (37.5%)
   Status: ⚠️ INVESTIGATE failures
```

**Actions** :
1. Investiguer bugs logique prix Keepa (`_determine_target_sell_price`, `_determine_buy_cost_used`)
2. Vérifier logs backend : `[VALIDATION]` entries
3. Tester ASINs FAIL individuellement avec Keepa API directe
4. NO-GO Phase 2 tant que < 60%

---

## Logs Backend

### Activer Logs Détaillés
Les logs `[VALIDATION]` s'affichent **uniquement** si header `X-Feature-Flags-Override` présent (script automatique).

**Exemple log attendu** :
```
[VALIDATION] ASIN=0593655036 | strategy=velocity | method=direct_keepa_prices | roi=28.3% | buy=$18.50 | sell=$28.00
```

### Logs Debug Supplémentaires
```
[DEV] Feature flags overridden: {'strategy_profiles_v2': True, 'direct_roi_calculation': True}
```

---

## Rollback / Nettoyage

### Aucune Modification Persistante
- ✅ Script modifie config **in-memory** via header HTTP
- ✅ Zéro modification fichier `business_rules.json`
- ✅ Pas de commit requis après tests

### Vérification Git
```bash
git status
# Expected: aucun fichier config modifié (seulement keepa.py + tools/)
```

---

## Troubleshooting

### Erreur : `Connection refused`
**Cause** : Backend pas démarré

**Fix** :
```bash
cd backend
uvicorn app.main:app --reload
```

---

### Erreur : `Missing dependencies`
**Cause** : Packages Python manquants

**Fix** :
```bash
pip install requests pandas
```

---

### Erreur : `Invalid feature flags override header`
**Cause** : Bug parsing JSON header (ne devrait pas arriver avec script)

**Fix** : Vérifier que `keepa.py` contient bien le bloc override (ligne ~415-425)

---

### ASIN Retourne SKIP
**Causes possibles** :
1. ASIN invalide ou non trouvé dans Keepa
2. Erreur réseau temporaire
3. Keepa API quota dépassé

**Fix** : Retester avec ASINs différents ou attendre quota Keepa

---

## Prochaines Étapes (Après Validation)

### Si ≥80% PASS
1. ✅ Continuer **Phase 2** : Views Integration
2. Implémenter VIEW_WEIGHTS matrix
3. Créer endpoint `/views/{view_type}`

### Si 60-80% PASS
1. ⚠️ Analyser cas FAIL
2. Décision : GO Phase 2 avec monitoring **OU** ajuster rules
3. Shadow mode 48h recommandé

### Si <60% PASS
1. ❌ NO-GO Phase 2
2. Debug logique prix Keepa
3. Re-valider après fix

---

## Contact / Support

**Questions** : Voir CLAUDE.md dans `.claude/` pour instructions générales

**Logs Production** : Render Dashboard → Logs

**Documentation Keepa** : https://github.com/keepacom/api_backend
