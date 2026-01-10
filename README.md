# ArbitrageVault BookFinder - Production v1.7

Professional Book Arbitrage Analysis Platform - Full-Stack Application with Firebase Authentication

Complete application for identifying profitable book arbitrage opportunities with **production backend** and **deployed frontend**.

---

## Project Status - January 2026

### FULL-STACK COMPLETE - PRODUCTION LIVE

| Component | Status | URL |
|-----------|--------|-----|
| Backend API | Production | https://arbitragevault-backend-v2.onrender.com |
| Frontend | Deployed | https://arbitragevault.netlify.app |
| Database | Neon PostgreSQL | Production-grade |
| Authentication | Firebase Auth | Email/Password |

### Test Coverage
- **880+ tests passing** (unit + integration + E2E)
- Phases 1-13 validated

---

## Architecture Overview

```
Frontend (Netlify)          Backend (Render)           External Services
React 18 + TypeScript  -->  FastAPI + SQLAlchemy  -->  Neon PostgreSQL
Firebase SDK               Firebase Admin SDK         Firebase Auth
Tailwind CSS + Vite        Keepa API Integration      Keepa API
```

### Key Features
- **Firebase Authentication**: Secure login/register with email/password
- **AutoSourcing**: Automated product discovery from Keepa bestsellers
- **Token Control**: Safeguards preventing API waste
- **Real-Time Metrics**: BSR, price history, velocity scoring
- **Niche Discovery**: Category-based opportunity finding
- **Mes Recherches**: Centralized search results with 30-day retention
- **Mobile-First UX**: Responsive design with touch-friendly UI

---

## Project Structure

```
arbitragevault-bookfinder/
├── backend/                   # FastAPI application
│   ├── app/                   # Core application code
│   │   ├── api/v1/           # API endpoints (40+ routes)
│   │   ├── services/         # Business logic
│   │   ├── core/             # Auth, DB, Firebase config
│   │   └── models/           # SQLAlchemy models
│   └── tests/                 # Test suite (600+ tests)
├── frontend/                  # React 18 application
│   ├── src/                   # Source code
│   │   ├── components/       # UI components + auth
│   │   ├── contexts/         # AuthContext
│   │   ├── pages/            # Route pages
│   │   └── services/         # API client
│   └── tests/                 # Playwright E2E tests
└── .claude/                   # Project memory & config
```

---

## Quick Start

### Production

```bash
# Health check
curl "https://arbitragevault-backend-v2.onrender.com/health"
# Response: {"status":"ok"}

# API Documentation
open "https://arbitragevault-backend-v2.onrender.com/docs"

# Frontend
open "https://arbitragevault.netlify.app"
```

### Local Development

**Backend:**
```bash
cd backend
uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
cp .env.example .env  # Configure DATABASE_URL, KEEPA_API_KEY, FIREBASE_*
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local  # Configure VITE_API_URL, VITE_FIREBASE_*
npm run dev
```

---

## Completed Phases

| Phase | Description | Date | Status |
|-------|-------------|------|--------|
| 1 | Foundation Infrastructure | Nov 2025 | Complete |
| 2 | Keepa API Integration | Nov 2025 | Complete |
| 3 | Product Discovery MVP | Dec 2025 | Complete |
| 4 | Backlog Cleanup | Dec 2025 | Complete |
| 5 | Niche Bookmarks | Dec 2025 | Complete |
| 6 | Niche Discovery Optimization | Dec 2025 | Complete |
| 7 | AutoSourcing Safeguards | Dec 2025 | Complete |
| 8 | Advanced Analytics | Dec 2025 | Complete |
| 9 | UI Completion | Dec 2025 | Complete |
| 10 | Unified Product Table | Jan 2026 | Complete |
| 11 | Page Centrale Recherches | Jan 2026 | Complete |
| 12 | UX Mobile-First | Jan 2026 | Complete |
| 13 | Firebase Authentication | Jan 2026 | Complete |

---

## Configuration

### Backend Environment Variables (Render)

```env
DATABASE_URL=postgresql://...@neon.tech/neondb
KEEPA_API_KEY=<your-keepa-key>
FIREBASE_PROJECT_ID=<project-id>
FIREBASE_PRIVATE_KEY=<private-key>
FIREBASE_CLIENT_EMAIL=<client-email>
SENTRY_DSN=<optional>
```

### Frontend Environment Variables (Netlify)

```env
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
VITE_FIREBASE_API_KEY=<api-key>
VITE_FIREBASE_AUTH_DOMAIN=<domain>
VITE_FIREBASE_PROJECT_ID=<project-id>
VITE_FIREBASE_STORAGE_BUCKET=<bucket>
VITE_FIREBASE_MESSAGING_SENDER_ID=<sender-id>
VITE_FIREBASE_APP_ID=<app-id>
```

---

## Documentation

- [Backend README](./backend/README.md) - Backend setup and API
- [API Documentation](./backend/API_DOCUMENTATION.md) - REST API reference
- [Frontend README](./frontend/README.md) - Frontend setup
- [Project Memory](./.claude/compact_master.md) - Full project history

---

**Current Version**: v1.7.0
**Last Updated**: January 10, 2026
**Backend**: https://arbitragevault-backend-v2.onrender.com
**Frontend**: https://arbitragevault.netlify.app
