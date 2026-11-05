import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

// Browsers live inside the repo (gitignored) rather than in a global cache.
process.env.PLAYWRIGHT_BROWSERS_PATH ??= fileURLToPath(new URL('./.playwright', import.meta.url));

/**
 * Runs against a live stack: start the backend (`uvicorn`, seeded with scripts/seed_demo.py) and
 * `npm run dev`, or point E2E_BASE_URL / E2E_API_URL at another pair. Nothing is mocked, except
 * the screenshots spec, which replays a recorded chat answer to avoid spending LLM quota.
 */
export default defineConfig({
  testDir: './e2e/real',
  outputDir: './test-results',
  reporter: 'list',
  workers: 1,
  timeout: 120_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 800 },
  },
  projects: [
    { name: 'critical-path', testMatch: /critical-path\.spec\.ts/ },
    { name: 'screenshots', testMatch: /screenshots\.spec\.ts/ },
  ],
});
