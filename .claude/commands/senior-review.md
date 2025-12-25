# Senior Review Gate

Verification finale en mode "Senior Developer" avant commit de phases majeures. Identifie gaps, incoherences et manques.

---

## Posture

**Je passe en mode Senior Developer Review.**

- Je ne defends plus le code implemente
- Je cherche activement les failles et gaps
- Je pense utilisateur final, pas juste technique

---

## 5 Questions OBLIGATOIRES

### 1. Quels GAPS existent dans la couverture de tests ?

| Zone | Tests existants | Tests manquants |
|------|-----------------|-----------------|
| [Zone 1] | [X tests] | [Description] |
| [Zone 2] | [X tests] | [Description] |

### 2. Les services combines peuvent-ils produire des resultats ABSURDES ?

| Scenario | Services impliques | Resultat possible | Coherent ? |
|----------|-------------------|-------------------|------------|
| [Scenario 1] | [Service A + B] | [Description] | OK/KO |

### 3. Les seuils/valeurs hardcodes sont-ils documentes et justifies ?

| Seuil | Valeur | Documente ? | Justification |
|-------|--------|-------------|---------------|
| [Seuil 1] | [Valeur] | Oui/Non | [Source ou "A documenter"] |

### 4. Le frontend est-il teste pour cette feature/phase ?

- [ ] Tests unitaires composants
- [ ] Tests E2E Playwright
- [ ] Validation manuelle responsive
- [ ] N/A - Backend uniquement

### 5. Quels edge cases UTILISATEUR ne sont pas geres ?

| Edge case | Gere ? | Action requise |
|-----------|--------|----------------|
| [Edge case 1] | Oui/Non | [Description] |

---

## Verdict

**Gaps identifies :** [Nombre]

| # | Gap | Severite | Action proposee |
|---|-----|----------|-----------------|
| 1 | [Description] | Critique/Important/Mineur | [Fix] |

**Decision :**

- [ ] **PRET** pour commit final (0 gap critique)
- [ ] **NEEDS WORK** - Mini-plan propose ci-dessous
- [ ] **BLOQUER** - Revue architecture necessaire

---

## Anti-Boucle

Si apres 2 iterations des gaps persistent, proposer :
- A) Committer avec gaps documentes dans KNOWN_ISSUES.md
- B) Continuer a iterer (non recommande)
- C) Revoir l'approche/architecture

**ATTENDRE choix explicite de l'utilisateur.**
