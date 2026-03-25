# Brief de Test Manuel — ArbitrageVault BookFinder
## PR #25 : Security Hardening, Cleanup, Picks Tuning, Config Save, Logout

---

## Contexte du Projet

ArbitrageVault BookFinder est une application web de sourcing de livres pour l'arbitrage Amazon.
- **Backend** : FastAPI + PostgreSQL (Neon), deploye sur Render
- **Frontend** : React + TypeScript + Vite + Tailwind, deploye sur Netlify

La PR #25 corrige 5 problemes en un seul batch. On doit valider que tout fonctionne avant merge.

---

## Ce qui a ete change (resume)

| # | Feature | Changement cle |
|---|---------|---------------|
| 1 | Security | SECRET_KEY crash en production si absent ; .env.autoscheduler retire de git |
| 2 | Cleanup | 50+ fichiers debug archives ; legacy config.py supprime, products.py migre vers get_settings() |
| 3 | Picks Tuning | MAX_PRODUCTS 10->25, roi_min 30->20, nouvel endpoint /last-job-stats |
| 4 | Config Save | Fix double toast erreur sur la page Configuration |
| 5 | Logout | Bouton "Se deconnecter" dans la navbar (desktop + mobile) |

---

## Tests a Executer

### Prerequis
- Acceder au frontend Netlify (URL du site deploye)
- Avoir un token Cowork pour les appels API backend (header Authorization: Bearer <token>)
- Acceder aux logs Render pour verifier les logs pipeline

---

### Test A — Backend : fetch-and-score retourne des picks

**Objectif** : Verifier que le pipeline autosourcing fonctionne avec roi_min=20.0

**Etapes** :
1. Ouvrir un terminal ou un outil HTTP (curl, Postman, navigateur avec extension REST)
2. Envoyer cette requete :
```
POST https://<backend-render-url>/api/v1/cowork/fetch-and-score
Headers:
  Authorization: Bearer <COWORK_API_TOKEN>
  Content-Type: application/json
Body: {}
```
3. Verifier la reponse :
   - `status` devrait etre `"success"`
   - `picks_count` devrait etre > 0 (grace au roi_min abaisse a 20)

**Resultat attendu** : Reponse 200 avec picks_count > 0

---

### Test B — Backend : last-job-stats endpoint

**Objectif** : Verifier que le nouvel endpoint retourne les stats du dernier job

**Etapes** :
1. Envoyer cette requete :
```
GET https://<backend-render-url>/api/v1/cowork/last-job-stats
Headers:
  Authorization: Bearer <COWORK_API_TOKEN>
```
2. Verifier la reponse contient :
   - `job_id` (string ou null si aucun job)
   - `status` (ex: "success")
   - `total_discovered`, `total_tested`, `total_selected` (entiers)
   - `created_at` (date ISO)

**Resultat attendu** : Reponse 200 avec les champs ci-dessus. Si le Test A a ete fait avant, les valeurs devraient etre non-zero.

---

### Test C — Backend : Logs pipeline

**Objectif** : Verifier que les 4 nouveaux log lines apparaissent apres un fetch-and-score

**Etapes** :
1. Aller sur le dashboard Render > Service backend > Logs
2. Chercher les lignes suivantes (apres avoir fait le Test A) :
   - `pipeline discover: X ASINs found`
   - `pipeline dedup: X ASINs after deduplication`
   - `pipeline score: X products scored`
   - `pipeline final: X picks selected (roi_min=20.0)`

**Resultat attendu** : Les 4 lignes sont presentes dans les logs

---

### Test D — Frontend : Page Configuration (pas de double toast)

**Objectif** : Verifier que sauvegarder la config affiche UN SEUL toast (pas de doublon)

**Etapes** :
1. Ouvrir le site frontend dans un navigateur
2. Se connecter si necessaire
3. Aller sur la page Configuration (menu Settings)
4. Cliquer "Modifier"
5. Changer une valeur (ex: buffer securite de 15 a 16)
6. Cliquer "Sauvegarder"
7. Observer les notifications toast

**Resultat attendu** :
- Succes : UN SEUL toast vert "Configuration mise a jour"
- PAS de toast vert double ni de toast rouge en plus

**Test erreur (optionnel)** :
1. En mode edition, mettre les poids ROI=0.8 et Velocite=0.8 (somme != 1.0)
2. Sauvegarder
3. Le toast rouge devrait afficher le message d'erreur SPECIFIQUE du backend (pas "Erreur lors de la sauvegarde" generique)

---

### Test E — Frontend : Bouton Logout (Desktop)

**Objectif** : Verifier que le bouton logout fonctionne sur desktop

**Etapes** :
1. Ouvrir le site frontend (largeur > 1024px)
2. En haut a droite, cliquer sur l'avatar (cercle avec initiales)
3. Un dropdown devrait apparaitre avec :
   - L'email de l'utilisateur connecte (texte gris)
   - Un bouton "Se deconnecter"
4. Cliquer "Se deconnecter"
5. L'utilisateur devrait etre redirige vers la page de login

**Resultat attendu** : Dropdown s'ouvre, email visible, clic logout redirige vers login

---

### Test F — Frontend : Bouton Logout (Mobile)

**Objectif** : Verifier que le dropdown fonctionne aussi en mobile

**Etapes** :
1. Ouvrir le site frontend
2. Reduire la fenetre a une largeur mobile (< 768px) OU utiliser les DevTools > mode responsive
3. Cliquer sur l'avatar en haut a droite
4. Le dropdown doit apparaitre correctement sans etre coupe
5. Cliquer "Se deconnecter" — doit rediriger vers login

**Resultat attendu** : Meme comportement que desktop, dropdown bien positionne

---

### Test G — Frontend : Fermeture dropdown sur navigation

**Objectif** : Verifier que le menu user se ferme quand on change de page

**Etapes** :
1. Cliquer sur l'avatar pour ouvrir le dropdown
2. Sans cliquer "Se deconnecter", cliquer sur un lien du menu lateral (ex: Dashboard)
3. Le dropdown doit se fermer automatiquement

**Resultat attendu** : Dropdown ferme apres changement de page

---

## Resume des Resultats Attendus

| Test | Endpoint / Page | Critere de succes |
|------|----------------|-------------------|
| A | POST /cowork/fetch-and-score | 200, picks_count > 0 |
| B | GET /cowork/last-job-stats | 200, champs presents |
| C | Logs Render | 4 lignes "pipeline ..." presentes |
| D | Page Configuration | 1 seul toast, message erreur specifique |
| E | Navbar desktop | Dropdown avec email + logout fonctionnel |
| F | Navbar mobile | Idem en responsive |
| G | Navigation | Dropdown se ferme au changement de page |

---

## Informations Techniques

- **Repo** : github.com/aziztraorebf-ctrl/arbitragevault-bookfinder
- **PR** : #25
- **Branche** : claude/setup-bookfinder-app-oAoGv
- **Backend URL Render** : (a remplir)
- **Frontend URL Netlify** : (a remplir)
- **COWORK_API_TOKEN** : (a fournir de maniere securisee, ne pas mettre ici)
