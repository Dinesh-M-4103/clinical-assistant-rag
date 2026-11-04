import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, type ReportUpload } from '../endpoints';
import { queryKeys } from './keys';

export function useReports(uhid: string) {
  return useQuery({ queryKey: queryKeys.reports(uhid), queryFn: () => api.listReports(uhid) });
}

/** The report count lives on the patient, so both caches are refreshed after a change. */
function useRefreshAfterReportChange(uhid: string) {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.reports(uhid) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.patient(uhid), exact: true }),
      queryClient.invalidateQueries({ queryKey: queryKeys.patients, exact: true }),
    ]);
}

/** Errors are shown inside the upload dialog, so the global toast is skipped. */
export function useUploadReport(uhid: string) {
  const refresh = useRefreshAfterReportChange(uhid);
  return useMutation({
    mutationFn: (upload: ReportUpload) => api.uploadReport(uhid, upload),
    meta: { silent: true },
    onSuccess: async (report) => {
      await refresh();
      toast.success(`${report.name} uploaded and indexed`);
    },
  });
}

export function useDeleteReport(uhid: string) {
  const refresh = useRefreshAfterReportChange(uhid);
  return useMutation({
    mutationFn: (reportId: string) => api.deleteReport(uhid, reportId),
    onSuccess: async () => {
      await refresh();
      toast.success('Report deleted');
    },
  });
}
