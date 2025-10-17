# 🎨 Guide Test Utilisateur - Frontend ArbitrageVault

**Date** : 16 Octobre 2025
**Fix Déployé** : Prix & Timestamps Keepa
**Mode** : Test Local Frontend + Backend

---

## 🚀 Serveurs Actifs

### ✅ Backend Local
- **URL** : `http://localhost:8000`
- **Status** : 🟢 RUNNING
- **API Docs** : http://localhost:8000/docs

### ✅ Frontend Local
- **URL** : `http://localhost:5173`
- **Status** : 🟢 RUNNING
- **Config** : Pointe vers backend local

---

## 🎯 Objectif du Test

Vérifier que le fix des **prix** et **timestamps** fonctionne **depuis l'interface utilisateur**, comme un vrai utilisateur qui cherche des livres à arbitrer.

### Ce que tu vas tester :

1. ✅ **Prix réels affichés** (~$14-17 au lieu de $0.16)
2. ✅ **BSR cohérent** (< 100 pour bestsellers)
3. ✅ **ROI calculé correctement** (20-35% au lieu de 500%)
4. ✅ **Profit réaliste** (~$1-3 au lieu de $0.02)
5. ✅ **Pas de badges "Données obsolètes"**

---

## 📋 Test Étape par Étape

### Étape 1 : Ouvrir l'Application

1. Ouvre ton navigateur
2. Va sur : **http://localhost:5173**
3. Tu devrais voir l'interface ArbitrageVault

**✅ Ce que tu dois voir** :
- Page d'accueil avec formulaire de recherche
- Titre "ArbitrageVault" ou similaire
- Champ pour entrer des ASINs

---

### Étape 2 : Tester avec un ASIN Bestseller

**ASIN à tester** : `0593655036`
**Produit** : "The Anxious Generation" (Bestseller actuel)

**Actions** :
1. Dans le champ ASIN/ISBN, entre : `0593655036`
2. Sélectionne stratégie : **Balanced** (ou laisse par défaut)
3. Clique sur **"Analyser"** ou **"Search"**
4. Attends 5-15 secondes (temps de requête Keepa)

**✅ RÉSULTAT ATTENDU** :

Une **card produit** s'affiche avec :

```
╔═══════════════════════════════════════════════╗
║  The Anxious Generation                       ║
║  by Jonathan Haidt                            ║
║═══════════════════════════════════════════════║
║  💰 Prix Amazon: $16.98                       ║  ✅ PAS $0.16 !
║  📊 BSR: #69                                  ║  ✅ Bestseller
║  📈 ROI: 30%                                  ║  ✅ Réaliste
║  💵 Profit Net: $1.91                         ║  ✅ > $1.00
║  ⚡ Vélocité: FAST                            ║
║  🎯 Recommandation: STRONG BUY                ║
╚═══════════════════════════════════════════════╝
```

**❌ ÉCHEC SI TU VOIS** :
- Prix : $0.16 ou $0.11
- ROI : 500% ou plus
- Profit : $0.02
- Badge rouge "Données obsolètes"

---

### Étape 3 : Vérifier les Détails (ROI Accordion)

**Actions** :
1. Clique sur la section **"Détails ROI"** ou **"Breakdown"**
2. Expande l'accordion pour voir le calcul détaillé

**✅ CE QUE TU DOIS VOIR** :

```
ROI Breakdown
─────────────────────────────
Prix de vente:        $16.98  ✅
Prix d'achat cible:   $6.37   ✅
Frais Amazon:         $7.85   ✅
  - Referral Fee:     $2.55
  - FBA Fee:          $2.90
  - Closing Fee:      $1.80
  - Shipping:         $0.40
  - Prep:             $0.20

Profit Net:           $1.91   ✅
ROI:                  30.00%  ✅
Marge:                11.26%  ✅
```

**Validation** :
- `Prix de vente` doit être **> $10.00**
- `Frais Amazon` doivent être **< $10.00**
- `Profit Net` doit être **positif et > $1.00**

---

### Étape 4 : Tester avec Atomic Habits

**ASIN** : `0735211299`
**Produit** : "Atomic Habits" (Classic bestseller)

**Actions** :
1. Clear le champ ASIN
2. Entre : `0735211299`
3. Clique **"Analyser"**

**✅ RÉSULTAT ATTENDU** :

```
╔═══════════════════════════════════════════════╗
║  Atomic Habits                                ║
║  by James Clear                               ║
║═══════════════════════════════════════════════║
║  💰 Prix Amazon: $14.00                       ║  ✅ ~$11-15
║  📊 BSR: #250                                 ║  ✅ < 1000
║  📈 ROI: 35%                                  ║  ✅ Réaliste
║  💵 Profit Net: $2.15                         ║  ✅ > $1.00
║  ⚡ Vélocité: FAST                            ║
║  🎯 Recommandation: STRONG BUY                ║
╚═══════════════════════════════════════════════╝
```

---

### Étape 5 : Test Batch (Multiple ASINs)

**ASINs** : `0593655036, 0735211299`

**Actions** :
1. Dans le champ, entre les **2 ASINs séparés par une virgule** :
   ```
   0593655036, 0735211299
   ```
2. Clique **"Analyser"**
3. Attends 10-20 secondes

**✅ RÉSULTAT ATTENDU** :

Tu devrais voir **2 cards** s'afficher :

```
[Card 1: The Anxious Generation - $16.98 - ROI 30%]
[Card 2: Atomic Habits - $14.00 - ROI 35%]
```

**Validation** :
- Les 2 produits s'affichent
- Les 2 ont des prix > $10
- Les 2 montrent ROI réaliste (20-40%)

---

### Étape 6 : Vérifier Timestamp Data Freshness

**Actions** :
1. Sur une card produit, cherche l'indicateur de fraîcheur
2. Peut être dans un tooltip, badge ou section "Dernière mise à jour"

**✅ CE QUE TU DOIS VOIR** :
- **Date** : 15 ou 16 Octobre 2025 (ou "Aujourd'hui")
- **Badge vert** : "Données fraîches" ou "Up to date"

**❌ ÉCHEC SI TU VOIS** :
- Date : 25 Juillet 2015
- Badge rouge : "Données obsolètes"
- Warning : "Prix non à jour"

---

## 🎨 Éléments UI à Vérifier

### Prix Display
- [ ] Affiché avec symbole $ et 2 décimales ($16.98)
- [ ] Couleur verte ou neutre (pas rouge warning)
- [ ] Pas de tooltip d'erreur au survol

### ROI Badge
- [ ] Pourcentage affiché (ex: "30%")
- [ ] Couleur appropriée (vert si > 25%, orange si 15-25%)
- [ ] Pas de valeurs absurdes (> 100%)

### Recommendation Badge
- [ ] "STRONG BUY", "BUY", ou "PASS"
- [ ] Cohérent avec ROI (STRONG BUY si ROI > 25%)

### BSR Display
- [ ] Format numérique (#69, #250)
- [ ] Pas de valeurs décimales bizarres

---

## 🧪 Tests Avancés (Optionnel)

### Test 7 : Vérifier Console Browser (DevTools)

**Actions** :
1. Ouvre DevTools (F12)
2. Va dans l'onglet **Console**
3. Fais une nouvelle recherche ASIN

**✅ CE QUE TU NE DOIS PAS VOIR** :
- ❌ Erreurs réseau (500, 404)
- ❌ Warnings "Invalid price"
- ❌ Errors "Failed to parse"

**✅ CE QUI EST OK** :
- Logs informatifs (API call, parsing success)
- Warnings mineurs non-bloquants

---

### Test 8 : Vérifier Network Tab

**Actions** :
1. DevTools → Onglet **Network**
2. Fais une recherche ASIN
3. Cherche la requête `POST /api/v1/keepa/ingest`

**✅ VÉRIFICATIONS** :

**Request** :
```json
{
  "identifiers": ["0593655036"],
  "strategy": "balanced"
}
```

**Response (200 OK)** :
```json
{
  "successful": 1,
  "results": [{
    "current_price": 16.98,  // ✅ Prix réel
    "current_bsr": 69,        // ✅ BSR cohérent
    "roi": {
      "roi_percentage": "30.00"  // ✅ ROI réaliste
    }
  }]
}
```

---

## ✅ Checklist Validation Finale

Coche chaque élément après validation :

### Affichage Prix
- [ ] Prix Amazon affiché > $10 pour bestsellers
- [ ] Prix formaté correctement ($16.98, pas 16.980000)
- [ ] Cohérent avec prix Amazon réel (vérifiable sur Amazon.com)

### Calculs ROI
- [ ] ROI entre 5% et 50% (pas 500%)
- [ ] Profit net positif et > $1.00
- [ ] Frais Amazon réalistes (~$7-8 pour livres)

### BSR & Metrics
- [ ] BSR < 1000 pour bestsellers connus
- [ ] Vélocité affichée (Fast/Medium/Slow)
- [ ] Rating cohérent si affiché

### UI/UX
- [ ] Pas de badges "Données obsolètes"
- [ ] Recommandation cohérente (STRONG BUY pour ROI > 25%)
- [ ] Loading states pendant requêtes
- [ ] Pas d'erreurs console bloquantes

### Fonctionnalités
- [ ] Recherche single ASIN fonctionne
- [ ] Recherche multiple ASINs (batch) fonctionne
- [ ] Backend répond en < 30s
- [ ] Frontend affiche résultats sans crash

---

## 📸 Screenshots à Partager (Optionnel)

Si tu veux documenter les résultats :

1. **Screenshot 1** : Card produit "The Anxious Generation" montrant prix $16.98
2. **Screenshot 2** : ROI Breakdown détaillé
3. **Screenshot 3** : Batch de 2 ASINs affichés
4. **Screenshot 4** : Network tab montrant response JSON

---

## 🐛 Si ça ne marche pas

### Problème : Prix toujours $0.16

**Solutions** :
1. Vérifie que `.env.local` pointe vers `http://localhost:8000`
2. Hard refresh navigateur (Ctrl+Shift+R)
3. Clear cache navigateur
4. Vérifie backend logs

### Problème : "Network Error"

**Solutions** :
1. Vérifie que backend tourne : `curl http://localhost:8000/health`
2. Vérifie CORS configuré pour `localhost:5173`
3. Regarde console backend pour erreurs

### Problème : Lenteur > 30s

**Cause** : Keepa API timeout (normal première requête)

**Solutions** :
- Attends jusqu'à 60s première fois
- Retry avec même ASIN (sera en cache)

---

## 🎯 Résultat Final Attendu

Après tous les tests, tu devrais pouvoir dire :

✅ **"Je vois des prix réels ($14-17) au lieu de $0.16"**
✅ **"Les ROI affichés sont réalistes (20-35%)"**
✅ **"Les profits nets sont > $1.00"**
✅ **"Aucun badge 'Données obsolètes' affiché"**
✅ **"L'application fonctionne comme prévu"**

---

## 📞 Feedback à Partager

Après tes tests, partage-moi :

1. **ASINs testés** (liste)
2. **Prix affichés** pour chaque ASIN
3. **ROI affichés** pour chaque ASIN
4. **Problèmes rencontrés** (si aucun, dis "Tout fonctionne!")
5. **Screenshots** (optionnel mais utile)

---

## 🔄 Pour Revenir en Mode Production

Quand tu auras fini les tests locaux :

1. Restaure `.env.local` :
   ```bash
   cp frontend/.env.local.backup frontend/.env.local
   ```

2. Ou édite manuellement pour pointer vers :
   ```
   VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
   ```

---

**Prêt pour tester ?** Ouvre **http://localhost:5173** et commence ! 🚀
