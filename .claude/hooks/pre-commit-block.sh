#!/bin/bash
# PreToolUse Hook - Bloque git commit sans checkpoint
# Declenche AVANT execution de Bash tool
# Version: 1.1 - Fixed: output to stderr for exit code 2

# Lire le JSON input depuis stdin
INPUT=$(cat)

# Extraire la commande du tool_input
COMMAND=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' 2>/dev/null || echo "$INPUT")

# Verifier si c'est un git commit ou git push
if echo "$COMMAND" | grep -qE "(git commit|git push)"; then
    # IMPORTANT: Exit code 2 requires stderr for error message (not stdout)
    cat >&2 << 'EOF'

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
avec PREUVES pour chaque point ci-dessus.

Utiliser /checkpoint pour le template complet.
==========================================

EOF

    # Mode BLOQUANT - exit 2 = block selon doc Claude Code
    exit 2
fi

# Autres commandes Bash passent normalement
exit 0
