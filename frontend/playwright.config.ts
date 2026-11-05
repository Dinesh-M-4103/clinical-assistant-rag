import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

// Browsers live inside the repo (gitignored) rather than in a global cache.
process.env.PLAYWRIGHT_BROWSERS_PATH ??= fileURLToPath(new URL('./.playwright', import.meta.url));

const PORT = 5174;

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  reporter: 'list',
  workers: 2,
  use: { baseURL: `http://localhost:${PORT}`, trace: 'retain-on-failure' },
  webServer: {
    // Runs the app against the in-browser MSW mocks, so no backend is needed.
    command: `npm run dev:mock -- --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: true,
    timeout: 60_000,
  },
  projects: [
    {
      name: 'e2e',
      testMatch: /(app|a11y).spec.ts/,
      fullyParallel: true,
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
  ],
});
