import { X } from 'lucide-react';
import { useReports } from '@/api/hooks/reports';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Badge } from '@/components/ui/badge';
import { IconButton } from '@/components/ui/icon-button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useActiveAnswer } from '@/features/chat/useActiveAnswer';
import { EvidencePanel } from '@/features/evidence/EvidencePanel';
import { ReportsPanel } from '@/features/reports/ReportsPanel';
import { TracePanel } from '@/features/trace/TracePanel';
import { useWorkspace, type InspectorTab } from './workspaceStore';

interface InspectorPanelProps {
  uhid: string;
  /** Present when the panel is shown in a slide-over, which needs its own close control. */
  onClose?: () => void;
}

function isInspectorTab(value: string): value is InspectorTab {
  return value === 'evidence' || value === 'reports' || value === 'trace';
}

/** Evidence / Reports / Trace tabs. On phones the bottom bar drives the tab, so the tab list is hidden. */
export function InspectorPanel({ uhid, onClose }: InspectorPanelProps) {
  const tab = useWorkspace((state) => state.inspectorTab);
  const setTab = useWorkspace((state) => state.setInspectorTab);
  const { data: reports } = useReports(uhid);
  const citedCount = useActiveAnswer(uhid)?.message.citations.filter((c) => c.cited).length ?? 0;

  return (
    <Tabs
      value={tab}
      onValueChange={(value) => isInspectorTab(value) && setTab(value)}
      className="flex h-full min-h-0 flex-col bg-surface"
    >
      <div className="flex items-center border-b border-border pr-2 max-md:hidden md:max-xl:pr-3">
        <TabsList className="flex-1 border-b-0">
          <TabsTrigger value="evidence">
            Evidence{' '}
            {citedCount > 0 && (
              <Badge tone="primary" className="tabular-nums">
                {citedCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="reports">
            Reports {reports && <Badge className="tabular-nums">{reports.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="trace">Trace</TabsTrigger>
        </TabsList>
        {onClose && (
          <IconButton
            label="Close inspector"
            size="iconSm"
            icon={<X className="size-4" />}
            onClick={onClose}
          />
        )}
      </div>
      <ErrorBoundary resetKey={`${uhid}:${tab}`}>
        <TabsContent value="evidence">
          <EvidencePanel uhid={uhid} />
        </TabsContent>
        <TabsContent value="reports">
          <ReportsPanel uhid={uhid} />
        </TabsContent>
        <TabsContent value="trace">
          <TracePanel uhid={uhid} />
        </TabsContent>
      </ErrorBoundary>
    </Tabs>
  );
}
