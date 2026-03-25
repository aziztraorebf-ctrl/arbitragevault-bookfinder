# Security Policy

## Secret Rotation Log
- Keepa API key: rotated 2026-03-25
- Database credentials: protected via Neon connection string, not exposed in code
- SECRET_KEY: defined as environment variable on Render

## Sensitive Files
- `backend/.env` — never committed, listed in .gitignore
- `backend/.env.autoscheduler` — removed from git tracking 2026-03-25
- `frontend/.env` — never committed, listed in .gitignore

## Pre-commit Protection
detect-secrets hook blocks any commit containing API keys or tokens. Run `pre-commit install` after cloning.
