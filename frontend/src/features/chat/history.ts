import type { ChatTurn } from '@/api/schemas';
import type { ChatMessage } from './types';

/** The server uses at most this many previous turns; sending more would only waste bandwidth. */
export const MAX_HISTORY_TURNS = 10;

/** Turns the model should remember: finished messages only, so failed or stopped answers are not replayed. */
export function buildHistory(messages: readonly ChatMessage[]): ChatTurn[] {
  return messages
    .filter((message) => message.status === 'done' && message.content.length > 0)
    .slice(-MAX_HISTORY_TURNS)
    .map(({ role, content }) => ({ role, content }));
}
