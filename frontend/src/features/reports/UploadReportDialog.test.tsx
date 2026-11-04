import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { Report } from '@/api/schemas';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { renderWithProviders } from '@/test/render';
import { UploadReportDialog } from './UploadReportDialog';

const uploaded: Report = {
  report_id: 'r-1',
  uhid: 'MG25001',
  name: 'Cbc report',
  category: 'lab',
  notes: null,
  original_filename: 'cbc_report.pdf',
  page_count: 2,
  chunk_count: 5,
  size_bytes: 10,
  uploaded_at: '2026-11-01T10:00:00Z',
  file_url: '/api/v1/patients/MG25001/reports/r-1/file',
};

const pdf = () => new File(['%PDF-1.4'], 'cbc_report.pdf', { type: 'application/pdf' });
const fileInput = () => screen.getByLabelText('PDF file');

beforeEach(() => {
  useWorkspace.setState({ uploadOpen: true });
});

describe('UploadReportDialog', () => {
  it('requires a file and a name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UploadReportDialog uhid="MG25001" />);

    await user.click(screen.getByRole('button', { name: 'Upload report' }));

    expect(await screen.findByText('Choose a PDF file')).toBeInTheDocument();
    expect(screen.getByText('Give the report a name')).toBeInTheDocument();
  });

  it('rejects non-PDF files', async () => {
    const user = userEvent.setup({ applyAccept: false });
    renderWithProviders(<UploadReportDialog uhid="MG25001" />);

    await user.upload(fileInput(), new File(['hello'], 'notes.txt', { type: 'text/plain' }));
    await user.click(screen.getByRole('button', { name: 'Upload report' }));

    expect(await screen.findByText('Only PDF files are supported')).toBeInTheDocument();
  });

  it('prefills the name from the file, uploads and closes', async () => {
    const upload = vi.spyOn(api, 'uploadReport').mockResolvedValue(uploaded);
    const user = userEvent.setup();
    renderWithProviders(<UploadReportDialog uhid="MG25001" />);

    await user.upload(fileInput(), pdf());
    expect(screen.getByLabelText('Report name')).toHaveValue('cbc report');
    await user.selectOptions(screen.getByLabelText('Category'), 'imaging');
    await user.click(screen.getByRole('button', { name: 'Upload report' }));

    await waitFor(() => expect(useWorkspace.getState().uploadOpen).toBe(false));
    expect(upload).toHaveBeenCalledWith(
      'MG25001',
      expect.objectContaining({ name: 'cbc report', category: 'imaging', notes: undefined }),
    );
  });

  it('shows the server error and stays open when the upload fails', async () => {
    vi.spyOn(api, 'uploadReport').mockRejectedValue(
      new ApiError(400, 'no_extractable_text', 'This PDF has no extractable text.'),
    );
    const user = userEvent.setup();
    renderWithProviders(<UploadReportDialog uhid="MG25001" />);

    await user.upload(fileInput(), pdf());
    await user.click(screen.getByRole('button', { name: 'Upload report' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('This PDF has no extractable text.');
    expect(useWorkspace.getState().uploadOpen).toBe(true);
  });
});
