# ArbitrageVault BookFinder - Production v1.6

Professional Book Arbitrage Analysis Platform - Full-Stack Application

Complete application for identifying profitable book arbitrage opportunities with **production backend** and **deployed frontend**.

---

## Project Status - December 2025

### FULL-STACK COMPLETE - PRODUCTION

| Component | Status | URL |
|-----------|--------|-----|
| Backend API | Production | https://arbitragevault-backend-v2.onrender.com |
| Frontend | Deployed | https://arbitragevault.netlify.app |
| Database | Neon PostgreSQL | 300-500 concurrent connections |

### Test Coverage
- **483 tests passing** (349+ unit tests + 56 E2E tests)
- Phases 1-7 validated with real Keepa API data

---

## Architecture Overview

```
Frontend (Netlify)          Backend (Render)           Database (Neon)
React 18 + TypeScript  -->  FastAPI + SQLAlchemy  -->  PostgreSQL
Tailwind CSS + Vite         Real Keepa API             Production-grade
```

### Key Features
- **AutoSourcing**: Automated product discovery from Keepa bestsellers
- **Token Control**: Safeguards preventing API waste (Phase 5)
- **Real-Time Metrics**: BSR, price history, velocity scoring
- **Niche Discovery**: Category-based opportunity finding

---

## Project Structure

```
arbitragevault-bookfinder/
├── backend/                   # FastAPI application
│   ├── app/                   # Core application code
│   │   ├── api/v1/           # API endpoints (20+ routes)
│   │   ├── services/         # Business logic
│   │   └── models/           # SQLAlchemy models
│   └── tests/                 # Test suite (483 tests)
├── frontend/                  # React 18 application
│   ├── src/                   # Source code
│   │   ├── components/       # UI components
│   │   ├── pages/            # Route pages
│   │   └── services/         # API client
│   └── e2e/                   # Playwright E2E tests
└── docs/                      # Architecture documentation
```

---

## Quick Start

### Production API
```bash
# Health check
curl "https://arbitragevault-backend-v2.onrender.com/health"
# Response: {"status":"ready","service":"ArbitrageVault API","version":"1.6.3"}

# API Documentation
open "https://arbitragevault-backend-v2.onrender.com/docs"

# Frontend
open "https://arbitragevault.netlify.app"
```

### Local Development

**Backend:**
```bash
cd backend
uv venv && .venv\Scripts\activate.bat
uv pip install -r requirements.txt
cp .env.example .env
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Foundation Infrastructure | Complete |
| Phase 2 | Database Migration (Neon) | Complete |
| Phase 3 | Keepa API Integration | Complete |
| Phase 4 | Business Logic & Scoring | Complete |
| Phase 5 | Token Control Safeguards | Complete |
| Phase 6 | Frontend E2E Tests | Complete |
| Phase 7 | AutoSourcing Production | Complete |

---

## Documentation

- [Backend README](./backend/README.md) - Backend setup and API
- [API Documentation](./backend/API_DOCUMENTATION.md) - REST API reference
- [Architecture Guide](./docs/ARCHITECTURE.md) - Technical architecture
- [Deployment Guide](./backend/DEPLOYMENT.md) - Production deployment

---

**Current Version**: v1.6.3
**Backend**: https://arbitragevault-backend-v2.onrender.com
**Frontend**: https://arbitragevault.netlify.app
