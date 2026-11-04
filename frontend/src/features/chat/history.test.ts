import { describe, expect, it } from 'vitest';
import { buildHistory, MAX_HISTORY_TURNS } from './history';
import type { ChatMessage, MessageStatus } from './types';

function message(
  index: number,
  status: MessageStatus = 'done',
  content = `m${index}`,
): ChatMessage {
  return {
    id: String(index),
    role: index % 2 === 0 ? 'user' : 'assistant',
    content,
    status,
    citations: [],
    trace: null,
    error: null,
  };
}

describe('buildHistory', () => {
  it('keeps role and content only', () => {
    expect(buildHistory([message(0), message(1)])).toEqual([
      { role: 'user', content: 'm0' },
      { role: 'assistant', content: 'm1' },
    ]);
  });

  it('drops failed, stopped, streaming and empty messages', () => {
    const history = buildHistory([
      message(0),
      message(1, 'error', ''),
      message(2, 'stopped'),
      message(3, 'streaming'),
      message(4, 'done', ''),
    ]);
    expect(history.map((turn) => turn.content)).toEqual(['m0']);
  });

  it('sends only the most recent turns', () => {
    const many = Array.from({ length: MAX_HISTORY_TURNS + 4 }, (_, i) => message(i));
    const history = buildHistory(many);
    expect(history).toHaveLength(MAX_HISTORY_TURNS);
    expect(history[0]?.content).toBe('m4');
  });
});
