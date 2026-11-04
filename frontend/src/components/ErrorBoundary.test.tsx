import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { ErrorBoundary } from './ErrorBoundary';

function Bomb({ explode }: { explode: boolean }) {
  if (explode) throw new Error('boom');
  return <p>All good</p>;
}

function Harness() {
  const [explode, setExplode] = useState(true);
  return (
    <>
      <button onClick={() => setExplode(false)}>fix</button>
      <ErrorBoundary>
        <Bomb explode={explode} />
      </ErrorBoundary>
    </>
  );
}

describe('ErrorBoundary', () => {
  it('shows a fallback and recovers once the failing child is fixed', async () => {
    // React rethrows render errors to window; swallow them so the test output stays clean.
    const swallow = (event: ErrorEvent) => event.preventDefault();
    window.addEventListener('error', swallow);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const user = userEvent.setup();
    render(<Harness />);

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'fix' }));
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(screen.getByText('All good')).toBeInTheDocument();
    window.removeEventListener('error', swallow);
  });
});
