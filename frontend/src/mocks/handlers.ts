import { bypass, delay, http, HttpResponse } from 'msw';
import { patientCreateSchema, type Report } from '@/api/schemas';
import { API_ORIGIN, API_PREFIX, MAX_UPLOAD_MB } from '@/lib/env';
import { buildResponse, pickScript } from './answers';
import { db, mockConfig, syncReportCount } from './db';
import { sseResponse } from './sseResponse';

const url = (path: string) => `${API_ORIGIN}${API_PREFIX}${path}`;

function apiError(status: number, code: string, message: string) {
  return HttpResponse.json({ error: { code, message } }, { status });
}

const notFound = (what: string) => apiError(404, 'not_found', `${what} not found.`);

const findPatient = (uhid: string) => db.patients.find((patient) => patient.uhid === uhid);
const reportsOf = (uhid: string) => db.reports.filter((report) => report.uhid === uhid);

export const handlers = [
  http.get(url('/health'), () =>
    HttpResponse.json({
      status: 'ok',
      llm_configured: true,
      embedding_model: 'BAAI/bge-small-en-v1.5',
      reranker_model: 'cross-encoder/ms-marco-MiniLM-L-6-v2',
      version: '0.1.0',
    }),
  ),

  http.get(url('/patients'), () => HttpResponse.json(db.patients)),

  http.post(url('/patients'), async ({ request }) => {
    const parsed = patientCreateSchema.safeParse(await request.json());
    if (!parsed.success) return apiError(422, 'validation_error', 'Invalid patient details.');
    if (findPatient(parsed.data.uhid)) {
      return apiError(409, 'patient_exists', 'A patient with this UHID already exists.');
    }
    const patient = {
      ...parsed.data,
      summary: parsed.data.summary ?? null,
      report_count: 0,
      created_at: new Date().toISOString(),
    };
    db.patients.unshift(patient);
    return HttpResponse.json(patient, { status: 201 });
  }),

  http.get(url('/patients/:uhid'), ({ params }) => {
    const patient = findPatient(String(params.uhid));
    return patient ? HttpResponse.json(patient) : notFound('Patient');
  }),

  http.delete(url('/patients/:uhid'), ({ params }) => {
    const uhid = String(params.uhid);
    if (!findPatient(uhid)) return notFound('Patient');
    db.patients = db.patients.filter((patient) => patient.uhid !== uhid);
    db.reports = db.reports.filter((report) => report.uhid !== uhid);
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(url('/patients/:uhid/reports'), ({ params }) => {
    const uhid = String(params.uhid);
    return findPatient(uhid) ? HttpResponse.json(reportsOf(uhid)) : notFound('Patient');
  }),

  http.post(url('/patients/:uhid/reports'), async ({ params, request }) => {
    const uhid = String(params.uhid);
    if (!findPatient(uhid)) return notFound('Patient');

    const form = await request.formData();
    const file = form.get('file');
    if (!(file instanceof Blob))
      return apiError(400, 'validation_error', 'A PDF file is required.');
    if (file.type !== 'application/pdf') {
      return apiError(415, 'unsupported_media_type', 'Only PDF files are accepted.');
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      return apiError(413, 'file_too_large', `Files are limited to ${MAX_UPLOAD_MB} MB.`);
    }

    await delay(mockConfig.uploadDelayMs);
    const id = crypto.randomUUID();
    const report: Report = {
      report_id: id,
      uhid,
      name: String(form.get('name') ?? 'Untitled report'),
      category: form.get('category') as Report['category'],
      notes: (form.get('notes') as string | null) ?? null,
      original_filename: file instanceof File ? file.name : 'report.pdf',
      page_count: 3,
      chunk_count: 8,
      size_bytes: file.size,
      uploaded_at: new Date().toISOString(),
      file_url: `${API_PREFIX}/patients/${uhid}/reports/${id}/file`,
    };
    db.reports.unshift(report);
    syncReportCount(uhid);
    return HttpResponse.json(report, { status: 201 });
  }),

  http.delete(url('/patients/:uhid/reports/:reportId'), ({ params }) => {
    const before = db.reports.length;
    db.reports = db.reports.filter((report) => report.report_id !== params.reportId);
    if (db.reports.length === before) return notFound('Report');
    syncReportCount(String(params.uhid));
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(url('/patients/:uhid/reports/:reportId/file'), async ({ params }) => {
    if (!db.reports.some((report) => report.report_id === params.reportId))
      return notFound('Report');
    const pdf = await fetch(bypass('/mock/sample-report.pdf'));
    return new HttpResponse(await pdf.arrayBuffer(), {
      headers: { 'Content-Type': 'application/pdf' },
    });
  }),

  http.post(url('/patients/:uhid/chat/stream'), async ({ params, request }) => {
    const uhid = String(params.uhid);
    if (!findPatient(uhid)) return notFound('Patient');
    const { question } = (await request.json()) as { question: string };

    const reports = reportsOf(uhid);
    const script = pickScript(question, reports.length > 0);
    return sseResponse(buildResponse(script, question, reports), mockConfig.streamDelayMs);
  }),
];
