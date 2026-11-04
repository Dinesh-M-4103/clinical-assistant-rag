import type { Patient, Report } from '@/api/schemas';

/** Tunable pacing so tests run instantly while the demo feels like a real stream. */
export const mockConfig = { streamDelayMs: 24, uploadDelayMs: 1600 };

const PDF_PAGES = 3;

function report(uhid: string, id: string, overrides: Partial<Report>): Report {
  return {
    report_id: id,
    uhid,
    name: 'Report',
    category: 'lab',
    notes: null,
    original_filename: 'report.pdf',
    page_count: PDF_PAGES,
    chunk_count: 9,
    size_bytes: 48_213,
    uploaded_at: '2026-10-21T09:30:00Z',
    file_url: `/api/v1/patients/${uhid}/reports/${id}/file`,
    ...overrides,
  };
}

function seedPatients(): Patient[] {
  return [
    {
      uhid: 'MG25001',
      name: 'Asha Verma',
      age: 54,
      gender: 'female',
      summary:
        'Type 2 diabetes (8 yrs) and hypertension. Quarterly review of glycaemic control and lipids.',
      report_count: 3,
      created_at: '2026-10-20T08:00:00Z',
    },
    {
      uhid: 'MG25002',
      name: 'Rohan Mehta',
      age: 67,
      gender: 'male',
      summary: 'Chronic kidney disease stage 3; on ACE inhibitor.',
      report_count: 2,
      created_at: '2026-10-12T11:15:00Z',
    },
    {
      uhid: 'MG25003',
      name: 'Priya Nair',
      age: 31,
      gender: 'female',
      summary: null,
      report_count: 0,
      created_at: '2026-10-02T15:40:00Z',
    },
  ];
}

function seedReports(): Report[] {
  return [
    report('MG25001', 'a1b2c3d4-0001', {
      name: 'HbA1c & Lipid Panel',
      category: 'lab',
      notes: 'Fasting sample, Sept 2026 review',
      original_filename: 'lab_panel_sep2026.pdf',
      uploaded_at: '2026-10-21T09:30:00Z',
    }),
    report('MG25001', 'a1b2c3d4-0002', {
      name: 'Discharge Summary',
      category: 'discharge',
      original_filename: 'discharge_summary.pdf',
      chunk_count: 14,
      uploaded_at: '2026-10-20T16:05:00Z',
    }),
    report('MG25001', 'a1b2c3d4-0003', {
      name: 'Medication Prescription',
      category: 'prescription',
      original_filename: 'prescription_oct.pdf',
      page_count: 1,
      chunk_count: 4,
      size_bytes: 21_904,
      uploaded_at: '2026-10-20T14:12:00Z',
    }),
    report('MG25002', 'b1b2c3d4-0001', {
      name: 'Renal Function Tests',
      category: 'lab',
      original_filename: 'renal_function.pdf',
      uploaded_at: '2026-10-15T10:00:00Z',
    }),
    report('MG25002', 'b1b2c3d4-0002', {
      name: 'Nephrology Consultation',
      category: 'consultation',
      original_filename: 'nephrology_consult.pdf',
      page_count: 2,
      uploaded_at: '2026-10-13T09:00:00Z',
    }),
  ];
}

export const db = { patients: seedPatients(), reports: seedReports() };

/** Restores the seed data; tests call this between cases. */
export function resetDb(): void {
  db.patients = seedPatients();
  db.reports = seedReports();
}

export function syncReportCount(uhid: string): void {
  const patient = db.patients.find((item) => item.uhid === uhid);
  if (patient) patient.report_count = db.reports.filter((item) => item.uhid === uhid).length;
}
