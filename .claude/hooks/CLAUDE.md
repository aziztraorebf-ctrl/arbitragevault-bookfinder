# Hooks ArbitrageVault

## Hooks actifs

### pre-commit-block.sh (PreToolUse - matcher: Bash)
- **Declenche** : avant git commit ou git push
- **Action** : bloque si pas de flag checkpoint-approved
- **Deblocage** : touch .claude/checkpoint-approved

### stop-checkpoint.sh (Stop)
- **Declenche** : a la fin de chaque tour Claude
- **Action** : rappel checkpoint obligatoire

## Ordre d'execution
Les hooks PreToolUse s'executent dans l'ordre de leur declaration dans settings.json.
