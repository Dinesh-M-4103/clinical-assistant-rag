import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { server } from '@/mocks/server';
import { API_ORIGIN, API_PREFIX } from '@/lib/env';
import { ApiError } from './client';
import { api } from './endpoints';

const url = (path: string) => `${API_ORIGIN}${API_PREFIX}${path}`;

describe('api client', () => {
  it('returns schema-validated data', async () => {
    const patients = await api.listPatients();
    expect(patients[0]).toMatchObject({ uhid: 'MG25001', report_count: 3 });
  });

  it('turns the error envelope into an ApiError', async () => {
    const error = await api.getPatient('NOPE').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'not_found', message: 'Patient not found.' });
  });

  it('reports a duplicate patient as a 409', async () => {
    const error = await api
      .createPatient({ uhid: 'MG25001', name: 'Dup', age: 40, gender: 'male' })
      .catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 409, code: 'patient_exists' });
  });

  it('rejects responses that break the contract', async () => {
    server.use(http.get(url('/patients'), () => HttpResponse.json([{ uhid: 'X' }])));
    const error = await api.listPatients().catch((e: unknown) => e);
    expect(error).toMatchObject({ code: 'invalid_response' });
  });

  it('falls back to a generic message when the error body is not the envelope', async () => {
    server.use(http.get(url('/patients'), () => new HttpResponse('boom', { status: 500 })));
    const error = await api.listPatients().catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 500, code: 'http_error' });
  });

  it('flags unreachable servers as network errors', async () => {
    server.use(http.get(url('/patients'), () => HttpResponse.error()));
    const error = await api.listPatients().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).isNetwork).toBe(true);
  });
});
