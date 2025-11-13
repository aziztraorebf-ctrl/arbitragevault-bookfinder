#!/usr/bin/env python3
"""Test imports."""

try:
    from app.api.v1.routers.analyses import router
    print('✅ analyses router imports OK')
except Exception as e:
    print(f'❌ analyses router error: {e}')

try:
    from app.api.v1.routers.batches import router  
    print('✅ batches router imports OK')
except Exception as e:
    print(f'❌ batches router error: {e}')

try:
    from app.main import app
    print('✅ main app imports OK')
except Exception as e:
    print(f'❌ main app error: {e}')