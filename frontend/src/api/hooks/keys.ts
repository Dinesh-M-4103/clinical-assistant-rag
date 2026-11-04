export const queryKeys = {
  health: ['health'] as const,
  patients: ['patients'] as const,
  patient: (uhid: string) => ['patients', uhid] as const,
  reports: (uhid: string) => ['patients', uhid, 'reports'] as const,
  reportPdf: (fileUrl: string) => ['report-pdf', fileUrl] as const,
};
