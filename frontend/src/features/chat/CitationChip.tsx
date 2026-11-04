import type { Citation } from '@/api/schemas';
import { cn } from '@/lib/cn';

interface CitationChipProps {
  id: string;
  /** Undefined when the model cited an id that was not among the retrieved chunks. */
  citation: Citation | undefined;
  onOpen: (citation: Citation) => void;
}

const base =
  'ml-0.5 inline-flex h-5 min-w-7 items-center justify-center rounded-md px-1.5 align-[0.1em] text-[11px] font-semibold tabular-nums leading-none';

/** Inline `[C1]` marker; opens the cited PDF page when the chunk is known. */
export function CitationChip({ id, citation, onOpen }: CitationChipProps) {
  if (!citation) {
    return <span className={cn(base, 'bg-subtle text-muted')}>{id}</span>;
  }
  return (
    <button
      type="button"
      data-citation={id}
      onClick={() => onOpen(citation)}
      title={`${citation.report_name} · page ${citation.page}`}
      aria-label={`Open ${citation.report_name}, page ${citation.page} (citation ${id})`}
      className={cn(
        base,
        'bg-cite text-cite-foreground transition-colors hover:bg-primary hover:text-primary-foreground',
      )}
    >
      {id}
    </button>
  );
}
