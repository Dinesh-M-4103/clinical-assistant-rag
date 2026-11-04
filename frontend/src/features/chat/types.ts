import type { Citation, Trace } from '@/api/schemas';

export type MessageStatus = 'streaming' | 'done' | 'stopped' | 'error';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status: MessageStatus;
  citations: Citation[];
  trace: Trace | null;
  error: string | null;
}
