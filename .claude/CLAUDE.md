# Custom Instructions Claude Code - Aziz

## Comportement General

### Style Communication
- **Langue** : Francais par defaut (sauf code/technical docs)
- **Ton** : Concis et direct, pas de preambule inutile
- **Validation** : Toujours confirmer avant modifications critiques (DB, deploiements)

### Workflow Developpement
- **Context7-First** : TOUJOURS verifier documentation officielle via Context7 AVANT d'ecrire du code API/integration. Ne JAMAIS assumer que la doc locale est a jour.
- **BUILD-TEST-VALIDATE** : Cycle continu avec vraies donnees
- **UX-First** : Prototyper UI -> Valider flux -> API contracts -> Backend -> Frontend
- **Git commits frequents** : Eviter drift code local/deploye

---

## Cles API

### Variables Environnement
- `KEEPA_API_KEY` : API Keepa pour analyses produits
- `GITHUB_TOKEN` : GitHub operations
- `RENDER_API_KEY` : Render deployments/logs
- `NETLIFY_TOKEN` : Netlify sites
- `DATABASE_URL` : PostgreSQL Neon

### Regles Securite
- JAMAIS exposer cles dans code/commits/logs
- Utiliser `.claude/settings.local.json` pour tests locaux
- Proteger `.env` files

---

## Code Style

### NO EMOJIS IN CODE (NON-NEGOTIABLE)
- FORBIDDEN: `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.yaml`, `.sql`, `.env`
- ALLOWED: `.md`, `.txt` only
- See `.claude/CODE_STYLE_RULES.md` for details

---

## Zero-Tolerance Engineering

### Superpowers Obligatoires
Invoquer ces skills SYSTEMATIQUEMENT :

| Situation | Skill |
|-----------|-------|
| Bug/Erreur | `superpowers:systematic-debugging` |
| Avant "c'est fait" | `superpowers:verification-before-completion` |
| Nouvelle feature | `superpowers:test-driven-development` |
| Probleme profond | `superpowers:root-cause-tracing` |
| Donnees externes | `superpowers:defense-in-depth` |
| Code review | `superpowers:requesting-code-review` |

### Gate System
AUCUN merge/completion sans :
- [ ] Tests passent (unit + integration + e2e)
- [ ] `verification-before-completion` execute avec PREUVE
- [ ] Assertions: donnees recues = donnees attendues
- [ ] Config externe validee au boot si applicable

### Validation Croisee MCP (ArbitrageVault)
Pour toute feature Keepa, COMPARER :
1. MCP Keepa direct (`mcp__keepa__get_product`) = source verite
2. Backend API (`/api/v1/keepa/{asin}/metrics`) = notre code
3. Si divergence prix/BSR > 1% : BLOQUER et investiguer
4. Les 2 doivent correspondre avant validation

### Modes de Test Keepa
| Mode | Usage | Source | Tokens |
|------|-------|--------|--------|
| REAL | Validation finale | API Keepa | Oui |
| REPLAY | Tests CI/rapides | JSON pre-enregistres | Non |
| MOCK | Unit tests | Valeurs fixes | Non |

Regle : REPLAY par defaut, REAL uniquement pour validation finale.

### Contrat Donnees Externes
```python
# OBLIGATOIRE pour tout ID/config externe (Keepa, APIs tierces)
# 1. Valider au demarrage
assert api.validate(external_id), f"{external_id} invalide!"

# 2. Assertions sur reponses
assert response.category == expected_category
assert bsr_min <= product.bsr <= bsr_max

# 3. Config centralisee avec metadata
EXTERNAL_CONFIG = {
    "category_x": {
        "id": 12345,
        "expected_name": "Category X",
        "validated_date": "2025-12-07",
    }
}
```

### Definition of Done
Une feature n'est JAMAIS "done" sans :
1. Tests passent avec vraies donnees
2. Preuve de validation (logs, screenshots, output)
3. Assertions en place dans le code
4. Donnees factuelles exactes (ASIN, prix, BSR, dates)
   - Approximatif OK pour scoring/predictions avec tolerance documentee

### Hostile Code Review (Pre-Commit)
**AVANT chaque commit/push**, Claude doit jouer le role d'attaquant :

1. **Posture** : Chercher activement les bugs, pas valider que ca marche
2. **Questions systematiques** :
   - Quels edge cases peuvent casser ce code?
   - Quelles donnees invalides peuvent arriver?
   - Quels etats impossibles sont possibles?
   - Quelle race condition peut survenir?
   - Quel null/undefined va exploser?
3. **Checklist pre-commit** :
   - [ ] Types stricts (pas de `any`, pas de `as unknown`)
   - [ ] Error handling complet (try/catch, .catch())
   - [ ] Validation inputs (Zod/Pydantic)
   - [ ] Tests couvrent cas negatifs
   - [ ] Pas de secrets hardcodes
4. **Bloquer si** : Doute sur un cas non teste

---

## Automated Quality Gates

### Pre-Commit Hooks (Recommande)
```bash
# .husky/pre-commit (frontend)
npm run lint && npm run type-check && npm run test:unit

# pre-commit (backend)
pytest tests/unit -x --tb=short
ruff check .
mypy app/
```

### CI/CD Pipeline
- **Build** : Doit passer avant merge
- **Tests** : Unit + Integration + E2E
- **Lint** : Zero warning accepte
- **Type-check** : Strict mode

### Niveaux de Tests
| Niveau | Tests | Duree | Quand |
|--------|-------|-------|-------|
| Smoke | 5 critiques | < 1 min | Chaque commit |
| Integration | 30-50 | < 5 min | Avant merge |
| Full E2E | Tous | 10+ min | Avant deploy |

---

## Observabilite

### Logs Production
- Consulter logs Render/Netlify AVANT debug local
- Format structure : `{timestamp, level, message, context}`
- Correlation IDs pour tracer requetes

### Monitoring
- Alertes sur erreurs 5xx
- Metriques : latence, taux erreur, tokens Keepa
- Dashboard : Render metrics, Netlify analytics

### Debug Workflow
1. Logs production (source verite)
2. Reproduire localement
3. Fix + test
4. Deployer + verifier logs

---

## Rollback Strategy

### Quand Rollback
- Erreurs 5xx > 1% des requetes
- Feature critique cassee
- Donnees corrompues

### Comment Rollback
```bash
# Git revert (prefere)
git revert HEAD --no-edit
git push

# Render : Redeploy previous commit
# Via Dashboard > Deploys > Redeploy

# Netlify : Instant rollback
# Via Dashboard > Deploys > Publish deploy
```

### Post-Rollback
1. Investiguer root cause
2. Fix dans branche separee
3. Tests exhaustifs
4. Re-deployer

---

## Code Review Workflow

### Quand Demander Review
- Avant merge de feature
- Apres fix de bug critique
- Changements DB/API/Auth

### Process
1. `superpowers:requesting-code-review` pour review structuree
2. Verifier : tests, types, edge cases, securite
3. Approval explicite avant merge

### Self-Review Checklist
- [ ] Je comprends chaque ligne
- [ ] Tests couvrent le comportement
- [ ] Pas de code commente/dead code
- [ ] Noms de variables clairs
- [ ] Pas de duplication

---

## CHECKPOINT OBLIGATOIRE (BLOQUANT)

### AVANT de dire "c'est fait" ou "termine"

**STOP. Repondre a CHAQUE question AVEC PREUVE :**

| # | Question | Reponse Requise |
|---|----------|-----------------|
| 1 | Ai-je invoque les superpowers skills necessaires? | Lister lesquels + resultats |
| 2 | Ai-je fait Context7-First pour APIs/libs externes? | Lien ou "N/A - pas d'API externe" |
| 3 | Ai-je fait Validation Croisee MCP (si Keepa)? | Comparaison MCP vs Backend ou "N/A" |
| 4 | Ai-je execute `verification-before-completion`? | Output du skill |
| 5 | Tests passent-ils avec vraies donnees? | Commande + output |
| 6 | Ai-je fait Hostile Code Review? | Liste des edge cases verifies |

### Format de Completion

```markdown
## Checkpoint Validation

1. **Superpowers invoquees** :
   - [x] systematic-debugging (Bug X trouve)
   - [x] verification-before-completion (Output ci-dessous)

2. **Context7-First** : Verifie doc Keepa API pour semantique BSR

3. **Validation Croisee MCP** :
   - MCP: price=24.99, bsr=45230
   - Backend: price=24.99, bsr=45230
   - Delta: 0% - OK

4. **Tests** : `pytest tests/ -v` - 514 passed, 0 failed

5. **Hostile Review** :
   - Edge case null: Couvert par validation Pydantic
   - Race condition: N/A - operations atomiques
   - Division par zero: Check ajoute ligne 145
```

### Consequence

**Si une question reste sans reponse avec preuve = NE PAS dire "c'est fait"**

Repondre plutot : "Tache en cours. Il me reste a : [liste des verifications manquantes]"

---

## Playwright Skills Evaluation (OBLIGATOIRE)

### Quand evaluer Playwright

AVANT toute modification frontend ou test E2E, evaluer si Playwright est necessaire.

### Criteres d'Evaluation

| Critere | Playwright Necessaire? |
|---------|------------------------|
| Test de flux utilisateur complet | OUI |
| Validation visuelle (responsive, layout) | OUI |
| Test d'interaction complexe (drag-drop, modals) | OUI |
| Test API uniquement | NON |
| Modification CSS mineure | NON (sauf si demande) |
| Nouveau composant React | EVALUER (demander) |

### Workflow Obligatoire

1. **Evaluer** : Ce changement necessite-t-il des tests Playwright?

2. **Si OUI** :
   ```
   "Cette modification affecte [description du flux UI].
   Je recommande d'utiliser playwright-skill pour :
   - [Test 1 specifique]
   - [Test 2 specifique]

   Voulez-vous que je lance les tests Playwright?"
   ```
   **ATTENDRE confirmation utilisateur avant d'executer**

3. **Si NON** :
   ```
   "Tests Playwright non necessaires pour cette modification car :
   - [Raison 1]
   - [Raison 2]

   Tests unitaires/integration suffisants."
   ```

### Exemple Concret

**Modification** : Ajout d'un bouton "Refresh" dans le dashboard

**Evaluation** :
- Flux utilisateur affecte? OUI (nouvelle interaction)
- Complexite UI? MOYENNE (clic simple)
- Tests existants couvrent? NON

**Conclusion** :
"Je recommande Playwright pour tester le flux clic-refresh-update.
Voulez-vous que je lance `playwright-skill` pour creer ce test?"

---

## Erreurs Critiques a Eviter

1. NE PAS utiliser `alembic stamp` (utiliser `upgrade head`)
2. NE PAS modifier frontend sans valider backend API d'abord
3. NE PAS commit tokens/cles API dans Git
4. NE PAS sur-implementer features non validees
5. NE PAS assumer PR mergee = donnees en production (tester API)
6. NE PAS diviser BSR Keepa par 100 (c'est un rank integer)
7. NE PAS dire "c'est fait" sans `verification-before-completion`
8. NE PAS utiliser IDs externes sans validation API prealable
9. NE PAS faire de migration DB sans : tester en branch, documenter rollback, convention `YYYYMMDD_description.py`

---

## Ressources Existantes (ArbitrageVault)

- **Tests** : `backend/tests/{api,core,e2e,integration,services}/`
- **Feature Flags** : Header `X-Feature-Flags-Override` + `business_rules.json`
- **Schemas/Contracts** : `backend/app/schemas/*.py` (Pydantic)
- **Memoire projet** : `.claude/{compact_master,compact_current}.md`

---

## Stack & Outils

- **MCP Servers** : GitHub, Context7, Render, Netlify, Neon, TestSprite
- **Backend** : FastAPI + PostgreSQL + SQLAlchemy 2.0
- **Frontend** : React + TypeScript + Vite + Tailwind
- **Validation** : Zod, Pydantic, pytest

---

## References

- **Context7** : Documentation officielle des libs
- **Keepa API** : github.com/keepacom/api_backend (Product.java)
- **Claude Code** : docs.claude.com/en/docs/claude-code

---

**Version** : 3.2 - Zero-Tolerance Engineering + Mandatory Checkpoints + Playwright Evaluation
**Mise a jour** : 2025-12-08
