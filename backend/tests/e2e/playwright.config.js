// Playwright E2E Configuration - Phase 5 Token Control System
// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',

  // Timeout pour tests E2E (API calls peuvent etre lents)
  timeout: 30000,

  // Retry failed tests en CI
  retries: process.env.CI ? 2 : 0,

  // Parallel execution
  workers: process.env.CI ? 1 : undefined,

  // Reporter HTML pour visualiser resultats
  reporter: [
    ['html', { outputFolder: './reports' }],
    ['list']
  ],

  use: {
    // Base URL production
    baseURL: 'https://arbitragevault.netlify.app',

    // Capture screenshots en cas d'echec
    screenshot: 'only-on-failure',

    // Capture videos en cas d'echec
    video: 'retain-on-failure',

    // Trace pour debugging
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
