# Hooks ArbitrageVault

## Hooks actifs

### pre-commit-block.sh (PreToolUse - matcher: Bash)
- **Declenche** : avant git commit ou git push
- **Action** : bloque si pas de flag checkpoint-approved
- **Deblocage** : touch .claude/checkpoint-approved

### circuit-breaker.sh (PreToolUse - matcher: Edit|Write)
- **Declenche** : avant chaque Edit ou Write tool
- **Action** : bloque apres 3 editions consecutives du meme fichier
- **State** : .claude/circuit-breaker-state.json
- **Deblocage** : echo ALL > .claude/circuit-breaker-reset (ou chemin de fichier specifique)
- **Objectif** : forcer re-evaluation si Claude tourne en boucle

### stop-checkpoint.sh (Stop)
- **Declenche** : a la fin de chaque tour Claude
- **Action** : rappel checkpoint obligatoire

## Ordre d'execution
Les hooks PreToolUse s'executent dans l'ordre de leur declaration dans settings.json.
