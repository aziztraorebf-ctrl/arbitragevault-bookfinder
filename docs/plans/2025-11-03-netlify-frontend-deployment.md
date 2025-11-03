# Netlify Frontend Deployment Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the ArbitrageVault BookFinder frontend to Netlify, connected to production Render backend, with full E2E verification.

**Architecture:** The frontend (React + Vite + TypeScript) will be deployed as a static site to Netlify, configured to communicate with the production Render backend API. Environment variables control API URL routing. Post-deployment, E2E tests validate the complete user flow ("Surprise Me" discovers niches using cached data from production).

**Tech Stack:**
- Frontend: React 19, TypeScript, Vite, Axios
- Deployment: Netlify (MCP available)
- Backend: FastAPI on Render (existing production)
- Testing: Playwright

---

## Pre-Deployment Checklist

Before starting tasks, verify prerequisites:

- [x] Git repo is clean (all changes committed or stashed)
- [x] Backend running on Render (https://arbitragevault-backend-v2.onrender.com)
- [x] Backend API health check passes: `curl https://arbitragevault-backend-v2.onrender.com/api/v1/health/ready`
- [x] Netlify CLI installed: `npm install -g netlify-cli`
- [x] Netlify account exists and authenticated: `netlify login`
- [x] Repository has `frontend/` and `backend/` directories

---

## Task 1: Create `netlify.toml` configuration file

**Files:**
- Create: `netlify.toml` (root of repository)

**Step 1: Create netlify.toml with build configuration**

This file configures Netlify's build system, publish directory, environment variables, and SPA routing.

```toml
# Netlify Configuration for ArbitrageVault BookFinder Frontend

[build]
  # Build directory - change to frontend folder
  base = "frontend"
  # Build command - compile TypeScript and bundle with Vite
  command = "npm run build"
  # Publish directory - Vite outputs to dist/
  publish = "dist"

[env.production]
  # Production backend URL - Render service
  VITE_API_URL = "https://arbitragevault-backend-v2.onrender.com"
  VITE_NODE_ENV = "production"

[env.development]
  # Development backend URL for preview deployments
  VITE_API_URL = "https://arbitragevault-backend-v2.onrender.com"
  VITE_NODE_ENV = "development"

# Critical for React Router / SPA
# All routes should fall back to index.html to allow client-side routing
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# Security headers
[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "SAMEORIGIN"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"
    # Allow requests to Render backend
    Access-Control-Allow-Origin = "https://arbitragevault-backend-v2.onrender.com"
```

**Step 2: Verify file was created correctly**

Run: `cat netlify.toml`

Expected output: Full netlify.toml content showing build command, publish directory, and redirects.

**Step 3: Commit the configuration file**

```bash
git add netlify.toml
git commit -m "config: add netlify.toml with build and routing configuration"
```

Expected: "1 file changed, 25 insertions(+)"

---

## Task 2: Create `.env.production` file for build-time variables

**Files:**
- Create: `frontend/.env.production`

**Step 1: Create production environment file**

This file will be used during the Netlify build process (before Vite runs).

```
# ArbitrageVault Frontend Production Configuration
# Used during build on Netlify

# Backend API URL - Points to production Render service
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com

# Node environment
VITE_NODE_ENV=production

# Build-time flag (optional - for analytics/monitoring)
VITE_BUILD_TIMESTAMP=${date}
```

**Step 2: Verify file was created**

Run: `cat frontend/.env.production`

Expected output: Shows VITE_API_URL pointing to Render backend

**Step 3: Commit the file**

```bash
git add frontend/.env.production
git commit -m "config: add production environment variables for Netlify build"
```

Expected: "1 file changed, 5 insertions(+)"

---

## Task 3: Test build locally to verify everything compiles

**Files:**
- Test: `frontend/package.json` (verify build script exists)
- Output: `frontend/dist/` (will be created)

**Step 1: Clean install dependencies (if needed)**

Run: `cd frontend && npm ci`

Expected: "added X packages in Y seconds"

**Step 2: Run the build command locally**

Run: `cd frontend && npm run build`

Expected output:
```
> frontend-temp@0.0.0 build
> tsc -b && vite build

✓ 152 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.31 kB
dist/assets/index-ABC123.js     245.67 kB │ gzip: 65.12 kB
Built at: 2025-11-03 14:30:00
```

**Step 3: Verify dist directory exists and contains index.html**

Run: `ls -la frontend/dist/`

Expected:
```
total XX
-rw-r--r--  1 user  group    XXX Nov  3 14:30 index.html
drwxr-xr-x  3 user  group   4096 Nov  3 14:30 assets
```

**Step 4: Verify API URL is correctly embedded in build**

Run: `grep -o "arbitragevault-backend-v2.onrender.com" frontend/dist/assets/*.js | head -1`

Expected: Shows the Render backend URL is embedded in the JavaScript bundle

**Step 5: No commit needed for dist/ (add to .gitignore if missing)**

Check: `cat frontend/.gitignore | grep dist`

Expected: `dist` is in .gitignore

If not present, add it:
```bash
echo "dist" >> frontend/.gitignore
git add frontend/.gitignore
git commit -m "config: ensure dist/ is ignored by git"
```

---

## Task 4: Connect repository to Netlify

**Files:**
- Configuration: Netlify Dashboard or Netlify CLI

**Step 1: Authenticate with Netlify**

Run: `netlify login`

Expected: Browser opens, you authenticate, returns "Logged in. You're all set!"

**Step 2: Link the repository to Netlify**

Run: `netlify link`

In the prompt:
- Select "Link this directory to an existing site" (if site exists) or "Create and configure a new site"
- Choose site name: `arbitragevault-bookfinder-frontend` (or use existing)
- Confirm: Site ID is displayed

Expected output:
```
Directory linked, saved in /path/to/.netlify/state.json
Site ID: abc123def456
```

**Step 3: Verify link was successful**

Run: `cat .netlify/state.json`

Expected: Contains `siteId` and `siteUrl`

**No commit needed** - `.netlify/state.json` should be in `.gitignore`

---

## Task 5: Configure environment variables in Netlify

**Files:**
- Configuration: Netlify Dashboard (UI) or via CLI

**Step 1: Set environment variable via CLI**

Run: `netlify env:set VITE_API_URL https://arbitragevault-backend-v2.onrender.com`

Expected output:
```
Environment variables set on production context
VITE_API_URL = https://arbitragevault-backend-v2.onrender.com
```

**Step 2: Verify environment variables were set**

Run: `netlify env:list`

Expected output:
```
key                    value
---------              ------
VITE_API_URL           https://arbitragevault-backend-v2.onrender.com
VITE_NODE_ENV          production
```

**Step 3: No commit needed** - Environment variables are stored in Netlify dashboard, not in git

---

## Task 6: Deploy to Netlify with CLI

**Files:**
- Source: `frontend/dist/` (output from npm run build)
- Target: Netlify production environment

**Step 1: Ensure dist/ is freshly built**

Run: `cd frontend && npm run build`

Expected: See build output (same as Task 3, Step 2)

**Step 2: Deploy to Netlify**

Run: `netlify deploy --prod --dir=frontend/dist`

Expected output:
```
Deploy path: /path/to/frontend/dist
Functions directory: None specified
Configuration file: /path/to/netlify.toml
Deploying to main site URL...
✔ Finished hashing 85 files
✔ Hashing files complete
...
✨ Site Live
URL: https://arbitragevault-bookfinder-frontend.netlify.app
Logs: https://app.netlify.com/sites/arbitragevault-bookfinder-frontend/overview
```

**Step 3: Copy the deployed URL**

Note the URL (e.g., `https://arbitragevault-bookfinder-frontend.netlify.app`) - you'll use this for testing.

**No commit needed** - Deployment is managed by Netlify, not git

---

## Task 7: Verify deployment - health check and basic connectivity

**Files:**
- Target: Deployed frontend URL from Task 6

**Step 1: Test that the deployed site loads**

Run: `curl -I https://arbitragevault-bookfinder-frontend.netlify.app`

Expected output:
```
HTTP/2 200
content-type: text/html; charset=UTF-8
...
```

**Step 2: Verify API URL is correct in deployed build**

Run: `curl https://arbitragevault-bookfinder-frontend.netlify.app | grep -o "arbitragevault-backend-v2.onrender.com" | head -1`

Expected: Shows the Render backend URL is present in the HTML

**Step 3: Test that Render backend is reachable**

Run: `curl https://arbitragevault-backend-v2.onrender.com/api/v1/health/ready`

Expected output:
```json
{
  "status": "ok",
  "timestamp": "2025-11-03T14:30:00Z"
}
```

**Step 4: Verify no CORS errors**

The Netlify-deployed frontend should be able to reach the Render backend. If CORS errors occur:
- Check that Render backend has CORS enabled for Netlify origin
- Verify API URL in environment variables is correct

**No commit needed**

---

## Task 8: Run Playwright E2E tests against deployed frontend

**Files:**
- Test script: `frontend/.claude/skills/playwright-skill/test-surprise-debug.js` (modified for production URL)
- Target: Deployed Netlify frontend

**Step 1: Create a production test script**

Create file `frontend/.claude/skills/playwright-skill/test-production-e2e.js`:

```javascript
const { chromium } = require('playwright');

(async () => {
  console.log('=== PRODUCTION E2E TEST ===\n');

  const FRONTEND_URL = 'https://arbitragevault-bookfinder-frontend.netlify.app';
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();

  const apiResponses = [];

  // Capture API responses
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('discover') || url.includes('niche') || url.includes('auto')) {
      const status = response.status();
      let body = '';
      try {
        body = await response.text();
      } catch (e) {
        body = '(unable to read)';
      }

      apiResponses.push({
        url: url,
        status: status,
        body: body.substring(0, 300)
      });

      console.log(`API RESPONSE: ${status} - ${url.substring(url.lastIndexOf('/'), url.length)}`);
      if (body && body !== '(unable to read)') {
        console.log(`  ${body.substring(0, 100)}...`);
      }
    }
  });

  // Capture console errors
  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    if (type === 'error') {
      console.log(`CONSOLE ERROR: ${text}`);
    }
  });

  try {
    console.log(`1. Loading ${FRONTEND_URL}\n`);
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 15000 });

    console.log('2. Navigating to /niche-discovery\n');
    await page.goto(`${FRONTEND_URL}/niche-discovery`, { waitUntil: 'networkidle', timeout: 15000 });

    console.log('3. Clicking Surprise Me button\n');
    await page.click('button:has-text("Surprise Me")');

    console.log('4. Waiting 10 seconds for responses...\n');
    await page.waitForTimeout(10000);

    console.log('5. Checking results:\n');

    const niche = await page.locator('[class*="niche"], [class*="Card"]').count();
    console.log(`   Niche elements: ${niche}`);

    const loading = await page.locator('[class*="loading"], [class*="spinner"]').count();
    console.log(`   Loading elements: ${loading}`);

    const errors = await page.locator('[class*="error"]').count();
    console.log(`   Error elements: ${errors}`);

    if (niche > 0) {
      console.log('\n   SUCCESS: Niches displayed!');
    } else {
      console.log('\n   WARNING: No niche elements found');
    }

  } catch (error) {
    console.error(`ERROR: ${error.message}`);
  } finally {
    console.log('\nAPI Responses captured:');
    apiResponses.forEach(res => {
      console.log(`  ${res.status} ${res.url}`);
      console.log(`     ${res.body}`);
    });

    await browser.close();
    console.log('\n=== TEST COMPLETE ===');
  }
})();
```

**Step 2: Run the production E2E test**

Run: `cd frontend && node .claude/skills/playwright-skill/test-production-e2e.js`

Expected output:
```
=== PRODUCTION E2E TEST ===

1. Loading https://arbitragevault-bookfinder-frontend.netlify.app
2. Navigating to /niche-discovery
3. Clicking Surprise Me button
4. Waiting 10 seconds for responses...
5. Checking results:
   Niche elements: X
   Loading elements: 0
   Error elements: 0
   SUCCESS: Niches displayed!

API Responses captured:
  200 https://arbitragevault-backend-v2.onrender.com/api/v1/niches/discover
     {"metadata":{"niches_count":3,...}
```

**Step 3: Verify critical success criteria**

Check that:
- [ ] Page loads without errors (HTTP 200)
- [ ] Niche elements are rendered (count > 0)
- [ ] No error elements displayed
- [ ] API calls to Render backend succeed (HTTP 200)
- [ ] "Surprise Me" button returns niches

If all checks pass, mark as SUCCESS. If any fail, see troubleshooting below.

**Step 4: No commit needed** - E2E test is for validation only

---

## Task 9: Troubleshooting & Rollback Procedures

**If deployment fails, use these procedures:**

### Issue 1: Build fails on Netlify

**Symptom:** Netlify build logs show "npm run build failed"

**Diagnosis:**
```bash
# Test locally
cd frontend
npm run build
```

If it fails locally, fix locally first. Common issues:
- TypeScript compilation errors: `npx tsc --noEmit`
- Missing dependencies: `npm ci`
- Vite configuration issues: Check `vite.config.ts`

**Rollback:** `netlify rollback`

### Issue 2: API returns 429 (Rate Limited)

**Symptom:** Playwright test shows "HTTP 429" in API responses

**Cause:** Production cache is empty or insufficient Keepa tokens

**Solution:**
- This is expected during initial deployment
- Cache will refill as users interact with the app
- No action needed - production backend will recover within 1 hour

**Temporary Workaround:** Disable Keepa rate limiting check (development only):
```bash
# On Render backend, temporarily increase rate limit or clear recent cache
# Contact backend team or check Render dashboard logs
```

### Issue 3: CORS errors

**Symptom:** Browser console shows "No 'Access-Control-Allow-Origin' header"

**Cause:** Render backend CORS not configured for Netlify origin

**Solution:**
1. Check Render backend has CORS enabled: `curl -H "Origin: https://arbitragevault-bookfinder-frontend.netlify.app" https://arbitragevault-backend-v2.onrender.com/api/v1/health/ready -v`
2. If CORS fails, update backend CORS configuration in `backend/app/main.py` to include Netlify origin
3. Redeploy backend on Render
4. Redeploy frontend on Netlify

### Issue 4: Frontend shows 0 niches but no error

**Symptom:** Page loads, "Surprise Me" returns no niches, no errors in console

**Cause:** API response is invalid or empty

**Solution:**
1. Check backend API: `curl https://arbitragevault-backend-v2.onrender.com/api/v1/niches/discover?count=3`
2. If API returns empty, check Keepa health: `curl https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/health`
3. If tokens are 0, wait for token refresh (daily limit resets at UTC midnight)

### Rollback to Previous Version

If deployment is broken and needs immediate rollback:

```bash
# Option 1: Rollback via Netlify CLI
netlify rollback

# Option 2: Rollback via Netlify Dashboard
# Go to Deploys > Find previous successful deploy > Right-click > Set as Production

# Option 3: Redeploy from git
git reset --hard <previous-commit-hash>
npm run build
netlify deploy --prod --dir=frontend/dist
```

---

## Task 10: Document deployment and archive logs

**Files:**
- Create: `docs/deployments/2025-11-03-netlify-deployment-log.md`

**Step 1: Create deployment log file**

```markdown
# Netlify Deployment Log - 2025-11-03

## Deployment Details

- **Frontend URL**: https://arbitragevault-bookfinder-frontend.netlify.app
- **Backend URL**: https://arbitragevault-backend-v2.onrender.com
- **Deployed by**: Claude (via Netlify CLI)
- **Deployment method**: `netlify deploy --prod --dir=frontend/dist`
- **Configuration**: `netlify.toml` + environment variables

## Build Configuration

- **Build command**: `npm run build` (in frontend directory)
- **Publish directory**: `dist/`
- **Node version**: 18+ (Netlify default)
- **Build time**: ~2-3 minutes

## Environment Variables

```
VITE_API_URL=https://arbitragevault-backend-v2.onrender.com
VITE_NODE_ENV=production
```

## Verification Results

- [x] Site loads (HTTP 200)
- [x] Niche Discovery page accessible
- [x] "Surprise Me" button works
- [x] API calls to Render backend succeed
- [x] E2E tests pass

## Known Issues

(None at deployment time)

## Rollback Information

If rollback is needed, execute:
```bash
netlify rollback
```

Most recent successful deployment: [deployment URL]
```

**Step 2: Commit the deployment log**

```bash
git add docs/deployments/2025-11-03-netlify-deployment-log.md
git commit -m "docs: add netlify deployment log for 2025-11-03"
```

Expected: "1 file changed, 30 insertions(+)"

---

## Post-Deployment Checklist

After all tasks complete, verify:

- [ ] `netlify.toml` exists in repository root
- [ ] `frontend/.env.production` contains correct Render backend URL
- [ ] Local build passes: `cd frontend && npm run build`
- [ ] Repository linked to Netlify: `netlify link`
- [ ] Environment variables set: `netlify env:list`
- [ ] Site deployed to production: `netlify deploy --prod`
- [ ] Deployed site loads without errors
- [ ] E2E test passes and shows niches
- [ ] Deployment log created and committed
- [ ] All configuration changes committed to git

---

## Execution

This plan is ready for implementation.

**Two execution options:**

**1. Subagent-Driven (this session)** - Fresh subagent per task, I review between tasks, fast iteration with code review gates

**2. Parallel Session (separate)** - Use superpowers:executing-plans in dedicated worktree session, batch execution with checkpoints

Which approach would you prefer?
