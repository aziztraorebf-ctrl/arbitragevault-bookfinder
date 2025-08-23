#!/usr/bin/env python3
"""Test simple d'import"""
import sys
print('Python:', sys.executable)

try:
    from app.main import app
    print('✅ App import successful')
    
    # Test simple du serveur
    import uvicorn
    print('✅ Uvicorn available')
    
except Exception as e:
    print('❌ Import failed:', e)
    import traceback
    traceback.print_exc()