import { z } from 'zod';
import { requestBlob, requestJson, requestVoid } from './client';
import { API_PREFIX } from '@/lib/env';
import {
  healthSchema,
  patientSchema,
  reportSchema,
  type Category,
  type PatientCreate,
} from './schemas';

export interface ReportUpload {
  file: File;
  name: string;
  category: Category;
  notes?: string;
}

const patientPath = (uhid: string) => `${API_PREFIX}/patients/${encodeURIComponent(uhid)}`;

export const api = {
  health: () => requestJson(`${API_PREFIX}/health`, healthSchema),

  listPatients: () => requestJson(`${API_PREFIX}/patients`, z.array(patientSchema)),
  getPatient: (uhid: string) => requestJson(patientPath(uhid), patientSchema),
  createPatient: (input: PatientCreate) =>
    requestJson(`${API_PREFIX}/patients`, patientSchema, { method: 'POST', json: input }),
  deletePatient: (uhid: string) => requestVoid(patientPath(uhid), { method: 'DELETE' }),

  listReports: (uhid: string) => requestJson(`${patientPath(uhid)}/reports`, z.array(reportSchema)),
  uploadReport: (uhid: string, { file, name, category, notes }: ReportUpload) => {
    const form = new FormData();
    form.set('file', file);
    form.set('name', name);
    form.set('category', category);
    if (notes) form.set('notes', notes);
    return requestJson(`${patientPath(uhid)}/reports`, reportSchema, { method: 'POST', form });
  },
  deleteReport: (uhid: string, reportId: string) =>
    requestVoid(`${patientPath(uhid)}/reports/${encodeURIComponent(reportId)}`, {
      method: 'DELETE',
    }),
  /** `fileUrl` is the server-relative `file_url` of a report. */
  fetchReportPdf: (fileUrl: string) => requestBlob(fileUrl, { accept: 'application/pdf' }),
};

export function reportFileUrl(uhid: string, reportId: string): string {
  return `${patientPath(uhid)}/reports/${encodeURIComponent(reportId)}/file`;
}
