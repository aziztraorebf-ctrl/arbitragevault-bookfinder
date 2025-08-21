#!/usr/bin/env python3
"""
Quick launcher for ArbitrageVault audit suite
Usage: python run_audit.py [--mode quick|full|benchmark]
"""
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.audit.audit_runner import main

if __name__ == '__main__':
    # Add some default arguments if none provided
    if len(sys.argv) == 1:
        sys.argv.append('--mode')
        sys.argv.append('quick')
    
    asyncio.run(main())