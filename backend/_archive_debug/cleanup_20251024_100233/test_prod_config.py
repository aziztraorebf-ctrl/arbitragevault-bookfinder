#!/usr/bin/env python3
"""Test configuration production."""

import os

# Force config production
os.environ['DEBUG'] = 'false'
os.environ['ENABLE_DOCS'] = 'false'
os.environ['ENABLE_REDOC'] = 'false'

from app.main import app

print('🔒 Test Configuration Production')
print('=' * 35)
print(f'DEBUG: {os.environ.get("DEBUG", "default")}')
print(f'Docs URL: {app.docs_url}')
print(f'Redoc URL: {app.redoc_url}')
print(f'OpenAPI URL: {app.openapi_url}')

if app.docs_url is None and app.redoc_url is None:
    print('✅ Swagger/Redoc désactivés en production')
else:
    print('❌ Swagger/Redoc encore actifs')