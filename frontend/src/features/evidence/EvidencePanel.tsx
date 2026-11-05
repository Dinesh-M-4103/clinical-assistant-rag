import { FileSearch, ListTree } from 'lucide-react';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import { useActiveAnswer } from '@/features/chat/useActiveAnswer';
import type { MessageStatus } from '@/features/chat/types';
import { useOpenCitation } from '@/features/chat/useOpenCitation';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { EvidenceCard } from './EvidenceCard';

const NOTHING_RETRIEVED = {
  title: 'No passages were retrieved',
  description: 'This answer did not draw on any report passages.',
};

const NO_PASSAGES_COPY: Record<MessageStatus, { title: string; description?: string }> = {
  streaming: { title: 'Searching the records…' },
  done: NOTHING_RETRIEVED,
  stopped: NOTHING_RETRIEVED,
  error: {
    title: 'No evidence available',
    description: 'The answer failed before any passages were returned.',
  },
};

export function EvidencePanel({ uhid }: { uhid: string }) {
  const active = useActiveAnswer(uhid);
  const openCitation = useOpenCitation(uhid);
  const setInspectorTab = useWorkspace((state) => state.setInspectorTab);

  if (!active) {
    return (
      <EmptyState
        icon={<FileSearch className="size-5" />}
        title="No evidence yet"
        description="Ask a question and the passages retrieved from the records will appear here."
      />
    );
  }

  const { citations } = active.message;
  const cited = citations.filter((citation) => citation.cited);
  const others = citations.filter((citation) => !citation.cited);

  if (citations.length === 0) {
    const { title, description } = NO_PASSAGES_COPY[active.message.status];
    return (
      <EmptyState
        icon={<FileSearch className="size-5" />}
        title={title}
        description={description}
      />
    );
  }

  return (
    <div className="space-y-5 p-4">
      <p className="text-xs text-muted">
        For: <span className="font-medium text-foreground">{active.question}</span>
      </p>
      {cited.length > 0 && (
        <section aria-label="Cited passages" className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
            Cited in the answer ({cited.length})
          </h3>
          <ul className="space-y-3">
            {cited.map((citation) => (
              <EvidenceCard key={citation.id} citation={citation} onOpen={openCitation} />
            ))}
          </ul>
        </section>
      )}
      {others.length > 0 && (
        <section aria-label="Also retrieved" className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
            Also retrieved ({others.length})
          </h3>
          <ul className="space-y-3">
            {others.map((citation) => (
              <EvidenceCard key={citation.id} citation={citation} onOpen={openCitation} />
            ))}
          </ul>
        </section>
      )}
      <Button
        variant="ghost"
        className="w-full text-primary-text"
        onClick={() => setInspectorTab('trace')}
      >
        <ListTree className="size-4" /> How this answer was made
      </Button>
    </div>
  );
}
