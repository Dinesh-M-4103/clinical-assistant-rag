import { HttpResponse } from 'msw';
import type { ChatResponse } from '@/api/schemas';

const encoder = new TextEncoder();
const frame = (event: string, data: unknown) =>
  encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Replays a finished answer as the contract's SSE sequence: meta, citations, tokens, done. */
export function sseResponse(response: ChatResponse, tokenDelayMs: number): Response {
  let cancelled = false;

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const emit = (event: string, data: unknown) => {
        if (!cancelled) controller.enqueue(frame(event, data));
      };
      emit('meta', {
        intent: response.trace.intent,
        rewritten_query: response.trace.rewritten_query,
      });
      await sleep(tokenDelayMs * 8);
      emit(
        'citations',
        response.citations.map((citation) => ({ ...citation, cited: false })),
      );
      for (const text of response.answer.match(/\S+\s*/g) ?? []) {
        if (cancelled) return;
        await sleep(tokenDelayMs);
        emit('token', { text });
      }
      emit('done', response);
      if (!cancelled) controller.close();
    },
    cancel() {
      cancelled = true;
    },
  });

  return new HttpResponse(stream, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
  });
}
