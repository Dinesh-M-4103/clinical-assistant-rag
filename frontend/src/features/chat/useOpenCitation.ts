import { useCallback } from 'react';
import { reportFileUrl } from '@/api/endpoints';
import type { Citation } from '@/api/schemas';
import { useWorkspace } from '@/features/workspace/workspaceStore';

/** Opens the PDF viewer on a citation's page, highlighting the cited passage. */
export function useOpenCitation(uhid: string) {
  const openPdf = useWorkspace((state) => state.openPdf);
  return useCallback(
    (citation: Citation) =>
      openPdf({
        uhid,
        reportId: citation.report_id,
        reportName: citation.report_name,
        fileUrl: reportFileUrl(uhid, citation.report_id),
        page: citation.page,
        highlight: citation.text,
      }),
    [uhid, openPdf],
  );
}
