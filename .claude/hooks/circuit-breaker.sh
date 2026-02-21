#!/bin/bash
# PreToolUse Hook - Circuit Breaker anti-boucle
# Detecte quand le meme fichier est edite 3+ fois consecutivement
# et force un STOP pour re-evaluation.
#
# Declenche AVANT chaque appel Edit ou Write tool.
# State persiste dans .claude/circuit-breaker-state.json

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="$PROJECT_DIR/.claude/circuit-breaker-state.json"
RESET_FILE="$PROJECT_DIR/.claude/circuit-breaker-reset"
MAX_EDITS=3

INPUT=$(cat)

# Extraire le type de tool
TOOL_NAME=$(echo "$INPUT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

# Seulement surveiller Edit et Write
if [ "$TOOL_NAME" != "Edit" ] && [ "$TOOL_NAME" != "Write" ]; then
    exit 0
fi

# Extraire le fichier cible
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Initialiser le state si inexistant
if [ ! -f "$STATE_FILE" ]; then
    echo '{"edits":{},"last_reset":""}' > "$STATE_FILE"
fi

# Si le fichier de reset existe, effacer le state pour ce fichier
if [ -f "$RESET_FILE" ]; then
    TARGET_FILE=$(cat "$RESET_FILE")
    if [ "$TARGET_FILE" = "$FILE_PATH" ] || [ "$TARGET_FILE" = "ALL" ]; then
        python3 -c "
import json
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
except:
    state = {'edits': {}, 'last_reset': ''}
target = '$TARGET_FILE'
if target == 'ALL':
    state['edits'] = {}
elif target in state['edits']:
    del state['edits'][target]
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
" 2>/dev/null
        rm -f "$RESET_FILE"
    fi
fi

# Lire le state actuel
CURRENT_COUNT=$(python3 -c "
import json
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    print(state.get('edits', {}).get('$FILE_PATH', 0))
except:
    print(0)
" 2>/dev/null)

NEW_COUNT=$((CURRENT_COUNT + 1))

# Mettre a jour le compteur
python3 -c "
import json
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
except:
    state = {'edits': {}, 'last_reset': ''}
state.setdefault('edits', {})
state['edits']['$FILE_PATH'] = $NEW_COUNT
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
" 2>/dev/null

# Bloquer si seuil atteint
if [ "$NEW_COUNT" -ge "$MAX_EDITS" ]; then
    echo "" >&2
    echo "==========================================" >&2
    echo "  CIRCUIT BREAKER ACTIVE - STOP" >&2
    echo "==========================================" >&2
    echo "" >&2
    echo "  Fichier : $FILE_PATH" >&2
    echo "  Editions consecutives : $NEW_COUNT / $MAX_EDITS" >&2
    echo "" >&2
    echo "  Ce fichier a ete edite $NEW_COUNT fois sans" >&2
    echo "  resolution confirmee. Possible boucle infinie." >&2
    echo "" >&2
    echo "  ACTIONS REQUISES :" >&2
    echo "  1. STOP - Ne pas continuer a editer" >&2
    echo "  2. Analyser la vraie cause racine" >&2
    echo "  3. Invoquer systematic-debugging" >&2
    echo "  4. Presenter options a l utilisateur" >&2
    echo "" >&2
    echo "  Pour debloquer apres resolution :" >&2
    echo "  echo ALL > .claude/circuit-breaker-reset" >&2
    echo "  ou" >&2
    echo "  echo chemin/du/fichier > .claude/circuit-breaker-reset" >&2
    echo "" >&2
    echo "==========================================" >&2
    exit 2
fi

exit 0
