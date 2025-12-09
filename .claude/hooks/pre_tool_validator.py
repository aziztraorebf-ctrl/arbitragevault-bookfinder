#!/usr/bin/env python3
"""
PreToolUse Hook - Bloque git commit sans checkpoint
Version: 2.0 - Python version for Windows compatibility
"""

import json
import sys
import os
from datetime import datetime

# Debug log
DEBUG_LOG = "C:/Users/azizt/Workspace/arbitragevault_bookfinder/.claude/hooks/hook-debug.log"

def log_debug(message):
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception as e:
        pass  # Ignore logging errors

def main():
    log_debug("Hook triggered")

    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
        log_debug(f"INPUT: {json.dumps(input_data)}")
    except Exception as e:
        log_debug(f"ERROR reading stdin: {e}")
        sys.exit(0)  # Don't block on parse errors

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash commands
    if tool_name != "Bash":
        log_debug(f"Not Bash tool, skipping: {tool_name}")
        sys.exit(0)

    command = tool_input.get("command", "")
    log_debug(f"Command: {command}")

    # Check for git commit or git push
    if "git commit" in command or "git push" in command:
        log_debug("BLOCKED: git commit/push detected")

        # Print to stderr (shown to Claude when exit code is 2)
        error_message = """
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
==========================================
"""
        print(error_message, file=sys.stderr)
        sys.exit(2)  # Exit code 2 = block tool call

    log_debug("Command allowed")
    sys.exit(0)

if __name__ == "__main__":
    main()
