import { FileUp, FolderOpen, Upload } from 'lucide-react';
import { useReports } from '@/api/hooks/reports';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { pluralize } from '@/lib/format';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { ReportCard } from './ReportCard';

function ReportsSkeleton() {
  return (
    <div className="space-y-3 p-4" role="status" aria-label="Loading reports">
      {[0, 1, 2].map((index) => (
        <Skeleton key={index} className="h-36 rounded-lg" />
      ))}
    </div>
  );
}

export function ReportsPanel({ uhid }: { uhid: string }) {
  const { data: reports, isPending, isError, refetch } = useReports(uhid);
  const setUploadOpen = useWorkspace((state) => state.setUploadOpen);

  if (isPending) return <ReportsSkeleton />;
  if (isError) {
    return (
      <EmptyState
        icon={<FolderOpen className="size-5" />}
        title="Couldn't load reports"
        action={<Button onClick={() => void refetch()}>Retry</Button>}
      />
    );
  }
  if (reports.length === 0) {
    return (
      <EmptyState
        icon={<FileUp className="size-5" />}
        title="No reports yet"
        description="Upload a PDF to make it searchable and citable."
        action={
          <Button variant="primary" onClick={() => setUploadOpen(true)}>
            <Upload className="size-4" /> Upload report
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
          {pluralize(reports.length, 'report')}
        </h3>
        <Button
          variant="secondary"
          size="sm"
          className="md:h-8"
          onClick={() => setUploadOpen(true)}
        >
          <Upload className="size-4" /> Upload
        </Button>
      </div>
      <ul className="space-y-3">
        {reports.map((report) => (
          <ReportCard key={report.report_id} report={report} />
        ))}
      </ul>
    </div>
  );
}
