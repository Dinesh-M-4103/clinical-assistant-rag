import { streamChat } from '@/api/chatStream';
import { describeError } from '@/lib/errors';
import { useChatStore } from './chatStore';
import { buildHistory } from './history';

/**
 * Drives one streaming answer per patient. Living outside React means a reply keeps arriving
 * (and lands in the right conversation) even if the clinician switches patients mid-answer.
 */
const inFlight = new Map<string, AbortController>();

export function stopAnswer(uhid: string): void {
  inFlight.get(uhid)?.abort();
}

async function run(uhid: string, assistantId: string, question: string, historyEnd: number) {
  const chat = useChatStore.getState();
  const history = buildHistory(chat.sessions[uhid]?.messages.slice(0, historyEnd) ?? []);
  const controller = new AbortController();
  inFlight.set(uhid, controller);

  try {
    for await (const event of streamChat(uhid, { question, history }, controller.signal)) {
      switch (event.type) {
        case 'citations':
          chat.setCitations(uhid, assistantId, event.citations);
          break;
        case 'token':
          chat.appendToken(uhid, assistantId, event.text);
          break;
        case 'done':
          chat.complete(uhid, assistantId, event.response);
          break;
        case 'error':
          chat.fail(uhid, assistantId, event.message);
          break;
      }
    }
    const message = useChatStore
      .getState()
      .sessions[uhid]?.messages.find((m) => m.id === assistantId);
    if (message?.status === 'streaming')
      chat.fail(uhid, assistantId, 'The answer ended unexpectedly.');
  } catch (error) {
    if (controller.signal.aborted) chat.stop(uhid, assistantId);
    else chat.fail(uhid, assistantId, describeError(error));
  } finally {
    inFlight.delete(uhid);
  }
}

export function sendQuestion(uhid: string, question: string): Promise<void> {
  const chat = useChatStore.getState();
  const priorCount = chat.sessions[uhid]?.messages.length ?? 0;
  const assistantId = chat.startTurn(uhid, question);
  return run(uhid, assistantId, question, priorCount);
}

/** Re-asks the question behind `assistantId`, using only the conversation that preceded it. */
export function retryAnswer(uhid: string, assistantId: string): Promise<void> {
  const chat = useChatStore.getState();
  const messages = chat.sessions[uhid]?.messages ?? [];
  const index = messages.findIndex((message) => message.id === assistantId);
  const question = messages[index - 1];
  if (index < 1 || question?.role !== 'user') return Promise.resolve();
  chat.restartAnswer(uhid, assistantId);
  return run(uhid, assistantId, question.content, index - 1);
}
