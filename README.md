# ArbitrageVault BookFinder - Production v2.2

Professional Book Arbitrage Analysis Platform - Full-Stack Application with Firebase Authentication and Agent API Integration.

Complete application for identifying profitable book arbitrage opportunities with **production backend**, **deployed frontend**, and **AI agent integration** (CoWork/N8N).

---

## Project Status - March 2026

### FULL-STACK COMPLETE - PRODUCTION LIVE

| Component | Status | URL |
|-----------|--------|-----|
| Backend API | Production | https://arbitragevault-backend-v2.onrender.com |
| Frontend | Deployed | https://arbitragevault.netlify.app |
| Database | Neon PostgreSQL | Production-grade |
| Authentication | Firebase Auth | Email/Password |
| Agent API | CoWork/N8N | Bearer token + API Keys |

### Test Coverage
- **800+ tests passing** (unit + integration + E2E)
- Phases 1-13 + Phase C + Bugfixes + Security + P2 validated

---

## Architecture Overview

```
Frontend (Netlify)          Backend (Render)           External Services
React 18 + TypeScript  -->  FastAPI + SQLAlchemy  -->  Neon PostgreSQL
Firebase SDK               Firebase Admin SDK         Firebase Auth
Tailwind CSS + Vite        Keepa API Integration      Keepa API
                           CoWork Agent API           Textbelt SMS / Resend Email
```

### Key Features
- **Firebase Authentication**: Secure login/register with email/password
- **AutoSourcing**: Automated product discovery from Keepa bestsellers with condition signals
- **Daily Review**: Classification engine (STABLE/JACKPOT/REVENANT/FLUKE/REJECT)
- **Condition Signals**: STRONG/MODERATE/WEAK scoring boosting confidence
- **Agent API (CoWork)**: 6 dedicated endpoints with Bearer token auth and rate limiting
- **Notifications**: SMS (Textbelt) + Email (Resend) when stable picks are found
- **Token Control**: Safeguards preventing Keepa API waste
- **Rate Limiting**: Sliding window (30 GET/min, 5 POST/min per token)
- **Mobile-First UX**: Responsive design with touch-friendly UI

---

## Project Structure

```
arbitragevault-bookfinder/
├── backend/                   # FastAPI application
│   ├── app/                   # Core application code
│   │   ├── api/v1/routers/   # 12 routers (~60 routes)
│   │   ├── services/         # Business logic
│   │   │   ├── autosourcing_service.py     # 1037 LOC (post-consolidation)
│   │   │   ├── autosourcing_scoring.py     # ROI + scoring helpers (extracted)
│   │   │   └── notification_service.py     # SMS + Email notifications
│   │   ├── core/             # Auth, DB, Firebase, rate_limiter
│   │   └── models/           # SQLAlchemy models
│   ├── scripts/              # Utility scripts (create_api_key.py, seed scripts)
│   └── tests/                # Test suite (800+ tests)
├── frontend/                  # React 18 application
│   ├── src/
│   │   ├── components/       # UI components + auth
│   │   ├── contexts/         # AuthContext
│   │   ├── pages/            # 4 pages: Dashboard, AutoSourcing, Scheduler, Config
│   │   └── services/         # API client
│   └── tests/                # Playwright E2E tests
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
uv venv && source .venv/bin/activate
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
| 1A-2D | Architecture Refactoring + Daily Review | Jan-Feb 2026 | Complete |
| 3 | Radical Simplification (BookMine-aligned) | Feb 2026 | Complete |
| C | Condition Signals + Pydantic v2 | Mar 2026 | Complete |
| - | 35+ Bugfixes (critical + medium + low) | Mar 2026 | Complete |
| - | Security Audit + Agent API Integration | Mar 2026 | Complete |
| P2 | CoWork Endpoints + Rate Limiting + ROI Consolidation | Mar 2026 | Complete |

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
COWORK_API_TOKEN=<bearer-token-for-cowork-agent>
TEXTBELT_API_KEY=<optional-sms-notifications>
NOTIFICATION_PHONE=<optional-phone-number>
RESEND_API_KEY=<optional-email-notifications>
NOTIFICATION_EMAIL=<optional-email-address>
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
- [Agent Context](./docs/AGENT_CONTEXT.md) - Context for AI agents (CoWork, N8N)
- [Frontend README](./frontend/README.md) - Frontend setup
- [Project Memory](./.claude/compact_master.md) - Full project history

---

**Current Version**: v2.2.0
**Last Updated**: March 26, 2026
**Backend**: https://arbitragevault-backend-v2.onrender.com
**Frontend**: https://arbitragevault.netlify.app
