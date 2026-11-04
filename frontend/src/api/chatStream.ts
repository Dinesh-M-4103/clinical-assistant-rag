import { z } from 'zod';
import { ApiError, send } from './client';
import { API_PREFIX } from '@/lib/env';
import { parseSse, type SseMessage } from './sse';
import {
  chatResponseSchema,
  citationSchema,
  type ChatRequest,
  type ChatResponse,
  type Citation,
} from './schemas';

export type ChatStreamEvent =
  | { type: 'citations'; citations: Citation[] }
  | { type: 'token'; text: string }
  | { type: 'done'; response: ChatResponse }
  | { type: 'error'; code: string; message: string };

const tokenSchema = z.object({ text: z.string() });
const errorSchema = z.object({ code: z.string(), message: z.string() });

const decoders: Record<string, (payload: unknown) => ChatStreamEvent> = {
  citations: (payload) => ({
    type: 'citations',
    citations: z.array(citationSchema).parse(payload),
  }),
  token: (payload) => ({ type: 'token', text: tokenSchema.parse(payload).text }),
  done: (payload) => ({ type: 'done', response: chatResponseSchema.parse(payload) }),
  error: (payload) => ({ type: 'error', ...errorSchema.parse(payload) }),
};

/** Validates one SSE message; events the UI does not use (such as the optional `meta`) are skipped. */
function decode(message: SseMessage): ChatStreamEvent | null {
  const decoder = decoders[message.event];
  if (!decoder) return null;
  try {
    return decoder(JSON.parse(message.data));
  } catch {
    throw new ApiError(502, 'invalid_response', 'The answer stream was malformed.');
  }
}

/** Streams a chat answer as typed events. Aborting `signal` ends the stream with an `AbortError`. */
export async function* streamChat(
  uhid: string,
  request: ChatRequest,
  signal: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
  const response = await send(`${API_PREFIX}/patients/${encodeURIComponent(uhid)}/chat/stream`, {
    method: 'POST',
    json: request,
    accept: 'text/event-stream',
    signal,
  });
  if (!response.body) {
    throw new ApiError(502, 'invalid_response', 'The server sent an empty stream.');
  }

  for await (const message of parseSse(response.body)) {
    const event = decode(message);
    if (event) yield event;
  }
}
