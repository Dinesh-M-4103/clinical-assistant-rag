import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { renderWithProviders } from '@/test/render';
import { seedAnswer } from '@/test/seed';
import { EvidencePanel } from './EvidencePanel';

describe('EvidencePanel', () => {
  it('prompts for a question before any answer exists', () => {
    renderWithProviders(<EvidencePanel uhid="MG25001" />);
    expect(screen.getByText('No evidence yet')).toBeInTheDocument();
  });

  it('separates cited passages from other retrieved ones', () => {
    seedAnswer('MG25001', 'What is the latest HbA1c?');
    renderWithProviders(<EvidencePanel uhid="MG25001" />);

    const cited = screen.getByRole('region', { name: 'Cited passages' });
    const others = screen.getByRole('region', { name: 'Also retrieved' });
    expect(within(cited).getAllByRole('listitem')).toHaveLength(3);
    expect(within(others).getAllByRole('listitem')).toHaveLength(2);
    expect(within(cited).getAllByText('Cited')).toHaveLength(3);
  });

  it('opens the PDF at the passage page with the passage text to highlight', async () => {
    const user = userEvent.setup();
    seedAnswer('MG25001', 'What is the latest HbA1c?');
    renderWithProviders(<EvidencePanel uhid="MG25001" />);

    const [firstOnPageThree] = screen.getAllByRole('button', { name: 'Open PDF at page 3' });
    await user.click(firstOnPageThree as HTMLElement);

    expect(useWorkspace.getState().pdf).toMatchObject({
      page: 3,
      reportId: 'a1b2c3d4-0001',
      highlight: expect.stringContaining('Poor glycaemic control'),
    });
  });

  it('explains when an answer used no passages', () => {
    seedAnswer('MG25001', 'What is the weather?');
    renderWithProviders(<EvidencePanel uhid="MG25001" />);
    expect(screen.getByText('No passages were retrieved')).toBeInTheDocument();
  });
});
