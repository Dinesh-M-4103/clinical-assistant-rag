import { ArrowLeft, ListTree } from 'lucide-react';
import type { Trace } from '@/api/schemas';
import { EmptyState } from '@/components/EmptyState';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useActiveAnswer } from '@/features/chat/useActiveAnswer';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { pluralize } from '@/lib/format';
import { CandidatesTable } from './CandidatesTable';
import { TimingBar } from './TimingBar';

const INTENT_LABELS: Record<Trace['intent'], string> = {
  question: 'Records question',
  greeting: 'Greeting',
  off_topic: 'Off topic',
};

function ModelList({ trace }: { trace: Trace }) {
  const rows = [
    ['Language model', trace.models.llm],
    ['Embedding model', trace.models.embedding],
    ['Reranker', trace.models.reranker],
  ] as const;
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Models</h3>
      <dl className="space-y-1.5 text-xs">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3">
            <dt className="shrink-0 text-muted">{label}</dt>
            <dd className="min-w-0 truncate font-medium" title={value ?? undefined}>
              {value ?? 'Not used'}
            </dd>
          </div>
        ))}
        {trace.tokens && (
          <div className="flex justify-between gap-3">
            <dt className="text-muted">Tokens</dt>
            <dd className="font-medium tabular-nums">
              {trace.tokens.prompt.toLocaleString()} in · {trace.tokens.completion.toLocaleString()}{' '}
              out
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}

export function TracePanel({ uhid }: { uhid: string }) {
  const active = useActiveAnswer(uhid);
  const setInspectorTab = useWorkspace((state) => state.setInspectorTab);
  const trace = active?.message.trace;

  if (!active || !trace) {
    return (
      <EmptyState
        icon={<ListTree className="size-5" />}
        title="No trace yet"
        description="Once an answer is complete, you can see how it was retrieved, ranked and generated."
      />
    );
  }

  return (
    <div className="space-y-6 p-4">
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 md:hidden"
        onClick={() => setInspectorTab('evidence')}
      >
        <ArrowLeft className="size-4" /> Evidence
      </Button>
      <header className="space-y-2">
        <h2 className="text-base font-semibold">How this answer was made</h2>
        <div className="flex flex-wrap gap-1.5">
          <Badge tone="primary">{INTENT_LABELS[trace.intent]}</Badge>
          <Badge>{pluralize(trace.candidates.length, 'candidate')}</Badge>
          {trace.insufficient_evidence && <Badge tone="warning">Insufficient evidence</Badge>}
        </div>
      </header>

      {trace.rewritten_query && (
        <div className="space-y-1.5">
          <h3 className="text-sm font-semibold">Rewritten query</h3>
          <p className="rounded-md border border-border bg-subtle px-3 py-2 text-[13px] leading-snug">
            {trace.rewritten_query}
          </p>
        </div>
      )}

      <TimingBar timings={trace.timings_ms} />
      {trace.candidates.length > 0 && (
        <CandidatesTable candidates={trace.candidates} citations={active.message.citations} />
      )}
      <ModelList trace={trace} />
    </div>
  );
}
