# ArbitrageVault Backend

FastAPI backend for the ArbitrageVault BookFinder platform.

## Production

**URL**: https://arbitragevault-backend-v2.onrender.com
**Docs**: https://arbitragevault-backend-v2.onrender.com/docs

## Tech Stack

- **FastAPI** 0.104+ with async/await
- **SQLAlchemy 2.0** with async support
- **Neon PostgreSQL** (300-500 concurrent connections)
- **Pydantic v2** for validation
- **Keepa API** for product data
- **Firebase Admin SDK** for authentication

## Quick Start

### Production API
```bash
# Health check
curl "https://arbitragevault-backend-v2.onrender.com/health"
# Response: {"status":"ready","service":"ArbitrageVault API","version":"1.6.3"}

# API Documentation
open "https://arbitragevault-backend-v2.onrender.com/docs"
```

### Local Development
```bash
cd backend
uv venv && .venv\Scripts\activate.bat
uv pip install -r requirements.txt
cp .env.example .env
uv run uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── routers/      # Route handlers
│   │   └── endpoints/    # Business endpoints
│   ├── services/         # Business logic
│   ├── models/           # SQLAlchemy models
│   └── schemas/          # Pydantic schemas
├── tests/                 # Test suite (880+ tests)
├── alembic/               # Database migrations
└── requirements.txt       # Dependencies
```

## API Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| Health | /health | System status |
| Auth | /api/v1/auth | Firebase authentication |
| Batches | /api/v1/batches | Batch management |
| Analyses | /api/v1/analyses | Analysis results |
| Keepa | /api/v1/keepa | Keepa integration |
| AutoSourcing | /api/v1/autosourcing | Product discovery |
| Niches | /api/v1/niches | Niche discovery |
| Bookmarks | /api/v1/bookmarks | Saved niches/searches |
| Searches | /api/v1/searches | Mes Recherches |
| Analytics | /api/v1/analytics | Business analytics |
| Config | /api/v1/config | Configuration |
| Views | /api/v1/views | View scoring |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific module
pytest tests/test_keepa_parsing.py -v
```

## Environment Variables

Required in `.env`:
```
DATABASE_URL=postgresql://...
KEEPA_API_KEY=your_key
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
```

## Documentation

- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - REST API reference
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [CHANGELOG.md](./CHANGELOG.md) - Version history
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide

---

**Version**: 1.7.0
**Frontend**: https://arbitragevault.netlify.app
