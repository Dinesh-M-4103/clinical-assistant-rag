import { FileSearch, FolderOpen, MessageSquare, type LucideIcon } from 'lucide-react';
import { useReports } from '@/api/hooks/reports';
import { useActiveAnswer } from '@/features/chat/useActiveAnswer';
import { cn } from '@/lib/cn';
import { useWorkspace } from './workspaceStore';

interface TabButtonProps {
  label: string;
  icon: LucideIcon;
  active: boolean;
  count?: number;
  onSelect: () => void;
}

function TabButton({ label, icon: Icon, active, count, onSelect }: TabButtonProps) {
  return (
    <button
      type="button"
      aria-current={active ? 'page' : undefined}
      onClick={onSelect}
      className={cn(
        'relative flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium transition-colors',
        active ? 'text-primary-text' : 'text-muted',
      )}
    >
      <Icon aria-hidden className="size-5" />
      {label}
      {count ? (
        <span className="absolute right-[calc(50%-1.75rem)] top-1.5 min-w-4 rounded-full bg-primary px-1 text-center text-[10px] font-semibold tabular-nums leading-4 text-primary-foreground">
          {count}
        </span>
      ) : null}
      {active && (
        <span aria-hidden className="absolute inset-x-6 top-0 h-0.5 rounded-b bg-primary" />
      )}
    </button>
  );
}

/** Phone navigation between the chat and the two inspector views (trace is reached from Evidence). */
export function BottomTabBar({ uhid }: { uhid: string }) {
  const { inspectorOpen, inspectorTab, openInspector, closeInspector } = useWorkspace();
  const { data: reports } = useReports(uhid);
  const citedCount = useActiveAnswer(uhid)?.message.citations.filter((c) => c.cited).length;

  return (
    <nav
      aria-label="Workspace sections"
      className="flex border-t border-border bg-surface pb-[env(safe-area-inset-bottom)]"
    >
      <TabButton
        label="Chat"
        icon={MessageSquare}
        active={!inspectorOpen}
        onSelect={closeInspector}
      />
      <TabButton
        label="Evidence"
        icon={FileSearch}
        active={inspectorOpen && inspectorTab !== 'reports'}
        count={citedCount}
        onSelect={() => openInspector('evidence')}
      />
      <TabButton
        label="Reports"
        icon={FolderOpen}
        active={inspectorOpen && inspectorTab === 'reports'}
        count={reports?.length}
        onSelect={() => openInspector('reports')}
      />
    </nav>
  );
}
