import { describe, expect, it } from 'vitest';
import type { Patient } from '@/api/schemas';
import { matchesQuery } from './search';

const patient: Patient = {
  uhid: 'MG25001',
  name: 'Asha Verma',
  age: 54,
  gender: 'female',
  summary: null,
  report_count: 3,
  created_at: '2026-10-20T08:00:00Z',
};

describe('matchesQuery', () => {
  it('matches name and UHID case-insensitively', () => {
    expect(matchesQuery(patient, 'verma')).toBe(true);
    expect(matchesQuery(patient, 'mg250')).toBe(true);
  });

  it('treats a blank query as match-all and ignores surrounding spaces', () => {
    expect(matchesQuery(patient, '   ')).toBe(true);
    expect(matchesQuery(patient, ' asha ')).toBe(true);
  });

  it('rejects non-matching queries', () => {
    expect(matchesQuery(patient, 'rohan')).toBe(false);
  });
});
