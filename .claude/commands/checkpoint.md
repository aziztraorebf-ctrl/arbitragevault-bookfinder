# Checkpoint Validation Template

Affiche le template complet de Checkpoint Validation selon CLAUDE.md v3.2.

---

## Checkpoint Validation

### 1. Superpowers invoquees

- [ ] `systematic-debugging` : [Resultat ou N/A]
- [ ] `verification-before-completion` : [Resultat]
- [ ] `test-driven-development` : [Resultat ou N/A]
- [ ] `root-cause-tracing` : [Resultat ou N/A]
- [ ] `defense-in-depth` : [Resultat ou N/A]
- [ ] `requesting-code-review` : [Resultat ou N/A]

### 2. Context7-First

- [ ] Documentation officielle consultee : [Lien ou N/A - pas d'API externe]
- [ ] Version API verifiee : [Version ou N/A]

### 3. Validation Croisee MCP (si Keepa)

| Source | Prix | BSR | Autres |
|--------|------|-----|--------|
| MCP Direct | $ | # | |
| Backend API | $ | # | |
| Delta | % | % | OK/KO |

Si delta > 1% : BLOQUER et investiguer

### 4. Tests

```bash
# Commande executee :
pytest tests/ -v

# Resultat :
X passed, Y failed, Z skipped
```

### 5. Hostile Code Review

| Edge Case | Statut | Action |
|-----------|--------|--------|
| Null/undefined | [ ] | |
| Division par zero | [ ] | |
| Race condition | [ ] | |
| Donnees invalides | [ ] | |
| Error handling | [ ] | |

### 6. Conclusion

- [ ] TOUTES les preuves fournies
- [ ] Tests passent avec vraies donnees
- [ ] Pret pour commit/merge

---

**Rappel** : Si une question reste sans preuve = NE PAS dire "c'est fait"
