# ArbitrageVault - Error Registry


---

## DB — Base de données / asyncpg

**DB-01** — can't subtract offset-naive and offset-aware datetimes
- **Cause** : autosourcing_jobs.created_at est TIMESTAMP WITHOUT TIMEZONE en DB, asyncpg rejette les comparaisons avec des datetimes aware
- **Fix** : Utiliser datetime.utcnow() (naive) et NON datetime.now(timezone.utc) (aware)
- **Colonnes affectées** : autosourcing_jobs.created_at (naive) vs asin_history.tracked_at (aware — OK avec aware)
- **Détecté** : Fév 2026

---

## GIT — Git / Hooks

**GIT-01** — Hook pre-commit consomme le flag checkpoint-approved avant que git s'exécute
- **Cause** : Si git add + git commit sont dans UNE seule commande Bash, le hook mange le flag sur git add
- **Fix** : Créer le flag dans un appel Bash séparé, puis git add && git commit dans l'appel suivant
- **Détecté** : Fév 2026

**GIT-02** — Scripts shell cassés après migration Windows vers macOS
- **Cause** : CRLF (Windows \r\n) dans les scripts bash — les heredoc EOF markers échouent
- **Fix** : Utiliser echo statements plutôt que heredoc, ou convertir avec dos2unix
- **Détecté** : Jan 2026

**GIT-03** — grep -oP (PCRE) non disponible sur macOS
- **Cause** : macOS utilise BSD grep, pas GNU grep — -P (Perl regex) n'existe pas
- **Fix** : Utiliser sed à la place
- **Détecté** : Jan 2026

---

## BACKEND — FastAPI / SQLAlchemy

**BE-01** — Deux Base classes SQLAlchemy dans le même projet
- **Cause** : app.core.db.Base (bare) pour autosourcing vs app.models.base.Base (avec id/created_at/updated_at) pour analytics
- **Fix** : Les modèles sur des Bases différentes coexistent mais ne partagent pas de metadata. JOINs entre modèles de même Base OK.
- **Détecté** : Fév 2026

**BE-02** — Endpoint URL mismatch frontend/backend (underscore vs hyphen)
- **Cause** : Frontend appelait /run_custom (underscore), backend attendait /run-custom (hyphen) — HTTP 404
- **Fix** : Convention : TOUJOURS des hyphens dans les routes FastAPI. Vérifier les deux côtés avant deploy.
- **Fichier** : frontend/src/pages/AutoSourcing.tsx
- **Détecté** : Fév 2026

---

## CONFIG — Configuration

**CFG-01** — Backend URL Render incorrect
- **Cause** : URL sans -v2 utilisée par erreur
- **Fix** : URL correcte = https://arbitragevault-backend-v2.onrender.com (avec -v2)
- **Détecté** : Fév 2026

**CFG-02** — Mismatch catégories Keepa : Books=3 (frontend) vs Books=283155 (backend)
- **Cause** : Frontend productDiscoveryService.ts utilise ID 3, backend keepa_categories.py utilise 283155
- **Fix** : Source de vérité = backend/app/config/keepa_categories.py. Frontend doit envoyer le nom, pas l'ID.
- **Fichier** : frontend/src/services/productDiscoveryService.ts
- **Détecté** : Fév 2026

---

## BE — Keepa Integration

**BE-03** — Indices Keepa CSV decales pour RATING et COUNT_REVIEWS
- **Cause** : Code utilisait RATING=15 et COUNT_REVIEWS=16, mais l'API officielle Keepa (Product.java) definit EXTRA_INFO_UPDATES=15, RATING=16, COUNT_REVIEWS=17
- **Fix** : Corrige keepa_constants.py (ajout EXTRA_INFO_UPDATES=15, RATING=16, COUNT_REVIEWS=17) et keepa_parser_v2.py (_extract_rating lit array[16])
- **Fichiers** : keepa_constants.py, keepa_parser_v2.py
- **Detecte** : Mars 2026

**BE-04** — dispatch_webhook utilise session DB potentiellement expiree
- **Cause** : asyncio.create_task(dispatch_webhook(db=self.db)) - la session du caller peut etre fermee quand le task s'execute
- **Fix** : dispatch_webhook cree sa propre session via db_manager.session()
- **Fichiers** : webhook_service.py, autosourcing_service.py
- **Detecte** : Mars 2026

---

## Ajouter un nouveau bug

Pour ajouter une entrée :
1. Choisir le domaine selon le tableau ci-dessous

| Code | Domaine |
|------|---------|
| DB | Base de données / asyncpg / PostgreSQL |
| GIT | Git / Hooks / CI |
| BE | Backend FastAPI / SQLAlchemy |
| FE | Frontend React / TypeScript |
| CFG | Configuration / Env / URLs |
| TEST | Tests pytest / Playwright |
| PERF | Performance / Optimisation |
2. Incrémenter le numéro (ex: BE-03)
3. Remplir : Cause | Fix | Fichiers concernés | Date détection
