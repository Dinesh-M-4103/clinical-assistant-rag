import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import type { Page } from '@playwright/test';

export const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';
export const SYNTHETIC_PDFS = new URL('../../../data/synthetic/pdfs/', import.meta.url);

export async function backendIsUp(): Promise<boolean> {
  try {
    return (await fetch(`${API_URL}/api/v1/health`)).ok;
  } catch {
    return false;
  }
}

export function pdfPath(uhid: string, filename: string): string {
  return fileURLToPath(new URL(`${uhid}/${filename}`, SYNTHETIC_PDFS));
}

/** Creates a patient through the API so a test can start from a known state. */
export async function createPatient(uhid: string, name: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/patients`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ uhid, name, age: 40, gender: 'female' }),
  });
  if (!response.ok) throw new Error(`Could not create ${uhid}: ${response.status}`);
}

/** Uploads a PDF through the API; `name` lets a test choose an awkward report name. */
export async function uploadReport(uhid: string, file: string, name: string): Promise<void> {
  const form = new FormData();
  form.set('file', new Blob([readFileSync(file)], { type: 'application/pdf' }), 'report.pdf');
  form.set('name', name);
  form.set('category', 'lab');
  const response = await fetch(`${API_URL}/api/v1/patients/${uhid}/reports`, {
    method: 'POST',
    body: form,
  });
  if (!response.ok) throw new Error(`Could not upload to ${uhid}: ${response.status}`);
}

export async function deletePatient(uhid: string): Promise<void> {
  await fetch(`${API_URL}/api/v1/patients/${uhid}`, { method: 'DELETE' });
}

/** Fails a test if the page logs a console error/warning or throws, so regressions surface early. */
export function watchConsole(page: Page): string[] {
  const problems: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' || message.type() === 'warning') problems.push(message.text());
  });
  page.on('response', (r) => {
    if (r.status() >= 400) problems.push(`${r.status()} ${r.request().method()} ${r.url()}`);
  });
  page.on('pageerror', (error) => problems.push(error.message));
  return problems;
}
