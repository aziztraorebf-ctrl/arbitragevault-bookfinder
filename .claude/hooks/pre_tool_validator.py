#!/usr/bin/env python3
"""
PreToolUse Hook - Bloque git commit sans checkpoint valide
Version: 3.0 - Validation par fichier checkpoint avec expiration 30 min
"""

import json
import sys
import os
from datetime import datetime, timezone

# Paths
PROJECT_ROOT = "C:/Users/azizt/Workspace/arbitragevault_bookfinder"
CHECKPOINT_FILE = os.path.join(PROJECT_ROOT, ".claude", "checkpoint_validated.json")
DEBUG_LOG = os.path.join(PROJECT_ROOT, ".claude", "hooks", "hook-debug.log")

# Configuration
CHECKPOINT_VALIDITY_MINUTES = 30


def log_debug(message):
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass


def is_checkpoint_valid():
    """Check if a valid checkpoint file exists and is not expired."""
    try:
        if not os.path.exists(CHECKPOINT_FILE):
            log_debug("Checkpoint file does not exist")
            return False, "Fichier checkpoint non trouve"

        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        timestamp_str = data.get("timestamp")
        if not timestamp_str:
            log_debug("Checkpoint has no timestamp")
            return False, "Checkpoint sans timestamp"

        # Parse timestamp
        checkpoint_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_minutes = (now - checkpoint_time).total_seconds() / 60

        log_debug(f"Checkpoint age: {age_minutes:.1f} minutes (max: {CHECKPOINT_VALIDITY_MINUTES})")

        if age_minutes > CHECKPOINT_VALIDITY_MINUTES:
            return False, f"Checkpoint expire (age: {age_minutes:.0f} min, max: {CHECKPOINT_VALIDITY_MINUTES} min)"

        # Valid checkpoint
        tests_passed = data.get("tests_passed", "unknown")
        return True, f"Checkpoint valide - Tests: {tests_passed}"

    except json.JSONDecodeError as e:
        log_debug(f"JSON parse error: {e}")
        return False, "Erreur parsing checkpoint JSON"
    except Exception as e:
        log_debug(f"Error checking checkpoint: {e}")
        return False, f"Erreur: {e}"


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
        log_debug("Git commit/push detected, checking checkpoint...")

        is_valid, message = is_checkpoint_valid()

        if is_valid:
            log_debug(f"ALLOWED: {message}")
            sys.exit(0)  # Allow the commit

        log_debug(f"BLOCKED: {message}")

        # Print to stderr (shown to Claude when exit code is 2)
        error_message = f"""
==========================================
  CHECKPOINT OBLIGATOIRE AVANT COMMIT
==========================================

Status: {message}

Pour debloquer le commit:

1. Invoquer le skill verification-before-completion
2. Fournir les preuves du checkpoint:
   - Tests executes (pytest output)
   - Context7-First fait (si API externe)
   - Hostile review fait (edge cases)

Le skill creera automatiquement le fichier checkpoint.
Validite: {CHECKPOINT_VALIDITY_MINUTES} minutes

==========================================
"""
        print(error_message, file=sys.stderr)
        sys.exit(2)  # Exit code 2 = block tool call

    log_debug("Command allowed")
    sys.exit(0)


if __name__ == "__main__":
    main()
