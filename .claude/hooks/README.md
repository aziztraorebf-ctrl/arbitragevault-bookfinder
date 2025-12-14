# Claude Code Hooks - Checkpoint System

> **Version:** 3.0
> **Derniere mise a jour:** 2025-12-13

## Vue d'ensemble

Ce systeme de hooks enforce le workflow de qualite Zero-Tolerance Engineering en bloquant les commits Git jusqu'a ce qu'un checkpoint valide soit fourni.

## Architecture

```
.claude/hooks/
    README.md                 # Cette documentation
    pre_tool_validator.py     # Hook principal PreToolUse (v3.0)
    pre-commit-block.sh       # Version bash (legacy)
    stop_checkpoint.py        # Hook Stop - rappel checkpoint
    stop-checkpoint.sh        # Version bash (legacy)
    hook-debug.log           # Logs de debug (genere automatiquement)

.claude/
    checkpoint_validated.json # Fichier de preuve checkpoint
    settings.json             # Configuration hooks
    settings.local.json       # Configuration locale (API keys)
```

## Hooks disponibles

### 1. PreToolUse Hook (pre_tool_validator.py)

**Declencheur:** Avant chaque appel a l'outil Bash
**Action:** Bloque `git commit` et `git push` si pas de checkpoint valide

#### Fonctionnement

1. Detecte les commandes `git commit` ou `git push`
2. Verifie l'existence de `.claude/checkpoint_validated.json`
3. Valide que le checkpoint n'est pas expire (30 minutes)
4. Exit code 2 = bloque la commande avec message d'erreur

### 2. Stop Hook (stop_checkpoint.py)

**Declencheur:** A la fin de chaque tour Claude
**Action:** Affiche un rappel pour le checkpoint validation

## Fichier Checkpoint

Le fichier `.claude/checkpoint_validated.json` est cree automatiquement par le skill `verification-before-completion`.

### Format

```json
{
  "timestamp": "2025-12-13T18:45:00+00:00",
  "tests_passed": "23/23 (Phase 4 Batch 2)",
  "verification_skill_invoked": true,
  "context7_done": true,
  "hostile_review_done": true,
  "phase": "Phase 4 Batch 2",
  "tasks_completed": ["I4", "I7"]
}
```

### Validite

- **Duree:** 30 minutes (configurable via CHECKPOINT_VALIDITY_MINUTES)
- **Expiration:** Apres 30 minutes, un nouveau checkpoint est requis

## Workflow

```
1. Implementer feature/fix
       |
       v
2. Executer tests (pytest, npm build)
       |
       v
3. Invoquer skill verification-before-completion
       |
       v
4. Fournir preuves:
   - Tests executes (output)
   - Context7-First (si API externe)
   - Hostile review (edge cases)
       |
       v
5. Checkpoint file cree automatiquement
       |
       v
6. git commit autorise (30 min window)
```

## Debloquer un commit

Si le hook bloque un commit:

1. Invoquer le skill: verification-before-completion
2. Fournir les preuves: output tests, docs, edge cases
3. Le skill cree le fichier checkpoint
4. Retenter le commit (dans les 30 minutes)

## Debug

Logs dans `.claude/hooks/hook-debug.log`:

```
[2025-12-13T18:45:00] Hook triggered
[2025-12-13T18:45:00] Command: git commit -m "..."
[2025-12-13T18:45:00] Checkpoint age: 15.2 minutes (max: 30)
[2025-12-13T18:45:00] ALLOWED: Checkpoint valide - Tests: 23/23
```

## Exit codes

| Code | Signification |
|------|--------------|
| 0    | Commande autorisee |
| 2    | Commande bloquee (checkpoint requis) |

## References

- Claude Code Hooks Documentation: https://docs.anthropic.com/en/docs/claude-code/hooks
- CLAUDE.md - Zero-Tolerance Engineering
