# ArbitrageVault Frontend

React 18 frontend for the ArbitrageVault BookFinder platform.

## Production

**URL**: https://arbitragevault.netlify.app

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Playwright** for E2E testing

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run E2E tests
npx playwright test
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Route pages
│   ├── services/         # API client
│   ├── hooks/            # Custom React hooks
│   └── types/            # TypeScript types
├── e2e/                   # Playwright E2E tests
├── public/                # Static assets
└── vite.config.ts         # Vite configuration
```

## Environment Variables

Create `.env.local` for local development:
```
VITE_API_URL=http://localhost:8000
```

Production uses:
```
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
```

## Features

- **Dashboard**: Overview of arbitrage opportunities
- **AutoSourcing**: Automated product discovery
- **Niche Discovery**: Category-based opportunity finding
- **Product Analysis**: Detailed product metrics

## Testing

```bash
# Run all E2E tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test file
npx playwright test e2e/autosourcing.spec.ts
```

## Deployment

Deployed automatically via Netlify on push to main branch.

Build settings:
- Build command: `npm run build`
- Publish directory: `dist`

---

**Backend API**: https://arbitragevault-backend-v2.onrender.com
**API Docs**: https://arbitragevault-backend-v2.onrender.com/docs
