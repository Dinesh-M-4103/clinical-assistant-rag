import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import type { Patient } from '@/api/schemas';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { renderWithProviders } from '@/test/render';
import { ChatPanel } from './ChatPanel';

const patient: Patient = {
  uhid: 'MG25001',
  name: 'Asha Verma',
  age: 54,
  gender: 'female',
  summary: null,
  report_count: 3,
  created_at: '2026-10-20T08:00:00Z',
};

const input = () => screen.getByLabelText('Ask a question about this patient');

describe('ChatPanel', () => {
  it('offers suggested questions and the verification disclaimer when empty', () => {
    renderWithProviders(<ChatPanel patient={patient} />);
    expect(screen.getByRole('heading', { name: /Ask about Asha.s records/ })).toBeInTheDocument();
    expect(
      screen.getAllByRole('button', { name: /HbA1c|diagnoses|medications|reference range/ }),
    ).toHaveLength(4);
    expect(screen.getByText(/verify before clinical use/i)).toBeInTheDocument();
  });

  it('streams an answer, renders markdown and turns [C1] into a citation chip that opens the PDF', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatPanel patient={patient} />);

    await user.type(input(), 'What is the latest HbA1c?{Enter}');

    expect(await screen.findByRole('table', {}, { timeout: 8000 })).toBeInTheDocument();
    const chip = await screen.findByRole('button', { name: /citation C1/ });
    expect(chip).toHaveTextContent('C1');
    expect(input()).toHaveValue('');

    await user.click(chip);
    expect(useWorkspace.getState().pdf).toMatchObject({
      page: 1,
      reportName: 'HbA1c & Lipid Panel',
    });
  }, 20_000);

  it('keeps Shift+Enter for new lines instead of sending', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatPanel patient={patient} />);

    await user.type(input(), 'line one{Shift>}{Enter}{/Shift}line two');
    expect(input()).toHaveValue('line one\nline two');
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
  });

  it('disables the composer until the patient has reports', () => {
    renderWithProviders(<ChatPanel patient={{ ...patient, report_count: 0 }} />);
    expect(input()).toBeDisabled();
    expect(screen.getByRole('heading', { name: 'Upload a report to begin' })).toBeInTheDocument();
  });

  it('shows the evidence note for answers that could not be grounded', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatPanel patient={patient} />);

    await user.type(input(), 'What is the weather today?{Enter}');

    await waitFor(() =>
      expect(screen.getByText('Not enough evidence in the uploaded records')).toBeInTheDocument(),
    );
  });
});
