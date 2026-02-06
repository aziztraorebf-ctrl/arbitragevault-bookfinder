#!/bin/bash
# PreToolUse Hook - Bloque git commit sans checkpoint
# Declenche AVANT execution de Bash tool
# Version: 2.0 - Ajout mecanisme de deblocage via fichier flag
#
# Usage: Pour debloquer un commit apres validation checkpoint,
# creer le fichier .claude/checkpoint-approved
# Le fichier est automatiquement supprime apres le commit.

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APPROVE_FLAG="$PROJECT_DIR/.claude/checkpoint-approved"

# Lire le JSON input depuis stdin
INPUT=$(cat)

# Extraire la commande du tool_input (compatible macOS - pas de grep -oP)
COMMAND=$(echo "$INPUT" | sed -n 's/.*"command"\s*:\s*"\([^"]*\)".*/\1/p')
if [ -z "$COMMAND" ]; then
    COMMAND="$INPUT"
fi

# Verifier si c'est un git commit ou git push
if echo "$COMMAND" | grep -qE "(git commit|git push)"; then
    # Verifier si le checkpoint a ete approuve
    if [ -f "$APPROVE_FLAG" ]; then
        # Checkpoint approuve - supprimer le flag et laisser passer
        rm -f "$APPROVE_FLAG"
        exit 0
    fi

    # Pas de flag = BLOQUER
    cat >&2 << 'CHECKPOINT_MSG'

==========================================
  CHECKPOINT OBLIGATOIRE AVANT COMMIT
==========================================

STOP! Avant de committer, verifier:

1. Superpowers skills invoques?
   - systematic-debugging (si bug)
   - verification-before-completion
   - test-driven-development (si feature)

2. Context7-First fait pour APIs externes?

3. Validation Croisee MCP (si Keepa)?
   - MCP direct vs Backend API
   - Delta < 1%?

4. Tests passent avec vraies donnees?
   - pytest / npm test execute?

5. Hostile Code Review fait?
   - Edge cases identifies?
   - Null checks?
   - Error handling?

==========================================
  COMMIT BLOQUE - Checkpoint requis
==========================================

Pour debloquer, fournir le Checkpoint Validation
avec PREUVES pour chaque point ci-dessus,
puis creer .claude/checkpoint-approved

Utiliser /checkpoint pour le template complet.
==========================================

CHECKPOINT_MSG

    exit 2
fi

# Autres commandes Bash passent normalement
exit 0
