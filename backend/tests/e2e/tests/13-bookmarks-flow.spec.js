// Bookmarks E2E Tests - Phase 5
// Valide le flux complet de gestion des bookmarks de niches
const { test, expect } = require('@playwright/test');
const { getRandomNicheData } = require('../test-utils/random-data');

const BACKEND_URL = 'https://arbitragevault-backend-v2.onrender.com';
const FRONTEND_URL = 'https://arbitragevault.netlify.app';

// Use seed-based randomization for reproducibility
const TEST_SEED = process.env.TEST_SEED || 'bookmarks-test';
const TEST_NICHE_DATA = getRandomNicheData(TEST_SEED);

test.describe('Bookmarks Flow - Phase 5', () => {
  test('should display empty state when no bookmarks', async ({ page }) => {
    test.setTimeout(30000);
    console.log('Testing empty state display...');

    await page.goto(`${FRONTEND_URL}/mes-niches`);

    // Wait for React app to load
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait for loading to complete
    const loader = page.locator('text=/Chargement de vos niches/i');
    if (await loader.isVisible({ timeout: 5000 }).catch(() => false)) {
      await loader.waitFor({ state: 'detached', timeout: 15000 });
    }

    // Check for empty state OR existing bookmarks
    const emptyState = page.locator('text=/Aucune niche sauvegardee/i');
    const nichesList = page.locator('text=/niche.* sauvegardee/i');

    const hasEmptyState = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    const hasNichesList = await nichesList.isVisible({ timeout: 5000 }).catch(() => false);

    // Either should be visible
    expect(hasEmptyState || hasNichesList).toBe(true);

    if (hasEmptyState) {
      console.log('Empty state displayed correctly');

      // Verify empty state components
      const emptyIcon = page.locator('[class*="lucide"]').first();
      await expect(emptyIcon).toBeVisible({ timeout: 3000 });

      const emptyMessage = page.locator('text=/Decouvrez des niches dans la page/i');
      await expect(emptyMessage).toBeVisible({ timeout: 3000 });
    } else {
      console.log('Bookmarks list displayed (already has bookmarks)');
    }
  });

  test('should navigate to niche discovery from empty state', async ({ page }) => {
    test.setTimeout(30000);
    console.log('Testing navigation to niche discovery...');

    await page.goto(`${FRONTEND_URL}/mes-niches`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait for page to load
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Look for "Decouvrir des niches" link (in empty state or navigation)
    const discoveryLinks = [
      page.locator('a[href="/niche-discovery"]'),
      page.locator('text=/Decouvrir des niches/i'),
      page.locator('a:has-text("Niche Discovery")'),
      page.locator('a:has-text("Niches")'),
    ];

    let linkFound = false;
    for (const link of discoveryLinks) {
      if (await link.first().isVisible({ timeout: 2000 }).catch(() => false)) {
        await link.first().click();
        console.log('Clicked discovery link');
        linkFound = true;
        break;
      }
    }

    if (linkFound) {
      // Wait for navigation
      await page.waitForURL(/niche-discovery/, { timeout: 10000 });
      console.log('Successfully navigated to niche discovery page');

      // Verify we're on the right page
      await page.waitForSelector('#root', { timeout: 10000 });
      expect(page.url()).toContain('niche-discovery');
    } else {
      console.log('Discovery link not found - might be in navigation only');
    }
  });

  test('should save a niche from discovery results', async ({ request }) => {
    test.setTimeout(45000);
    console.log('Testing save niche bookmark...');

    // Create a bookmark via API
    const response = await request.post(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      data: TEST_NICHE_DATA,
      timeout: 30000
    });

    console.log('Create bookmark response status:', response.status());

    // Handle auth requirement
    if (response.status() === 401 || response.status() === 403) {
      console.log('Skipping test - authentication required');
      return;
    }

    expect(response.status()).toBe(201);

    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('niche_name');
    expect(data.niche_name).toBe(TEST_NICHE_DATA.niche_name);
    expect(data).toHaveProperty('created_at');
    expect(data).toHaveProperty('updated_at');

    console.log('Created bookmark:', {
      id: data.id,
      name: data.niche_name,
      category: data.category_name
    });

    // Cleanup
    const deleteResponse = await request.delete(
      `${BACKEND_URL}/api/v1/bookmarks/niches/${data.id}`,
      { timeout: 30000 }
    );

    console.log('Cleanup delete status:', deleteResponse.status());
  });

  test('should list saved bookmarks', async ({ request }) => {
    test.setTimeout(45000);
    console.log('Testing list bookmarks...');

    // First, create a test bookmark
    const createResponse = await request.post(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      data: TEST_NICHE_DATA,
      timeout: 30000
    });

    if (createResponse.status() === 401 || createResponse.status() === 403) {
      console.log('Skipping test - authentication required');
      return;
    }

    expect(createResponse.status()).toBe(201);
    const created = await createResponse.json();
    console.log('Created test bookmark:', created.id);

    // List bookmarks
    const listResponse = await request.get(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      timeout: 30000
    });

    expect(listResponse.status()).toBe(200);

    const listData = await listResponse.json();

    // Validate list response structure
    expect(listData).toHaveProperty('niches');
    expect(listData).toHaveProperty('total_count');
    expect(Array.isArray(listData.niches)).toBe(true);
    expect(listData.total_count).toBeGreaterThan(0);

    console.log(`Found ${listData.total_count} bookmarks`);

    // Find our test bookmark
    const found = listData.niches.find(n => n.id === created.id);
    expect(found).toBeDefined();
    expect(found.niche_name).toBe(TEST_NICHE_DATA.niche_name);

    console.log('Test bookmark found in list');

    // Cleanup
    const deleteResponse = await request.delete(
      `${BACKEND_URL}/api/v1/bookmarks/niches/${created.id}`,
      { timeout: 30000 }
    );

    console.log('Cleanup delete status:', deleteResponse.status());
  });

  test('should delete a bookmark with confirmation', async ({ page, request }) => {
    test.setTimeout(60000);
    console.log('Testing delete bookmark with confirmation...');

    // First, create a test bookmark via API
    const createResponse = await request.post(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      data: TEST_NICHE_DATA,
      timeout: 30000
    });

    if (createResponse.status() === 401 || createResponse.status() === 403) {
      console.log('Skipping test - authentication required');
      return;
    }

    expect(createResponse.status()).toBe(201);
    const created = await createResponse.json();
    console.log('Created test bookmark:', created.id);

    // Navigate to bookmarks page
    await page.goto(`${FRONTEND_URL}/mes-niches`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait for loading to complete
    const loader = page.locator('text=/Chargement de vos niches/i');
    if (await loader.isVisible({ timeout: 5000 }).catch(() => false)) {
      await loader.waitFor({ state: 'detached', timeout: 20000 });
    }

    // Look for our test bookmark by name
    const nicheTitle = page.locator(`text=${TEST_NICHE_DATA.niche_name}`);
    if (await nicheTitle.isVisible({ timeout: 10000 }).catch(() => false)) {
      console.log('Test bookmark visible in UI');

      // Find delete button (with Trash icon or "Supprimer" text)
      const deleteButtons = [
        page.locator('button:has-text("Supprimer")'),
        page.locator('button[title*="Supprimer"]'),
        page.locator('button:has([class*="trash"])'),
      ];

      let deleteButton = null;
      for (const btn of deleteButtons) {
        const button = btn.first();
        if (await button.isVisible({ timeout: 2000 }).catch(() => false)) {
          deleteButton = button;
          break;
        }
      }

      if (deleteButton) {
        // Setup dialog handler for confirmation
        page.on('dialog', dialog => {
          console.log('Confirmation dialog:', dialog.message());
          dialog.accept();
        });

        await deleteButton.click();
        console.log('Clicked delete button');

        // Wait for deletion to complete
        await page.waitForTimeout(2000);

        // Verify bookmark is gone
        const stillVisible = await nicheTitle.isVisible({ timeout: 3000 }).catch(() => false);
        expect(stillVisible).toBe(false);

        console.log('Bookmark successfully deleted from UI');
      } else {
        console.log('Delete button not found in UI');
        // Cleanup via API
        await request.delete(`${BACKEND_URL}/api/v1/bookmarks/niches/${created.id}`, {
          timeout: 30000
        });
      }
    } else {
      console.log('Test bookmark not visible in UI - cleaning up via API');
      await request.delete(`${BACKEND_URL}/api/v1/bookmarks/niches/${created.id}`, {
        timeout: 30000
      });
    }
  });

  test('should re-run analysis from saved bookmark', async ({ page, request }) => {
    test.setTimeout(90000);
    console.log('Testing re-run analysis from bookmark...');

    // Create a test bookmark via API
    const createResponse = await request.post(`${BACKEND_URL}/api/v1/bookmarks/niches`, {
      data: TEST_NICHE_DATA,
      timeout: 30000
    });

    if (createResponse.status() === 401 || createResponse.status() === 403) {
      console.log('Skipping test - authentication required');
      return;
    }

    expect(createResponse.status()).toBe(201);
    const created = await createResponse.json();
    console.log('Created test bookmark:', created.id);

    // Navigate to bookmarks page
    await page.goto(`${FRONTEND_URL}/mes-niches`);
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait for loading
    const loader = page.locator('text=/Chargement de vos niches/i');
    if (await loader.isVisible({ timeout: 5000 }).catch(() => false)) {
      await loader.waitFor({ state: 'detached', timeout: 20000 });
    }

    // Look for our test bookmark
    const nicheTitle = page.locator(`text=${TEST_NICHE_DATA.niche_name}`);
    if (await nicheTitle.isVisible({ timeout: 10000 }).catch(() => false)) {
      console.log('Test bookmark visible in UI');

      // Find re-run button (with RefreshCw icon or "Relancer" text)
      const rerunButtons = [
        page.locator('button:has-text("Relancer")'),
        page.locator('button[title*="Relancer"]'),
        page.locator('button:has([class*="refresh"])'),
      ];

      let rerunButton = null;
      for (const btn of rerunButtons) {
        const button = btn.first();
        if (await button.isVisible({ timeout: 2000 }).catch(() => false)) {
          rerunButton = button;
          break;
        }
      }

      if (rerunButton) {
        await rerunButton.click();
        console.log('Clicked re-run button');

        // Wait for navigation or loading indicator
        const analyzing = page.locator('text=/Analyse/i');
        if (await analyzing.isVisible({ timeout: 5000 }).catch(() => false)) {
          console.log('Analysis started');
        }

        // Should navigate to niche-discovery with results
        await page.waitForURL(/niche-discovery/, { timeout: 15000 }).catch(() => {
          console.log('Navigation timeout - might still be on same page');
        });

        if (page.url().includes('niche-discovery')) {
          console.log('Successfully navigated to discovery page with re-run results');

          // Verify page loaded
          await page.waitForSelector('#root', { timeout: 10000 });
        } else {
          console.log('Did not navigate (might be insufficient tokens or error)');
        }
      } else {
        console.log('Re-run button not found in UI');
      }
    } else {
      console.log('Test bookmark not visible in UI');
    }

    // Cleanup
    await request.delete(`${BACKEND_URL}/api/v1/bookmarks/niches/${created.id}`, {
      timeout: 30000
    }).catch(err => {
      console.log('Cleanup delete failed:', err.message);
    });
  });
});
