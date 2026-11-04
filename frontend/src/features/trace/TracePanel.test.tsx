import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { renderWithProviders } from '@/test/render';
import { seedAnswer } from '@/test/seed';
import { TracePanel } from './TracePanel';

describe('TracePanel', () => {
  it('asks for an answer first', () => {
    renderWithProviders(<TracePanel uhid="MG25001" />);
    expect(screen.getByText('No trace yet')).toBeInTheDocument();
  });

  it('shows the query rewrite, stage timings, candidate ranks, models and tokens', () => {
    seedAnswer('MG25001', 'What is the latest HbA1c?');
    renderWithProviders(<TracePanel uhid="MG25001" />);

    expect(screen.getByText('Records question')).toBeInTheDocument();
    expect(screen.getByText('What is the latest HbA1c')).toBeInTheDocument();
    expect(
      screen.getByRole('img', { name: /Rewrite 212 ms, Retrieval 38 ms/ }),
    ).toBeInTheDocument();

    const rows = within(screen.getByRole('table')).getAllByRole('row');
    expect(rows).toHaveLength(6);
    expect(within(rows[1] as HTMLElement).getByText('0.940')).toBeInTheDocument();

    expect(screen.getByText('gemini-2.5-flash')).toBeInTheDocument();
    expect(screen.getByText('1,204 in · 186 out')).toBeInTheDocument();
  });

  it('badges answers that were refused for lack of evidence', () => {
    seedAnswer('MG25001', 'What is the weather?');
    renderWithProviders(<TracePanel uhid="MG25001" />);

    expect(screen.getByText('Insufficient evidence')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
