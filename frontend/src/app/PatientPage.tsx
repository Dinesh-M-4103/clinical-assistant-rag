import { UserX } from 'lucide-react';
import { lazy, Suspense, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { usePatient } from '@/api/hooks/patients';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Button } from '@/components/ui/button';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { describeError } from '@/lib/errors';
import { ChatPanel } from '@/features/chat/ChatPanel';
import { PatientHeader, PatientHeaderSkeleton } from '@/features/patients/PatientHeader';
import { BottomTabBar } from '@/features/workspace/BottomTabBar';
import { InspectorPanel } from '@/features/workspace/InspectorPanel';
import { InspectorSheet } from '@/features/workspace/InspectorSheet';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { UploadReportDialog } from '@/features/reports/UploadReportDialog';

const PdfViewerSheet = lazy(() => import('@/features/pdf/PdfViewerSheet'));

function PatientUnavailable({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const missing = error instanceof ApiError && error.status === 404;
  return (
    <EmptyState
      className="m-auto"
      icon={<UserX className="size-5" />}
      title={missing ? 'Patient not found' : 'Couldn’t load this patient'}
      description={
        missing ? 'They may have been deleted, or the link is wrong.' : describeError(error)
      }
      action={
        missing ? (
          <Button asChild variant="primary">
            <Link to="/">Back to patients</Link>
          </Button>
        ) : (
          <Button onClick={onRetry}>Retry</Button>
        )
      }
    />
  );
}

export function PatientPage() {
  const { uhid = '' } = useParams();
  const { data: patient, error, isPending, refetch } = usePatient(uhid);
  const breakpoint = useBreakpoint();
  const inspectorOpen = useWorkspace((state) => state.inspectorOpen);
  const hasPdf = useWorkspace((state) => state.pdf !== null);
  const closeInspector = useWorkspace((state) => state.closeInspector);
  const closePdf = useWorkspace((state) => state.closePdf);

  useEffect(() => {
    closeInspector();
    closePdf();
  }, [uhid, closeInspector, closePdf]);

  if (isPending) return <PatientHeaderSkeleton />;
  if (error) return <PatientUnavailable error={error} onRetry={() => void refetch()} />;

  const mobileInspector = breakpoint === 'mobile' && inspectorOpen;
  return (
    <ErrorBoundary resetKey={uhid}>
      <div className="flex min-h-0 flex-1">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <PatientHeader patient={patient} />
          {mobileInspector ? (
            <InspectorPanel uhid={uhid} />
          ) : (
            <ChatPanel key={uhid} patient={patient} />
          )}
          {breakpoint === 'mobile' && <BottomTabBar uhid={uhid} />}
        </div>
        {breakpoint === 'desktop' && (
          <aside
            aria-label="Inspector"
            className="w-[26rem] shrink-0 border-l border-border 2xl:w-[30rem]"
          >
            <InspectorPanel uhid={uhid} />
          </aside>
        )}
      </div>
      {breakpoint === 'tablet' && <InspectorSheet uhid={uhid} />}
      <UploadReportDialog uhid={uhid} />
      {hasPdf && (
        <Suspense fallback={null}>
          <PdfViewerSheet />
        </Suspense>
      )}
    </ErrorBoundary>
  );
}
