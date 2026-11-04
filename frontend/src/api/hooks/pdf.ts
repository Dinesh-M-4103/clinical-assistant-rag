import { useQuery } from '@tanstack/react-query';
import { api } from '../endpoints';
import { queryKeys } from './keys';

/** Downloads a report PDF through the API client so errors and mocks behave like any other call. */
export function useReportPdf(fileUrl: string) {
  return useQuery({
    queryKey: queryKeys.reportPdf(fileUrl),
    queryFn: () => api.fetchReportPdf(fileUrl),
    staleTime: Infinity,
    gcTime: 5 * 60_000,
  });
}
