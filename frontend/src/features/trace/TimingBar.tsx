import type { Trace } from '@/api/schemas';
import { formatMs } from '@/lib/format';

const STAGES = [
  { key: 'rewrite', label: 'Rewrite', swatch: 'bg-violet-500' },
  { key: 'retrieval', label: 'Retrieval', swatch: 'bg-primary' },
  { key: 'rerank', label: 'Rerank', swatch: 'bg-amber-500' },
  { key: 'generation', label: 'Generation', swatch: 'bg-emerald-500' },
] as const;

export function TimingBar({ timings }: { timings: Trace['timings_ms'] }) {
  const stages = STAGES.map((stage) => ({ ...stage, ms: timings[stage.key] }));
  const sum = stages.reduce((total, stage) => total + stage.ms, 0);

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold">Timing</h3>
        <span className="text-sm tabular-nums text-muted">Total {formatMs(timings.total)}</span>
      </div>
      <div
        role="img"
        aria-label={stages.map((stage) => `${stage.label} ${formatMs(stage.ms)}`).join(', ')}
        className="flex h-2.5 gap-0.5 overflow-hidden rounded-full bg-subtle"
      >
        {stages
          .filter((stage) => stage.ms > 0)
          .map((stage) => (
            <div
              key={stage.key}
              className={stage.swatch}
              style={{ width: `${(stage.ms / sum) * 100}%` }}
            />
          ))}
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        {stages.map((stage) => (
          <div key={stage.key} className="flex items-center gap-2">
            <span aria-hidden className={`size-2.5 shrink-0 rounded-sm ${stage.swatch}`} />
            <dt className="text-muted">{stage.label}</dt>
            <dd className="ml-auto font-medium tabular-nums">{formatMs(stage.ms)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
