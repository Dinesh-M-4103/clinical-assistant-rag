import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { API_ORIGIN, API_PREFIX } from '@/lib/env';
import { server } from '@/mocks/server';
import { renderWithProviders } from '@/test/render';
import { HealthBanner } from './HealthBanner';

const healthUrl = `${API_ORIGIN}${API_PREFIX}/health`;

describe('HealthBanner', () => {
  it('stays hidden while the backend is healthy', async () => {
    renderWithProviders(<HealthBanner />);
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('warns with a retry button when the backend is unreachable', async () => {
    server.use(http.get(healthUrl, () => HttpResponse.error()));
    renderWithProviders(<HealthBanner />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/reach the backend/);
    expect(screen.getByRole('button', { name: 'Retry now' })).toBeInTheDocument();
  });

  it('flags a backend that has no language model configured', async () => {
    server.use(
      http.get(healthUrl, () =>
        HttpResponse.json({ status: 'ok', llm_configured: false, version: '0.1.0' }),
      ),
    );
    renderWithProviders(<HealthBanner />);

    expect(await screen.findByRole('status')).toHaveTextContent(/configured/);
  });
});
