import { describe, expect, it } from 'vitest';
import { parseSse, type SseMessage } from './sse';

function streamOf(...chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
      controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<SseMessage[]> {
  const messages: SseMessage[] = [];
  for await (const message of parseSse(stream)) messages.push(message);
  return messages;
}

describe('parseSse', () => {
  it('parses named events with JSON data', async () => {
    const messages = await collect(streamOf('event: token\ndata: {"text":"Hi"}\n\n'));
    expect(messages).toEqual([{ event: 'token', data: '{"text":"Hi"}' }]);
  });

  it('reassembles events split across chunks, even mid-line', async () => {
    const messages = await collect(
      streamOf('event: tok', 'en\ndata: {"te', 'xt":"a"}\n', '\nevent: done\ndata: {}\n\n'),
    );
    expect(messages.map((m) => m.event)).toEqual(['token', 'done']);
    expect(messages[0]?.data).toBe('{"text":"a"}');
  });

  it('handles CRLF line endings, including a CR/LF pair split between chunks', async () => {
    const messages = await collect(streamOf('event: token\r\ndata: 1\r', '\n\r\n'));
    expect(messages).toEqual([{ event: 'token', data: '1' }]);
  });

  it('joins multi-line data, ignores comments and defaults the event name', async () => {
    const messages = await collect(streamOf(': keep-alive\n\ndata: one\ndata: two\n\n'));
    expect(messages).toEqual([{ event: 'message', data: 'one\ntwo' }]);
  });

  it('flushes a final event that lacks the trailing blank line', async () => {
    const messages = await collect(streamOf('event: done\ndata: {"ok":true}'));
    expect(messages).toEqual([{ event: 'done', data: '{"ok":true}' }]);
  });

  it('decodes multi-byte characters split across chunks', async () => {
    const bytes = new TextEncoder().encode('data: héllo\n\n');
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes.slice(0, 8));
        controller.enqueue(bytes.slice(8));
        controller.close();
      },
    });
    expect(await collect(stream)).toEqual([{ event: 'message', data: 'héllo' }]);
  });
});
