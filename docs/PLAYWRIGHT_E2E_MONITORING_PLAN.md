# Plan Complet Playwright E2E & Monitoring
**Phase 5 - Token Control System Testing & Production Monitoring**

Date: 2025-11-04
Auteur: Claude Code avec Playwright Skill

---

## Contexte

ArbitrageVault BookFinder est déployé sur deux plateformes :
- **Frontend** : Netlify (`https://arbitragevault.netlify.app/`)
- **Backend** : Render (`https://arbitragevault-backend-v2.onrender.com/`)

Le **Token Control System** (Phase 5) est maintenant en production et nécessite :
1. Tests E2E pour valider le flow complet HTTP 429
2. Monitoring automatisé pour détecter pannes/régressions
3. Alertes quand balance tokens Keepa devient critique

---

## Objectifs

### 1. Tests E2E (End-to-End)
Valider que le système Token Control fonctionne correctement en production :
- Niche Discovery bloquée quand tokens insuffisants
- Message utilisateur clair avec balance/required affichés
- Composants `TokenErrorAlert` affichés correctement
- Retry après recharge tokens fonctionne

### 2. Monitoring Production
Détecter problèmes avant les utilisateurs :
- Backend health check (`/api/v1/health/ready`)
- Frontend accessible et React chargé
- Token balance Keepa > CRITICAL_THRESHOLD (20 tokens)
- Temps de réponse endpoints < 5 secondes

### 3. Tests de Régression
Assurer que features existantes fonctionnent toujours :
- Navigation entre pages principales
- Formulaires fonctionnels (Analyse Manuelle, Configuration)
- AutoSourcing job submission

---

## Architecture Tests Playwright

### Structure Projet

```
backend/
  tests/
    e2e/                          # Nouveau dossier pour tests E2E
      playwright.config.ts        # Config Playwright
      fixtures/                   # Test data et helpers
        auth.ts                   # Authentication fixtures
        mock-data.ts              # Mock responses pour tests
      tests/
        01-health-monitoring.spec.ts      # Health checks production
        02-token-control-flow.spec.ts     # HTTP 429 flow E2E
        03-niche-discovery.spec.ts        # Niche Discovery E2E
        04-manual-search.spec.ts          # Manual Search E2E
        05-autosourcing-jobs.spec.ts      # AutoSourcing E2E
        06-navigation-flow.spec.ts        # Navigation entre pages
      reports/                    # Rapports tests HTML
      screenshots/                # Screenshots en cas d'échec
      videos/                     # Vidéos tests (optionnel)
```

### Installation

```bash
cd backend/tests/e2e
npm init -y
npm install --save-dev @playwright/test
npx playwright install chromium
```

---

## Tests Critiques à Implémenter

### Test 1: Health Monitoring (CRITIQUE)

**Fichier** : `01-health-monitoring.spec.ts`

**Objectif** : Vérifier que production est accessible et fonctionnelle

**Tests** :
```typescript
test('Backend /health/ready should return 200', async ({ request }) => {
  const response = await request.get('https://arbitragevault-backend-v2.onrender.com/api/v1/health/ready')
  expect(response.status()).toBe(200)
})

test('Frontend should load and render React app', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/')
  await expect(page.locator('#root')).toBeVisible()
  await expect(page.locator('nav')).toBeVisible() // Navigation présente
})

test('Keepa token balance should be above critical threshold', async ({ request }) => {
  const response = await request.get('https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/health')
  const data = await response.json()

  const CRITICAL_THRESHOLD = 20
  expect(data.tokensLeft).toBeGreaterThan(CRITICAL_THRESHOLD)

  // Warning si proche du seuil
  if (data.tokensLeft < 50) {
    console.warn(`⚠️ Token balance low: ${data.tokensLeft} tokens remaining`)
  }
})
```

**Fréquence** : Toutes les 30 minutes (GitHub Actions scheduled)

---

### Test 2: Token Control Flow (HTTP 429)

**Fichier** : `02-token-control-flow.spec.ts`

**Objectif** : Valider que HTTP 429 est correctement géré par le frontend

**Approche** : Mock l'API backend pour simuler HTTP 429

**Tests** :
```typescript
test('should display TokenErrorAlert when HTTP 429 returned', async ({ page }) => {
  // Intercepter requête Niche Discovery et retourner 429
  await page.route('**/api/v1/niches/discover*', (route) => {
    route.fulfill({
      status: 429,
      headers: {
        'X-Token-Balance': '15',
        'X-Token-Required': '50',
        'Retry-After': '3600'
      },
      body: JSON.stringify({
        detail: 'Insufficient Keepa tokens for action surprise_me. Required: 50, Available: 15, Deficit: 35'
      })
    })
  })

  await page.goto('https://arbitragevault.netlify.app/niche-discovery')

  // Cliquer sur "Surprise Me"
  await page.click('button:has-text("Surprise Me")')

  // Vérifier que TokenErrorAlert s'affiche
  const alert = page.locator('.bg-yellow-50') // TokenErrorAlert
  await expect(alert).toBeVisible()

  // Vérifier contenu du message
  await expect(alert).toContainText('Disponible: 15')
  await expect(alert).toContainText('Requis: 50')
  await expect(alert).toContainText('Manquant: 35')
})

test('should allow retry after token recharge', async ({ page }) => {
  // Premier appel: 429 (tokens insuffisants)
  let callCount = 0
  await page.route('**/api/v1/niches/discover*', (route) => {
    callCount++
    if (callCount === 1) {
      route.fulfill({
        status: 429,
        headers: { 'X-Token-Balance': '15', 'X-Token-Required': '50' },
        body: JSON.stringify({ detail: 'Insufficient tokens' })
      })
    } else {
      // Deuxième appel: succès (tokens rechargés)
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          products: [],
          metadata: {
            mode: 'auto',
            niches: [
              { id: 'test-1', name: 'Tech Books', products_found: 5 }
            ],
            niches_count: 1
          }
        })
      })
    }
  })

  await page.goto('https://arbitragevault.netlify.app/niche-discovery')
  await page.click('button:has-text("Surprise Me")')

  // Vérifier erreur affichée
  await expect(page.locator('.bg-yellow-50')).toBeVisible()

  // Cliquer sur bouton "Réessayer"
  await page.click('button:has-text("Réessayer")')

  // Vérifier que niches s'affichent après retry
  await expect(page.locator('.bg-yellow-50')).not.toBeVisible()
  await expect(page.locator('text=Tech Books')).toBeVisible()
})
```

---

### Test 3: Niche Discovery E2E (Happy Path)

**Fichier** : `03-niche-discovery.spec.ts`

**Objectif** : Valider flow Niche Discovery complet avec tokens suffisants

**Tests** :
```typescript
test('should discover niches successfully when tokens available', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/niche-discovery')

  // Cliquer "Surprise Me"
  await page.click('button:has-text("Surprise Me")')

  // Attendre réponse API (max 10 secondes)
  await page.waitForSelector('[data-testid="niche-card"]', { timeout: 10000 })

  // Vérifier que niches s'affichent
  const nicheCards = page.locator('[data-testid="niche-card"]')
  const count = await nicheCards.count()

  expect(count).toBeGreaterThan(0)
  expect(count).toBeLessThanOrEqual(5) // Max 5 niches

  // Vérifier structure niche card
  const firstNiche = nicheCards.first()
  await expect(firstNiche.locator('.niche-name')).toBeVisible()
  await expect(firstNiche.locator('.niche-metrics')).toBeVisible()
})

test('should allow drilling into niche details', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/niche-discovery')
  await page.click('button:has-text("Surprise Me")')

  // Attendre niches
  await page.waitForSelector('[data-testid="niche-card"]')

  // Cliquer sur première niche
  await page.click('[data-testid="niche-card"] >> nth=0')

  // Vérifier que produits s'affichent
  await page.waitForSelector('[data-testid="product-row"]', { timeout: 10000 })

  const productRows = page.locator('[data-testid="product-row"]')
  const count = await productRows.count()

  expect(count).toBeGreaterThan(0)
})
```

---

### Test 4: Manual Search E2E

**Fichier** : `04-manual-search.spec.ts`

**Objectif** : Valider recherche manuelle produits avec filtres

**Tests** :
```typescript
test('should search products with filters', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/analyse-manuelle')

  // Remplir formulaire recherche
  await page.fill('input[name="bsr_min"]', '10000')
  await page.fill('input[name="bsr_max"]', '50000')
  await page.selectOption('select[name="category"]', { label: 'Books' })

  // Soumettre recherche
  await page.click('button[type="submit"]')

  // Attendre résultats
  await page.waitForSelector('[data-testid="product-table"]', { timeout: 15000 })

  // Vérifier résultats affichés
  const rows = page.locator('tbody tr')
  const count = await rows.count()

  expect(count).toBeGreaterThan(0)

  // Vérifier colonnes présentes
  await expect(page.locator('th:has-text("ASIN")')).toBeVisible()
  await expect(page.locator('th:has-text("ROI")')).toBeVisible()
  await expect(page.locator('th:has-text("Vélocité")')).toBeVisible()
})
```

---

### Test 5: AutoSourcing Job Submission

**Fichier** : `05-autosourcing-jobs.spec.ts`

**Objectif** : Valider soumission job AutoSourcing

**Tests** :
```typescript
test('should submit autosourcing job successfully', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/auto-sourcing')

  // Remplir configuration job
  await page.fill('input[name="profile_name"]', 'Test Job Playwright')
  await page.selectOption('select[name="category"]', { label: 'Books' })
  await page.fill('input[name="min_roi"]', '30')

  // Soumettre job
  await page.click('button:has-text("Lancer la recherche")')

  // Attendre confirmation
  await page.waitForSelector('.success-message', { timeout: 10000 })

  await expect(page.locator('text=Job lancé avec succès')).toBeVisible()
})
```

---

### Test 6: Navigation Flow

**Fichier** : `06-navigation-flow.spec.ts`

**Objectif** : Valider navigation entre pages principales

**Tests** :
```typescript
test('should navigate between main pages', async ({ page }) => {
  await page.goto('https://arbitragevault.netlify.app/')

  // Dashboard → Niche Discovery
  await page.click('nav >> text=Mes Niches')
  await expect(page).toHaveURL(/niche-discovery/)

  // Niche Discovery → AutoSourcing
  await page.click('nav >> text=AutoSourcing')
  await expect(page).toHaveURL(/auto-sourcing/)

  // AutoSourcing → Configuration
  await page.click('nav >> text=Configuration')
  await expect(page).toHaveURL(/configuration/)

  // Configuration → Dashboard
  await page.click('nav >> text=Dashboard')
  await expect(page).toHaveURL(/^https:\/\/arbitragevault\.netlify\.app\/$/)
})
```

---

## Configuration Playwright

**Fichier** : `backend/tests/e2e/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',

  // Timeout pour tests E2E (API calls peuvent être lents)
  timeout: 30000,

  // Retry failed tests en CI
  retries: process.env.CI ? 2 : 0,

  // Parallel execution
  workers: process.env.CI ? 1 : undefined,

  // Reporter HTML pour visualiser résultats
  reporter: [
    ['html', { outputFolder: './reports' }],
    ['list']
  ],

  use: {
    // Base URL production
    baseURL: 'https://arbitragevault.netlify.app',

    // Capture screenshots en cas d'échec
    screenshot: 'only-on-failure',

    // Capture vidéos en cas d'échec
    video: 'retain-on-failure',

    // Trace pour debugging
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],
})
```

---

## Exécution Locale

### Tests individuels
```bash
cd backend/tests/e2e

# Test health monitoring
npx playwright test 01-health-monitoring

# Test Token Control flow
npx playwright test 02-token-control-flow

# Tous les tests
npx playwright test

# Mode headed (voir navigateur)
npx playwright test --headed

# Mode debug
npx playwright test --debug
```

### Visualiser rapports
```bash
npx playwright show-report reports
```

---

## GitHub Actions CI/CD

**Fichier** : `.github/workflows/e2e-tests.yml`

```yaml
name: E2E Tests & Monitoring

on:
  # Run on every push to main
  push:
    branches: [main]

  # Run on PR
  pull_request:
    branches: [main]

  # Scheduled monitoring (every 30 minutes)
  schedule:
    - cron: '*/30 * * * *'

  # Manual trigger
  workflow_dispatch:

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        working-directory: backend/tests/e2e
        run: npm ci

      - name: Install Playwright browsers
        working-directory: backend/tests/e2e
        run: npx playwright install --with-deps chromium

      - name: Run E2E tests
        working-directory: backend/tests/e2e
        run: npx playwright test
        env:
          CI: true

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: backend/tests/e2e/reports/
          retention-days: 30

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-screenshots
          path: backend/tests/e2e/screenshots/
          retention-days: 7

      - name: Notify on failure
        if: failure() && github.event_name == 'schedule'
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: '🚨 Production monitoring tests failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Monitoring Dashboard

### Métriques à Tracker

1. **Test Success Rate** : % tests passants
2. **Token Balance Trend** : Graphique balance tokens dans le temps
3. **Response Time P95** : Temps réponse 95e percentile
4. **Error Rate** : % requêtes échouées (4xx, 5xx)
5. **Test Duration** : Temps exécution suite tests

### Outils Recommandés

- **Playwright HTML Reporter** : Inclus, visualisation rapports
- **GitHub Actions Artifacts** : Stockage rapports + screenshots
- **Sentry** : Déjà configuré pour backend monitoring
- **Slack Notifications** : Alertes en cas d'échec tests scheduled

---

## Prochaines Étapes

### Phase 1: Setup (Cette session)
1. ✅ Créer plan complet
2. ⏳ Installer Playwright dans projet
3. ⏳ Créer Test 1 (Health Monitoring)
4. ⏳ Tester exécution locale

### Phase 2: Tests Critiques (Prochaine session)
1. Implémenter Test 2 (Token Control Flow)
2. Implémenter Test 3 (Niche Discovery E2E)
3. Valider avec vraies URLs production

### Phase 3: Automation (Future)
1. Configurer GitHub Actions workflow
2. Activer scheduled monitoring (30 min)
3. Configurer Slack notifications

---

## Avantages de cette Approche

1. **Tests Production Réels** : Pas de mocks, test environnement réel
2. **Détection Précoce** : Problèmes détectés avant utilisateurs (monitoring 30 min)
3. **Traçabilité** : Screenshots + vidéos + traces pour debug
4. **Zero Maintenance** : Tests auto-cleanup, rapports auto-archivés
5. **Multi-Browser** : Chrome + Firefox + Mobile coverage

---

## Conclusion

Ce plan fournit une **couverture complète E2E + monitoring** pour le Token Control System. Les tests sont prêts à être implémentés avec le **Playwright Skill** dans cette session.

**Prêt à commencer l'implémentation ?** 🚀
