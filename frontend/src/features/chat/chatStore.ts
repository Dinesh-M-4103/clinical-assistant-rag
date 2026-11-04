import { create } from 'zustand';
import type { ChatResponse, Citation } from '@/api/schemas';
import type { ChatMessage } from './types';

interface Session {
  messages: ChatMessage[];
  /** The assistant message whose evidence and trace the inspector shows. */
  activeId: string | null;
}

interface ChatState {
  /** Conversations keyed by UHID. Kept in memory only: patient data is never persisted client-side. */
  sessions: Record<string, Session>;
  startTurn: (uhid: string, question: string) => string;
  restartAnswer: (uhid: string, assistantId: string) => void;
  appendToken: (uhid: string, id: string, text: string) => void;
  setCitations: (uhid: string, id: string, citations: Citation[]) => void;
  complete: (uhid: string, id: string, response: ChatResponse) => void;
  fail: (uhid: string, id: string, error: string) => void;
  stop: (uhid: string, id: string) => void;
  setActive: (uhid: string, id: string) => void;
  clear: (uhid: string) => void;
}

const EMPTY_SESSION: Session = { messages: [], activeId: null };

export const selectSession = (uhid: string) => (state: ChatState) =>
  state.sessions[uhid] ?? EMPTY_SESSION;

let nextId = 0;
const newId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${nextId++}`;

function blankAssistant(): ChatMessage {
  return {
    id: newId('a'),
    role: 'assistant',
    content: '',
    status: 'streaming',
    citations: [],
    trace: null,
    error: null,
  };
}

export const useChatStore = create<ChatState>((set) => {
  const updateSession = (uhid: string, change: (session: Session) => Session) =>
    set((state) => ({
      sessions: { ...state.sessions, [uhid]: change(state.sessions[uhid] ?? EMPTY_SESSION) },
    }));

  const updateMessage = (uhid: string, id: string, patch: (message: ChatMessage) => ChatMessage) =>
    updateSession(uhid, (session) => ({
      ...session,
      messages: session.messages.map((message) => (message.id === id ? patch(message) : message)),
    }));

  return {
    sessions: {},

    startTurn: (uhid, question) => {
      const assistant = blankAssistant();
      const user: ChatMessage = {
        id: newId('u'),
        role: 'user',
        content: question,
        status: 'done',
        citations: [],
        trace: null,
        error: null,
      };
      updateSession(uhid, (session) => ({
        messages: [...session.messages, user, assistant],
        activeId: assistant.id,
      }));
      return assistant.id;
    },

    restartAnswer: (uhid, assistantId) =>
      updateSession(uhid, (session) => ({
        activeId: assistantId,
        messages: session.messages.map((message) =>
          message.id === assistantId ? { ...blankAssistant(), id: assistantId } : message,
        ),
      })),

    appendToken: (uhid, id, text) =>
      updateMessage(uhid, id, (message) => ({ ...message, content: message.content + text })),

    setCitations: (uhid, id, citations) =>
      updateMessage(uhid, id, (message) => ({ ...message, citations })),

    complete: (uhid, id, response) =>
      updateMessage(uhid, id, (message) => ({
        ...message,
        content: response.answer,
        citations: response.citations,
        trace: response.trace,
        status: 'done',
      })),

    fail: (uhid, id, error) =>
      updateMessage(uhid, id, (message) => ({ ...message, status: 'error', error })),

    stop: (uhid, id) => updateMessage(uhid, id, (message) => ({ ...message, status: 'stopped' })),

    setActive: (uhid, id) => updateSession(uhid, (session) => ({ ...session, activeId: id })),

    clear: (uhid) => updateSession(uhid, () => EMPTY_SESSION),
  };
});
