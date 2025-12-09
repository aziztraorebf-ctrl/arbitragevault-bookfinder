#!/usr/bin/env python3
"""
Stop Hook - Rappel Checkpoint Validation
Declenche a la fin de chaque tour Claude
Version: 2.1 - With debug logging
"""

import json
import sys
from datetime import datetime

DEBUG_LOG = "C:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/hooks/stop-debug.log"

def log_debug(message):
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass

def main():
    log_debug("Stop hook triggered")

    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
        log_debug(f"INPUT: {json.dumps(input_data)}")
    except Exception as e:
        log_debug(f"No stdin or error: {e}")
        input_data = {}

    # Print reminder to stderr (shown to Claude/user)
    reminder = """
==========================================
  CHECKPOINT REMINDER
==========================================

Si cette tache est TERMINEE, fournir:

## Checkpoint Validation

1. **Superpowers invoquees** : [liste + resultats]
2. **Context7-First** : [lien doc ou N/A]
3. **Validation Croisee MCP** : [comparaison ou N/A]
4. **Tests** : [commande + output]
5. **Hostile Review** : [edge cases verifies]

==========================================
"""
    print(reminder, file=sys.stderr)
    log_debug("Reminder printed to stderr")

    # Exit 0 = allow stop (don't block)
    sys.exit(0)

if __name__ == "__main__":
    main()
