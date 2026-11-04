import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

const THEMES = ['light', 'dark'] as const;

async function violations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  return results.violations.map((violation) => ({
    rule: violation.id,
    targets: violation.nodes.map((node) => node.target.join(' ')).slice(0, 5),
  }));
}

for (const theme of THEMES) {
  test.describe(`${theme} theme`, () => {
    test.beforeEach(async ({ page }) => {
      await page.addInitScript(
        (value) => localStorage.setItem('clinical-assistant:theme', value),
        theme,
      );
    });

    test('patient workspace with an answer has no WCAG A/AA violations', async ({ page }) => {
      await page.goto('/patients/MG25001');
      await expect(page.getByRole('heading', { name: /Ask about Asha/ })).toBeVisible();
      expect(await violations(page)).toEqual([]);

      await page.getByLabel('Ask a question about this patient').fill('What is the latest HbA1c?');
      await page.keyboard.press('Enter');
      await expect(page.getByRole('button', { name: 'How it was made' })).toBeVisible({
        timeout: 15_000,
      });
      await page.waitForTimeout(300);
      expect(await violations(page)).toEqual([]);

      await page.getByRole('tab', { name: /Trace/ }).click();
      await page.waitForTimeout(300);
      expect(await violations(page)).toEqual([]);

      await page.getByRole('tab', { name: /Reports/ }).click();
      await page.waitForTimeout(300);
      expect(await violations(page)).toEqual([]);
    });

    test('dialogs have no WCAG A/AA violations', async ({ page }) => {
      await page.goto('/patients/MG25001');
      await page.getByRole('button', { name: 'Upload report' }).first().click();
      await page.waitForTimeout(300);
      expect(await violations(page)).toEqual([]);
      await page.keyboard.press('Escape');

      await page.getByRole('button', { name: 'Add patient' }).click();
      await page.getByRole('dialog').getByRole('button', { name: 'Add patient' }).click();
      await page.waitForTimeout(400);
      expect(await violations(page)).toEqual([]);
    });
  });
}
