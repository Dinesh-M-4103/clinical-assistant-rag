import '@fontsource-variable/inter';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from '@/app/App';
import { Providers } from '@/app/Providers';
import '@/styles/index.css';

async function enableMocks(): Promise<void> {
  if (import.meta.env.VITE_USE_MOCKS !== 'true') return;
  const { worker } = await import('@/mocks/browser');
  await worker.start({ onUnhandledFrame: 'bypass', quiet: true });
}

const root = document.getElementById('root');
if (!root) throw new Error('Missing #root element');

void enableMocks().then(() => {
  createRoot(root).render(
    <StrictMode>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Providers>
          <App />
        </Providers>
      </BrowserRouter>
    </StrictMode>,
  );
});
