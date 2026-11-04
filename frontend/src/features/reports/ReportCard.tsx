import { Eye, FileText, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useDeleteReport } from '@/api/hooks/reports';
import type { Report } from '@/api/schemas';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { IconButton } from '@/components/ui/icon-button';
import { CATEGORY_LABELS, CATEGORY_TONES } from '@/lib/categories';
import { formatBytes, formatDate, pluralize } from '@/lib/format';
import { useWorkspace } from '@/features/workspace/workspaceStore';

export function ReportCard({ report }: { report: Report }) {
  const openPdf = useWorkspace((state) => state.openPdf);
  const deleteReport = useDeleteReport(report.uhid);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const view = () =>
    openPdf({
      uhid: report.uhid,
      reportId: report.report_id,
      reportName: report.name,
      fileUrl: report.file_url,
      page: 1,
      highlight: null,
    });

  return (
    <li className="rounded-lg border border-border bg-surface p-3.5 shadow-soft">
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className="grid size-10 shrink-0 place-items-center rounded-md bg-subtle text-muted"
        >
          <FileText className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold">{report.name}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1">
            <Badge className={CATEGORY_TONES[report.category]}>
              {CATEGORY_LABELS[report.category]}
            </Badge>
            <span className="text-xs tabular-nums text-muted">
              {formatDate(report.uploaded_at)}
            </span>
          </div>
        </div>
      </div>
      <p className="mt-2.5 text-xs tabular-nums text-muted">
        {pluralize(report.page_count, 'page')} · {pluralize(report.chunk_count, 'chunk')} ·{' '}
        {formatBytes(report.size_bytes)}
      </p>
      {report.notes && (
        <p className="mt-1.5 line-clamp-2 text-[13px] leading-snug">{report.notes}</p>
      )}
      <div className="mt-3 flex items-center gap-2">
        <Button variant="secondary" size="sm" className="flex-1 md:h-8" onClick={view}>
          <Eye className="size-4" /> View PDF
        </Button>
        <IconButton
          label={`Delete ${report.name}`}
          icon={<Trash2 className="size-4" />}
          size="iconSm"
          className="hover:text-danger"
          onClick={() => setConfirmOpen(true)}
        />
      </div>
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Delete “${report.name}”?`}
        description="The PDF and its search index are removed. Earlier answers that cited it will no longer open."
        confirmLabel="Delete report"
        pending={deleteReport.isPending}
        onConfirm={() =>
          deleteReport.mutate(report.report_id, { onSuccess: () => setConfirmOpen(false) })
        }
      />
    </li>
  );
}
