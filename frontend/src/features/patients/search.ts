import type { Patient } from '@/api/schemas';

/** Case-insensitive match on name or UHID; an empty query matches everyone. */
export function matchesQuery(patient: Patient, query: string): boolean {
  const needle = query.trim().toLowerCase();
  return needle === '' || `${patient.name} ${patient.uhid}`.toLowerCase().includes(needle);
}
