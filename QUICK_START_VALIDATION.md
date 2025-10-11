# 🚀 Quick Start - Phase 1 Validation

## Étapes Simples (5 minutes)

### 1️⃣ Démarrer Backend (Terminal 1)

**Ouvrir nouveau terminal** et exécuter :

```bash
cd C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend
START_BACKEND.bat
```

**Attendre** ce message :
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Backend prêt** quand tu vois "Application startup complete"

---

### 2️⃣ Lancer Validation (Terminal 2)

**Ouvrir NOUVEAU terminal** (laisser Terminal 1 tourner) et exécuter :

```bash
cd C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend\tools
RUN_VALIDATION.bat
```

**Tu verras** :
```
[1/3] Checking backend availability...
      Backend OK (http://localhost:8000)
[2/3] Checking Python dependencies...
      Dependencies OK
[3/3] Running validation with 8 ASINs...
      This will take ~2-3 minutes...

🚀 Starting validation for 8 ASINs...
   [1/8] Testing 0134685997... PASS
   [2/8] Testing 1259573545... PASS
   [3/8] Testing 0593655036... PASS
   ...
```

---

### 3️⃣ Lire Résultats

**Fichiers générés** :
```
C:\tmp\roi_validation.csv           (données détaillées)
C:\tmp\roi_validation_summary.md    (rapport lisible)
```

**Ouvrir avec** :
- CSV : Excel ou VSCode
- Markdown : VSCode (prévisualisation avec CTRL+SHIFT+V)

---

## ✅ Critères de Succès

**Dans le terminal, chercher** :
```
📊 Summary:
   PASS: X/8 (XX%)
   Status: ✅ READY for Phase 2
```

**Scénarios** :
- **PASS ≥ 6/8 (75%)** → ✅ **GO Phase 2**
- **PASS 4-5/8 (50-62%)** → ⚠️ Analyser cas FAIL
- **PASS < 4/8 (<50%)** → ❌ Investiguer bugs

---

## 🔧 Troubleshooting

### Erreur : "Backend is not running"
**Solution** : Retourne Terminal 1, vérifie que backend a bien démarré

---

### Erreur : "uvicorn: command not found"
**Solution** :
```bash
cd backend
pip install -r requirements.txt
```

---

### Erreur : "Missing dependencies"
**Solution** :
```bash
pip install requests pandas
```

---

### Erreur : "KEEPA_API_KEY not found"
**Solution** : Vérifier fichier `.env` dans `backend/` contient :
```
KEEPA_API_KEY=your_key_here
```

---

## 📊 Interpréter les Résultats

### Exemple Résultat Idéal (Summary MD)

```markdown
## 📊 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| ASINs PASS | 7/8 (87.5%) |
| ASINs FAIL | 1/8 (12.5%) |
| ASINs SKIP | 0/8 (0%) |
| Delta moyen (PASS) | 8.3% |
| Delta max (PASS) | 18.7% |

**Statut Global** : ✅ PASS
```

**Action** → Continuer Phase 2

---

### Exemple Résultat Limite

```markdown
| ASINs PASS | 5/8 (62.5%) |
| ASINs FAIL | 2/8 (25%) |
```

**Action** → Lire section "⚠️ Cas Hors Tolérance" pour comprendre pourquoi

---

## 🎯 Après Validation

**Revenir sur Claude Code** et partager :
- ✅ Statut global (PASS X/8)
- ✅ Contenu `/tmp/roi_validation_summary.md` (copier-coller section Statistiques)
- ✅ Questions sur cas FAIL si applicable

**Claude continuera** avec Phase 2 ou debugging selon résultats.

---

## 📁 Fichiers Créés

```
backend/
├── START_BACKEND.bat                    ← Démarrage backend simplifié
└── tools/
    ├── RUN_VALIDATION.bat               ← Validation automatique
    ├── validate_roi_v1_vs_v2.py         ← Script Python (déjà créé)
    └── README_VALIDATION.md             ← Documentation complète
```

---

**Prêt à lancer ?** Suis les étapes 1️⃣ → 2️⃣ → 3️⃣ ci-dessus ! 🚀
