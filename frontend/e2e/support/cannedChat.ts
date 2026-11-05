import { readFileSync } from 'node:fs';
import type { Page } from '@playwright/test';

interface CannedCitation {
  id: string;
  report_name: string;
  category: string;
  page: number;
  section: string | null;
  text: string;
  score: number;
}

interface CannedAnswer {
  answer: string;
  citations: CannedCitation[];
  trace: Record<string, unknown>;
}

interface ReportRef {
  report_id: string;
  name: string;
}

const ABNORMAL_LABS: CannedAnswer = JSON.parse(
  readFileSync(new URL('./abnormal-labs.json', import.meta.url), 'utf8'),
);

function sse(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

/** Splits the answer into small token events, like the real stream does. */
function tokenEvents(answer: string): string {
  const words = answer.match(/\S+\s*/g) ?? [];
  return words.map((text) => sse('token', { text })).join('');
}

/**
 * Replaces the chat stream with a recorded answer about abnormal labs, pointing its citations at
 * the REAL reports of `uhid` (matched by name) so the PDF viewer still loads the real files. This
 * lets screenshots cover rich answers without spending any LLM quota.
 */
export async function installCannedChat(
  page: Page,
  apiUrl: string,
  uhid = 'MG25001',
): Promise<void> {
  const reports: ReportRef[] = await (
    await fetch(`${apiUrl}/api/v1/patients/${uhid}/reports`)
  ).json();
  const idByName = new Map(reports.map((report) => [report.name, report.report_id]));
  const citations = ABNORMAL_LABS.citations.map(({ report_name, ...rest }) => {
    const report_id = idByName.get(report_name);
    if (!report_id)
      throw new Error(`Report "${report_name}" is missing for ${uhid}; run seed_demo.py`);
    return { ...rest, report_name, report_id };
  });

  await page.route(`**/patients/${uhid}/chat/stream`, (route) =>
    route.fulfill({
      status: 200,
      headers: { 'content-type': 'text/event-stream' },
      body:
        sse('meta', { intent: 'question', rewritten_query: null }) +
        sse(
          'citations',
          citations.map((citation) => ({ ...citation, cited: false })),
        ) +
        tokenEvents(ABNORMAL_LABS.answer) +
        sse('done', {
          answer: ABNORMAL_LABS.answer,
          citations: citations.map((citation) => ({ ...citation, cited: true })),
          trace: ABNORMAL_LABS.trace,
        }),
    }),
  );
}
