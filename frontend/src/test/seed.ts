import { buildResponse, pickScript } from '@/mocks/answers';
import { db } from '@/mocks/db';
import { useChatStore } from '@/features/chat/chatStore';

/** Puts a finished answer into a patient's chat session, as if it had just streamed in. */
export function seedAnswer(uhid: string, question: string): void {
  const reports = db.reports.filter((report) => report.uhid === uhid);
  const chat = useChatStore.getState();
  const assistantId = chat.startTurn(uhid, question);
  const script = pickScript(question, reports.length > 0);
  chat.complete(uhid, assistantId, buildResponse(script, question, reports));
}
