import { expect, test, type Page } from '@playwright/test';

/**
 * Captures the key screens at four viewport sizes in both themes into test-results/screenshots.
 * One streamed answer per (viewport, theme) keeps the run short.
 */
const VIEWPORTS = [
  { width: 375, height: 812 },
  { width: 768, height: 1024 },
  { width: 1280, height: 800 },
  { width: 1920, height: 1080 },
] as const;
const THEMES = ['light', 'dark'] as const;
type Tab = 'Evidence' | 'Reports' | 'Trace';

const OUT_DIR = 'test-results/screenshots';

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
      const shot = async (scene: string) => {
        await page.waitForTimeout(350); // let enter animations finish
        await page.screenshot({ path: `${OUT_DIR}/${scene}__${width}x${height}__${theme}.png` });
      };

      await page.setViewportSize(viewport);
      await page.addInitScript(
        (value) => localStorage.setItem('clinical-assistant:theme', value),
        theme,
      );
      await page.goto('/patients/MG25001');
      await expect(page.getByRole('heading', { name: /Ask about Asha/ })).toBeVisible();
      await shot('01-empty-state');

      if (width < 1280) await page.getByRole('button', { name: 'Open patient list' }).click();
      await page.getByRole('button', { name: 'Add patient' }).click();
      await page.getByRole('dialog').getByRole('button', { name: 'Add patient' }).click();
      await expect(page.getByText('Enter the patient name')).toBeVisible();
      await shot('08-add-patient');
      await page.keyboard.press('Escape');

      await page.getByLabel('Ask a question about this patient').fill('What is the latest HbA1c?');
      await page.keyboard.press('Enter');
      await expect(page.getByRole('button', { name: 'How it was made' })).toBeVisible({
        timeout: 20_000,
      });
      await shot('02-chat-citations');

      await page.locator('button[data-citation="C1"]').first().click();
      await expect(page.locator('.pdf-highlight').first()).toBeVisible({ timeout: 15_000 });
      await shot('06-pdf-viewer');
      await page.keyboard.press('Escape');

      await showInspector(page, width, 'Evidence');
      await expect(page.getByText('Also retrieved')).toBeVisible();
      await shot('03-evidence');

      await showInspector(page, width, 'Trace');
      await expect(page.getByText('Retrieved candidates')).toBeVisible();
      await shot('07-trace');

      await showInspector(page, width, 'Reports');
      await expect(page.getByText('Medication Prescription')).toBeVisible();
      await shot('04-reports');

      await page
        .getByRole('button', { name: /^Upload/ })
        .first()
        .click();
      await page.getByLabel('PDF file').setInputFiles('public/mock/sample-report.pdf');
      await expect(page.getByLabel('Report name')).toHaveValue('sample report');
      await shot('05-upload-dialog');
      await page.keyboard.press('Escape');
      await backToChat(page, width);
    });
  }
}
