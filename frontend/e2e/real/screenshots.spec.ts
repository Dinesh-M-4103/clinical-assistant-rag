import { expect, test, type Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { installCannedChat } from '../support/cannedChat';
import {
  API_URL,
  backendIsUp,
  createPatient,
  deletePatient,
  pdfPath,
  uploadReport,
  watchConsole,
} from './stack';

/**
 * Captures the key screens of the real app at four viewport sizes in both themes into
 * test-results/screenshots, and copies a curated subset into docs/screenshots. The chat answer is
 * a recorded one (see support/cannedChat.ts) so this never spends LLM quota.
 */
const VIEWPORTS = [
  { width: 375, height: 812 },
  { width: 768, height: 1024 },
  { width: 1280, height: 800 },
  { width: 1920, height: 1080 },
] as const;
const THEMES = ['light', 'dark'] as const;
type Tab = 'Evidence' | 'Reports' | 'Trace';

const MATRIX_DIR = 'test-results/screenshots';
const DOCS_DIR = '../docs/screenshots';

/** scene|width|theme -> file name used in the README. */
const CURATED: Record<string, string> = {
  'chat|1280|light': '01-chat-desktop-light',
  'chat|1280|dark': '02-chat-desktop-dark',
  'pdf|1280|light': '03-pdf-highlight-desktop-light',
  'evidence|1920|light': '04-evidence-wide-light',
  'trace|1280|dark': '05-trace-desktop-dark',
  'reports|1280|light': '06-reports-desktop-light',
  'empty|1280|light': '07-empty-state-desktop-light',
  'chat|768|light': '08-chat-tablet-light',
  'evidence|768|dark': '09-evidence-tablet-dark',
  'chat|375|light': '10-chat-mobile-light',
  'chat|375|dark': '11-chat-mobile-dark',
  'pdf|375|dark': '12-pdf-mobile-dark',
  'reports|375|light': '13-reports-mobile-light',
  'add-patient|1280|light': '14-add-patient-desktop-light',
  'upload|375|dark': '15-upload-mobile-dark',
  'backend-down|1280|light': '16-backend-down-desktop-light',
};

const LONG_NAME =
  'Comprehensive Metabolic Panel With Extended Renal Function And Electrolytes - Outpatient Review';

test.beforeAll(async () => {
  test.skip(!(await backendIsUp()), `No backend at ${API_URL}`);
  mkdirSync(MATRIX_DIR, { recursive: true });
  mkdirSync(DOCS_DIR, { recursive: true });
});

async function showInspector(page: Page, width: number, tab: Tab) {
  if (width >= 1280) {
    await page.getByRole('tab', { name: new RegExp(tab) }).click();
  } else if (width >= 768) {
    if (!(await page.getByRole('tab', { name: new RegExp(tab) }).isVisible())) {
      await page.getByRole('button', { name: 'Open inspector' }).click();
    }
    await page.getByRole('tab', { name: new RegExp(tab) }).click();
  } else if (tab === 'Trace') {
    await page.getByRole('button', { name: 'Evidence' }).click();
    await page.getByRole('button', { name: 'How this answer was made' }).click();
  } else {
    await page
      .getByRole('navigation', { name: 'Workspace sections' })
      .getByRole('button', { name: tab })
      .click();
  }
}

async function backToChat(page: Page, width: number) {
  if (width >= 1280) return;
  if (width >= 768) {
    if (await page.getByRole('button', { name: 'Close inspector' }).isVisible()) {
      await page.getByRole('button', { name: 'Close inspector' }).click();
    }
    return;
  }
  await page
    .getByRole('navigation', { name: 'Workspace sections' })
    .getByRole('button', { name: 'Chat' })
    .click();
}

for (const viewport of VIEWPORTS) {
  for (const theme of THEMES) {
    test(`${viewport.width}x${viewport.height} ${theme}`, async ({ page }) => {
      const { width, height } = viewport;
      const problems = watchConsole(page);
      const shot = async (scene: string) => {
        await page.waitForTimeout(400); // let enter animations finish
        const image = await page.screenshot({
          path: `${MATRIX_DIR}/${scene}__${width}x${height}__${theme}.png`,
        });
        const curated = CURATED[`${scene}|${width}|${theme}`];
        if (curated) writeFileSync(`${DOCS_DIR}/${curated}.png`, image);
      };

      await page.setViewportSize(viewport);
      await page.addInitScript(
        (value) => localStorage.setItem('clinical-assistant:theme', value),
        theme,
      );
      await installCannedChat(page, API_URL);

      await page.goto('/patients/MG25001');
      await expect(page.getByRole('heading', { name: /Ask about Rajesh/ })).toBeVisible();
      // A first click puts Chrome into pointer mode, so later tab clicks show no keyboard focus ring.
      await page.mouse.click(1, 1);
      await shot('empty');

      if (width < 1280) await page.getByRole('button', { name: 'Open patient list' }).click();
      await page.getByRole('button', { name: 'Add patient' }).click();
      await page.getByRole('dialog').getByRole('button', { name: 'Add patient' }).click();
      await expect(page.getByText('Enter the patient name')).toBeVisible();
      await shot('add-patient');
      await page.getByRole('button', { name: 'Cancel' }).click();

      await page
        .getByLabel('Ask a question about this patient')
        .fill('Which lab values are outside the reference range?');
      await page.keyboard.press('Enter');
      await expect(page.getByRole('button', { name: 'How it was made' })).toBeVisible({
        timeout: 20_000,
      });
      await page
        .getByLabel('Your question')
        .evaluate((el) => el.scrollIntoView({ block: 'start' }));
      await shot('chat');

      await page.locator('button[data-citation="C1"]').first().click();
      await expect(page.locator('.pdf-highlight').first()).toBeVisible({ timeout: 15_000 });
      await shot('pdf');
      await page.getByRole('button', { name: 'Close' }).click();

      await showInspector(page, width, 'Evidence');
      await expect(page.getByText('Cited in the answer')).toBeVisible();
      await shot('evidence');

      await showInspector(page, width, 'Trace');
      await expect(page.getByText('Retrieved candidates')).toBeVisible();
      await shot('trace');

      await showInspector(page, width, 'Reports');
      await expect(page.getByText('Endocrinology Consultation - Sep 2025').first()).toBeVisible();
      await shot('reports');

      await page
        .getByRole('button', { name: /^Upload/ })
        .first()
        .click();
      await page
        .getByLabel('PDF file')
        .setInputFiles(pdfPath('MG25001', 'lab_report_2026-01-14.pdf'));
      await expect(page.getByLabel('Report name')).not.toHaveValue('');
      await shot('upload');
      await page.getByRole('button', { name: 'Cancel' }).click();
      await backToChat(page, width);

      expect(problems).toEqual([]);

      await page.route('**/api/v1/health', (route) => route.abort());
      await page.reload();
      await expect(page.getByRole('alert')).toContainText('reach the backend');
      await shot('backend-down');
    });
  }
}

test('long report names truncate and nothing overflows horizontally', async ({ page }) => {
  const uhid = `E2ELONG${Date.now().toString(36).toUpperCase()}`;
  await createPatient(uhid, 'Bartholomew Montgomery-Featherstonehaugh');
  await uploadReport(uhid, pdfPath('MG25001', 'lab_report_2026-01-14.pdf'), LONG_NAME);
  try {
    for (const viewport of [
      { width: 320, height: 640 },
      { width: 375, height: 812 },
      { width: 1280, height: 800 },
    ]) {
      await page.setViewportSize(viewport);
      await page.goto(`/patients/${uhid}`);
      await showInspector(page, viewport.width, 'Reports');
      await expect(page.getByText(LONG_NAME).first()).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow, `${viewport.width}px`).toBeLessThanOrEqual(0);
      await page.screenshot({
        path: `${MATRIX_DIR}/long-names__${viewport.width}x${viewport.height}__light.png`,
      });
    }
  } finally {
    await deletePatient(uhid);
  }
});

test('an answer with a wide table stays inside the bubble on a 320px phone', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await installCannedChat(page, API_URL);
  await page.goto('/patients/MG25001');
  await page.getByLabel('Ask a question about this patient').fill('Which values are abnormal?');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: 'How it was made' })).toBeVisible();

  const overflow = await page.evaluate(() => ({
    page: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    table: (() => {
      const wrap = document.querySelector('.table-wrap');
      return wrap ? wrap.scrollWidth - wrap.clientWidth : -1;
    })(),
  }));
  expect(overflow.page).toBeLessThanOrEqual(0);
  expect(overflow.table).toBeGreaterThan(0);
  await page.screenshot({ path: `${MATRIX_DIR}/table-bubble__320x640__light.png` });
});

test('a patient without reports shows a clear empty state', async ({ page }) => {
  const uhid = `E2EEMPTY${Date.now().toString(36).toUpperCase()}`;
  await createPatient(uhid, 'Anika Rao');
  try {
    await page.goto(`/patients/${uhid}`);
    await expect(page.getByRole('heading', { name: 'Upload a report to begin' })).toBeVisible();
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${MATRIX_DIR}/no-reports__1280x800__light.png` });
  } finally {
    await deletePatient(uhid);
  }
});
