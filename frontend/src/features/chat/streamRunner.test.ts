import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { API_ORIGIN, API_PREFIX } from '@/lib/env';
import { mockConfig } from '@/mocks/db';
import { server } from '@/mocks/server';
import { useChatStore } from './chatStore';
import { retryAnswer, sendQuestion, stopAnswer } from './streamRunner';

const UHID = 'MG25001';
const streamUrl = `${API_ORIGIN}${API_PREFIX}/patients/${UHID}/chat/stream`;
const session = () => useChatStore.getState().sessions[UHID];

describe('streamRunner', () => {
  it('streams an answer into the session and finalises it from the done event', async () => {
    await sendQuestion(UHID, 'What is the latest HbA1c?');

    const [question, answer] = session()?.messages ?? [];
    expect(question).toMatchObject({ role: 'user', content: 'What is the latest HbA1c?' });
    expect(answer?.status).toBe('done');
    expect(answer?.content).toContain('HbA1c is 7.8 %');
    expect(answer?.citations.filter((citation) => citation.cited)).toHaveLength(3);
    expect(answer?.trace?.intent).toBe('question');
  });

  it('sends earlier finished turns as history', async () => {
    await sendQuestion(UHID, 'What is the latest HbA1c?');
    const bodies: unknown[] = [];
    server.use(
      http.post(streamUrl, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ error: { code: 'x', message: 'stop' } }, { status: 500 });
      }),
    );
    await sendQuestion(UHID, 'And the glucose?');

    expect(bodies[0]).toMatchObject({
      question: 'And the glucose?',
      history: [
        { role: 'user', content: 'What is the latest HbA1c?' },
        { role: 'assistant', content: expect.stringContaining('HbA1c is 7.8 %') },
      ],
    });
  });

  it('marks the answer as failed when the server reports a stream error', async () => {
    server.use(
      http.post(
        streamUrl,
        () =>
          new HttpResponse(
            'event: error\ndata: {"code":"llm_unavailable","message":"Model offline"}\n\n',
            {
              headers: { 'Content-Type': 'text/event-stream' },
            },
          ),
      ),
    );
    await sendQuestion(UHID, 'Hello?');
    expect(session()?.messages[1]).toMatchObject({ status: 'error', error: 'Model offline' });
  });

  it('fails with the HTTP error message when the request is rejected', async () => {
    server.use(
      http.post(streamUrl, () =>
        HttpResponse.json(
          { error: { code: 'llm_unavailable', message: 'LLM is down' } },
          { status: 502 },
        ),
      ),
    );
    await sendQuestion(UHID, 'Anything');
    expect(session()?.messages[1]).toMatchObject({ status: 'error', error: 'LLM is down' });
  });

  it('keeps partial text and marks the answer stopped when aborted', async () => {
    mockConfig.streamDelayMs = 15;
    const running = sendQuestion(UHID, 'Summarise the key diagnoses');
    await vi.waitFor(() => expect(session()?.messages[1]?.content.length).toBeGreaterThan(0));
    stopAnswer(UHID);
    await running;

    const answer = session()?.messages[1];
    expect(answer?.status).toBe('stopped');
    expect(answer?.content.length).toBeGreaterThan(0);
  });

  it('retries a failed answer in place using the original question', async () => {
    server.use(
      http.post(
        streamUrl,
        () => HttpResponse.json({ error: { code: 'x', message: 'nope' } }, { status: 500 }),
        {
          once: true,
        },
      ),
    );
    await sendQuestion(UHID, 'What is the latest HbA1c?');
    const failed = session()?.messages[1];
    expect(failed?.status).toBe('error');

    await retryAnswer(UHID, failed?.id ?? '');
    const messages = session()?.messages ?? [];
    expect(messages).toHaveLength(2);
    expect(messages[1]).toMatchObject({ id: failed?.id, status: 'done' });
  });
});
