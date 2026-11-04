import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { renderWithProviders } from '@/test/render';
import { AddPatientDialog } from './AddPatientDialog';

beforeEach(() => {
  useWorkspace.setState({ addPatientOpen: true });
});

async function fill(user: ReturnType<typeof userEvent.setup>, uhid: string) {
  await user.type(screen.getByLabelText('Full name'), 'Meera Iyer');
  await user.type(screen.getByLabelText('UHID'), uhid);
  await user.type(screen.getByLabelText('Age'), '41');
}

describe('AddPatientDialog', () => {
  it('validates required fields before submitting', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AddPatientDialog />);

    await user.click(screen.getByRole('button', { name: 'Add patient' }));

    expect(await screen.findByText('Enter the patient name')).toBeInTheDocument();
    expect(screen.getByText(/Use 3–32 letters/)).toBeInTheDocument();
    expect(screen.getByText('Enter an age between 0 and 130')).toBeInTheDocument();
  });

  it('rejects UHIDs with unsupported characters', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AddPatientDialog />);

    await fill(user, 'bad id!');
    await user.click(screen.getByRole('button', { name: 'Add patient' }));

    expect(await screen.findByText(/Use 3–32 letters/)).toBeInTheDocument();
  });

  it('shows a duplicate UHID error inline and keeps the dialog open', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AddPatientDialog />);

    await fill(user, 'MG25001');
    await user.click(screen.getByRole('button', { name: 'Add patient' }));

    expect(await screen.findByText('A patient with this UHID already exists')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('creates the patient and closes the dialog', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AddPatientDialog />);

    await fill(user, 'MG25099');
    await user.click(screen.getByRole('button', { name: 'Add patient' }));

    await waitFor(() => expect(useWorkspace.getState().addPatientOpen).toBe(false));
    expect(await screen.findByText('Meera Iyer added')).toBeInTheDocument();
  });
});
