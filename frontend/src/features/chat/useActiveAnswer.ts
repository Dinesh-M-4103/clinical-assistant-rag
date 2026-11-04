import { selectSession, useChatStore } from './chatStore';
import type { ChatMessage } from './types';

export interface ActiveAnswer {
  message: ChatMessage;
  question: string;
}

/** The answer the inspector describes: the one the user picked, else the newest assistant message. */
export function useActiveAnswer(uhid: string): ActiveAnswer | null {
  const { messages, activeId } = useChatStore(selectSession(uhid));
  const index = messages.findIndex((message) => message.id === activeId);
  const fallback = messages.length - 1;
  const answerIndex = index >= 0 ? index : fallback;
  const message = messages[answerIndex];
  if (message?.role !== 'assistant') return null;
  return { message, question: messages[answerIndex - 1]?.content ?? '' };
}
