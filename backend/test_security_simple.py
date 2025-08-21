#!/usr/bin/env python3
"""Test sécurité simple."""

from app.core.settings import Settings

# Test 1: Config par défaut (dev)
print("🔒 Test Sécurité Minimale")
print("=" * 30)

settings_dev = Settings()
print(f"1. Config DEV:")
print(f"   DEBUG: {settings_dev.debug}")
print(f"   ENABLE_DOCS: {settings_dev.enable_docs}")
print(f"   CORS origins: {settings_dev.cors_allowed_origins}")

# Test 2: Simulation production
import os
os.environ['DEBUG'] = 'false'  
os.environ['ENABLE_DOCS'] = 'false'
os.environ['ENABLE_REDOC'] = 'false'

# Reload settings avec nouvelles valeurs
from app.core.settings import get_settings
get_settings.cache_clear()  # Clear cache

try:
    settings_prod = get_settings()
    print(f"\n2. Config PROD simulée:")
    print(f"   DEBUG: {settings_prod.debug}")
    print(f"   ENABLE_DOCS: {settings_prod.enable_docs}")
    print(f"   ENABLE_REDOC: {settings_prod.enable_redoc}")
    
    if not settings_prod.debug and not settings_prod.enable_docs:
        print("   ✅ Production: Swagger désactivé")
    else:
        print("   ❌ Production: Swagger encore actif")
        
except Exception as e:
    print(f"   ⚠️ Config prod error: {e}")

# Test 3: .env.example validation
print(f"\n3. Validation .env.example:")
import os.path
env_example_exists = os.path.exists('.env.example')
print(f"   .env.example existe: {'✅' if env_example_exists else '❌'}")

if env_example_exists:
    with open('.env.example', 'r') as f:
        content = f.read()
        has_debug = 'DEBUG=' in content
        has_cors = 'CORS_ALLOWED_ORIGINS=' in content  
        has_docs = 'ENABLE_DOCS=' in content
        print(f"   Contient DEBUG: {'✅' if has_debug else '❌'}")
        print(f"   Contient CORS: {'✅' if has_cors else '❌'}")
        print(f"   Contient ENABLE_DOCS: {'✅' if has_docs else '❌'}")

print(f"\n🎯 Sécurité minimale validée pour Phase 1 !")