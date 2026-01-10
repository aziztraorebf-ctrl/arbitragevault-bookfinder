# ArbitrageVault Frontend

React 18 frontend for the ArbitrageVault BookFinder platform.

## Production

**URL**: https://arbitragevault.netlify.app

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Firebase SDK** for authentication
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
│   │   └── auth/         # Login, Register, PasswordReset
│   ├── contexts/         # AuthContext (Firebase)
│   ├── pages/            # Route pages
│   ├── services/         # API client + Firebase config
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
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

Production uses (Netlify):
```
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

## Features

- **Firebase Authentication**: Login/Register with email/password
- **Dashboard**: Overview of arbitrage opportunities
- **AutoSourcing**: Automated product discovery
- **Niche Discovery**: Category-based opportunity finding
- **Mes Recherches**: Centralized search results (30-day retention)
- **Product Analysis**: Detailed product metrics
- **Mobile-First UX**: Responsive design with touch-friendly UI

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

**Version**: 1.7.0
**Backend API**: https://arbitragevault-backend-v2.onrender.com
**API Docs**: https://arbitragevault-backend-v2.onrender.com/docs
