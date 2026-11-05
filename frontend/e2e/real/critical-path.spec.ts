import { expect, test } from '@playwright/test';
import { API_URL, backendIsUp, deletePatient, pdfPath, watchConsole } from './stack';

/**
 * The whole clinician journey against the real backend. It makes ONE live LLM call, so it is
 * deliberately a single serial test.
 */
const UHID = `E2E${Date.now().toString(36).toUpperCase()}`;

test.beforeAll(async () => {
  test.skip(!(await backendIsUp()), `No backend at ${API_URL}`);
});

test.afterAll(async () => {
  await deletePatient(UHID);
});

test('add patient, upload a PDF, ask, open the cited page, then clean up', async ({ page }) => {
  const problems = watchConsole(page);
  await page.goto('/');

  await page.getByRole('button', { name: 'Add patient' }).first().click();
  await page.getByLabel('Full name').fill('Test Patient');
  await page.getByLabel('UHID').fill(UHID);
  await page.getByLabel('Age').fill('62');
  await page.getByRole('dialog').getByRole('button', { name: 'Add patient' }).click();
  await expect(page).toHaveURL(new RegExp(`/patients/${UHID}$`));
  await expect(page.getByRole('heading', { name: 'Upload a report to begin' })).toBeVisible();

  await page
    .getByRole('button', { name: /^Upload report/ })
    .first()
    .click();
  await page.getByLabel('PDF file').setInputFiles(pdfPath('MG25001', 'lab_report_2026-01-14.pdf'));
  await page.getByLabel('Report name').fill('Lab report Jan 2026');
  await page.getByRole('dialog').getByRole('button', { name: 'Upload report' }).click();
  await expect(page.getByText('Lab report Jan 2026 uploaded and indexed')).toBeVisible({
    timeout: 60_000,
  });

  await page.getByLabel('Ask a question about this patient').fill('What is the eGFR?');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: /Stop generating/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /How it was made/ })).toBeVisible({
    timeout: 60_000,
  });

  const chip = page.locator('button[data-citation]').first();
  await expect(chip).toBeVisible();
  await chip.click();
  const viewer = page.getByRole('dialog');
  await expect(viewer.getByRole('heading', { name: 'Lab report Jan 2026' })).toBeVisible();
  await expect(viewer.locator('canvas')).toBeVisible();
  await expect(viewer.locator('.pdf-highlight').first()).toBeVisible({ timeout: 15_000 });
  await page.keyboard.press('Escape');
  await expect(viewer).toBeHidden();

  await page.getByRole('tab', { name: /Evidence/ }).click();
  await expect(page.getByText('Cited in the answer')).toBeVisible();
  await page.getByRole('tab', { name: 'Trace' }).click();
  await expect(page.getByText('Retrieved candidates')).toBeVisible();

  await page.getByRole('tab', { name: /Reports/ }).click();
  await page.getByRole('button', { name: 'Delete Lab report Jan 2026' }).click();
  await page.getByRole('button', { name: 'Delete report' }).click();
  await expect(page.getByText('No reports yet')).toBeVisible();

  await page.getByRole('button', { name: 'Delete Test Patient' }).click();
  await page.getByRole('button', { name: 'Delete patient' }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: /Test Patient/ })).toHaveCount(0);

  expect(problems).toEqual([]);
});
