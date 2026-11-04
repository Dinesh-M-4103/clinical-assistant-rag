import { expect, test, type Page } from '@playwright/test';

/** Fails a test if the page logs a console error/warning or throws, so regressions surface early. */
function watchConsole(page: Page): string[] {
  const problems: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' || message.type() === 'warning') problems.push(message.text());
  });
  page.on('pageerror', (error) => problems.push(error.message));
  return problems;
}

async function ask(page: Page, question: string) {
  await page.getByLabel('Ask a question about this patient').fill(question);
  await page.keyboard.press('Enter');
}

test('asks a question, opens a citation in the PDF viewer and closes it with Esc', async ({
  page,
}) => {
  const problems = watchConsole(page);
  await page.goto('/patients/MG25001');

  await ask(page, 'What is the latest HbA1c?');
  await expect(page.getByRole('button', { name: /Stop generating/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /How it was made/ })).toBeVisible({
    timeout: 15_000,
  });

  await page.locator('button[data-citation="C1"]').first().click();
  const viewer = page.getByRole('dialog');
  await expect(viewer.getByRole('heading', { name: 'HbA1c & Lipid Panel' })).toBeVisible();
  await expect(viewer.locator('canvas')).toBeVisible();
  await expect(viewer.locator('.pdf-highlight').first()).toBeVisible();

  await page.keyboard.press('ArrowRight');
  await expect(viewer.getByLabel('Page number')).toHaveValue('2');

  await page.keyboard.press('Escape');
  await expect(viewer).toBeHidden();
  expect(problems).toEqual([]);
});

test('stopping a stream keeps the partial answer and offers regeneration', async ({ page }) => {
  await page.goto('/patients/MG25001');
  await ask(page, 'Summarise the key diagnoses');

  await page.getByRole('button', { name: 'Stop generating' }).click();
  await expect(page.getByText('Stopped', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Regenerate' })).toBeVisible();
});

test('adds a patient from the modal and lands on their page', async ({ page }) => {
  const problems = watchConsole(page);
  await page.goto('/');

  await page.getByRole('button', { name: 'Add patient' }).first().click();
  await page.getByLabel('Full name').fill('Meera Iyer');
  await page.getByLabel('UHID').fill('MG25050');
  await page.getByLabel('Age').fill('41');
  await page.getByRole('dialog').getByRole('button', { name: 'Add patient' }).click();

  await expect(page).toHaveURL(/\/patients\/MG25050$/);
  await expect(page.getByRole('heading', { name: 'Meera Iyer' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Upload a report to begin' })).toBeVisible();
  expect(problems).toEqual([]);
});

test('deep links and refresh keep the selected patient', async ({ page }) => {
  await page.goto('/patients/MG25002');
  await expect(page.getByRole('heading', { name: 'Rohan Mehta' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Rohan Mehta' })).toBeVisible();
});

test('shows a friendly state for unknown patients', async ({ page }) => {
  await page.goto('/patients/DOESNOTEXIST');
  await expect(page.getByRole('heading', { name: 'Patient not found' })).toBeVisible();
});

test('deleting a patient asks for confirmation first', async ({ page }) => {
  await page.goto('/patients/MG25003');
  await page.getByRole('button', { name: 'Delete Priya Nair' }).click();
  await expect(page.getByRole('alertdialog')).toBeVisible();
  await page.getByRole('button', { name: 'Delete patient' }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: /Priya Nair/ })).toHaveCount(0);
});

test('uploads a report with progress feedback', async ({ page }) => {
  await page.goto('/patients/MG25003');
  await page.getByRole('button', { name: 'Upload report' }).first().click();
  await page.getByLabel('PDF file').setInputFiles('public/mock/sample-report.pdf');
  await page.getByRole('dialog').getByRole('button', { name: 'Upload report' }).click();
  await expect(page.getByText('Uploading and indexing…')).toBeVisible();
  await expect(page.getByText('sample report uploaded and indexed')).toBeVisible({
    timeout: 10_000,
  });
});

test('never scrolls horizontally on a 320px phone', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto('/patients/MG25001');
  await ask(page, 'Which lab values are outside the reference range?');
  await expect(page.getByRole('button', { name: /How it was made/ })).toBeVisible({
    timeout: 15_000,
  });

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test('phone controls meet the 44px touch target size', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/patients/MG25001');
  await ask(page, 'List current medications with doses');
  await expect(page.getByRole('button', { name: /How it was made/ })).toBeVisible({
    timeout: 15_000,
  });

  const tooSmall = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea')]
      // Inline citation chips sit inside running text, where WCAG exempts small targets.
      .filter((element) => !element.hasAttribute('data-citation') && element.offsetParent !== null)
      .map((element) => ({
        label: element.getAttribute('aria-label') ?? element.textContent?.trim(),
        box: element.getBoundingClientRect(),
      }))
      .filter(({ box }) => box.width > 1 && (box.height < 43.5 || box.width < 43.5))
      .map(({ label, box }) => `${label} ${Math.round(box.width)}x${Math.round(box.height)}`),
  );
  expect(tooSmall).toEqual([]);
});
