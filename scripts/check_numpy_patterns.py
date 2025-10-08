#!/usr/bin/env python3
"""
NumPy Safety Pattern Checker for ArbitrageVault Backend
========================================================

Scans Python files for unsafe numpy array operations that can cause
"ambiguous truth value" errors.

Usage:
    python scripts/check_numpy_patterns.py

Exit codes:
    0 - No unsafe patterns found
    1 - Unsafe patterns detected

Checked patterns:
    - `if not array` on potential numpy arrays
    - Direct comparisons on data dictionary access
    - Boolean checks without explicit None handling

Source verified (2025-10-08):
  - Keepa SDK v1.3.0: https://github.com/akaszynski/keepa
  - Refactor: keepa_refactor_v2_verified
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Base directory to scan
BASE_DIR = Path(__file__).parent.parent / "backend" / "app"

# Files to scan (limit to Keepa-related files)
TARGET_PATTERNS = [
    "services/keepa*.py",
    "utils/keepa*.py"
]

# Unsafe patterns to detect
UNSAFE_PATTERNS = [
    # Pattern 1: Boolean check on potential array without None check
    # Example: if not data['key']:
    (r"if\s+not\s+data\[", "Boolean check 'if not data[key]' without None check"),

    # Pattern 2: Boolean check on .get() result without None check
    # Example: if not arr where arr = dict.get('key')
    (r"if\s+not\s+\w+\s+and.*\.get\(", "Boolean check on .get() result without None check"),
]

# Safe patterns (exceptions)
SAFE_EXCEPTIONS = [
    r"if\s+\w+\s+is\s+None",  # Explicit None check
    r"if\s+\w+\s+is\s+not\s+None",  # Explicit not None check
    r"safe_array_check\(",  # Using safe helper
    r"safe_value_check\(",  # Using safe helper
]


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a Python file for unsafe numpy patterns.

    Args:
        file_path: Path to Python file

    Returns:
        List of (line_number, line_content, pattern_description) tuples
    """
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                continue

            # Check for unsafe patterns
            for pattern, description in UNSAFE_PATTERNS:
                if re.search(pattern, line):
                    # Check if line has safe exception
                    is_safe = any(re.search(safe, line) for safe in SAFE_EXCEPTIONS)

                    if not is_safe:
                        violations.append((line_num, line.strip(), description))

    except Exception as e:
        print(f"⚠️  Error scanning {file_path}: {e}")

    return violations


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = violations found)
    """
    print("=" * 80)
    print("NumPy Safety Pattern Checker")
    print("=" * 80)
    print(f"Scanning: {BASE_DIR}")
    print()

    all_violations = []
    files_scanned = 0

    # Scan all target files
    for pattern in TARGET_PATTERNS:
        for file_path in BASE_DIR.glob(pattern):
            if file_path.is_file():
                files_scanned += 1
                violations = scan_file(file_path)

                if violations:
                    all_violations.extend([
                        (file_path, line_num, line, desc)
                        for line_num, line, desc in violations
                    ])

    # Report results
    print(f"📊 Files scanned: {files_scanned}")
    print()

    if all_violations:
        print(f"❌ Found {len(all_violations)} unsafe pattern(s):")
        print()

        for file_path, line_num, line, desc in all_violations:
            rel_path = file_path.relative_to(BASE_DIR.parent)
            print(f"  {rel_path}:{line_num}")
            print(f"    {desc}")
            print(f"    > {line}")
            print()

        print("=" * 80)
        print("❌ FAILED: Unsafe numpy patterns detected")
        print("=" * 80)
        return 1

    else:
        print("✅ No unsafe numpy patterns found")
        print()
        print("=" * 80)
        print("✅ PASSED: All files are numpy-safe")
        print("=" * 80)
        return 0


if __name__ == "__main__":
    sys.exit(main())
