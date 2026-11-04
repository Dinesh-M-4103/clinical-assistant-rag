import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { mockConfig, resetDb } from '@/mocks/db';
import { server } from '@/mocks/server';
import { useChatStore } from '@/features/chat/chatStore';
import { useWorkspace } from '@/features/workspace/workspaceStore';

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }));

beforeEach(() => {
  mockConfig.streamDelayMs = 0;
  mockConfig.uploadDelayMs = 0;
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  resetDb();
  useChatStore.setState({ sessions: {} });
  useWorkspace.setState(useWorkspace.getInitialState());
});

afterAll(() => server.close());

window.matchMedia ??= ((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addEventListener: () => undefined,
  removeEventListener: () => undefined,
  addListener: () => undefined,
  removeListener: () => undefined,
  dispatchEvent: () => false,
})) as typeof window.matchMedia;

window.HTMLElement.prototype.scrollIntoView ??= () => undefined;
window.HTMLElement.prototype.scrollTo ??= () => undefined;
window.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
