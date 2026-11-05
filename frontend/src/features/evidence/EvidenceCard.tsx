import { ExternalLink } from 'lucide-react';
import { useState } from 'react';
import type { Citation } from '@/api/schemas';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CATEGORY_LABELS, CATEGORY_TONES } from '@/lib/categories';
import { cn } from '@/lib/cn';
import { formatScore } from '@/lib/format';

const EXCERPT_CHARS = 220;

interface EvidenceCardProps {
  citation: Citation;
  onOpen: (citation: Citation) => void;
}

export function EvidenceCard({ citation, onOpen }: EvidenceCardProps) {
  const [expanded, setExpanded] = useState(false);
  const long = citation.text.length > EXCERPT_CHARS;
  const text =
    expanded || !long ? citation.text : `${citation.text.slice(0, EXCERPT_CHARS).trimEnd()}…`;

  return (
    <li
      className={cn(
        'rounded-lg border p-3.5',
        citation.cited
          ? 'border-primary/40 bg-primary-soft/50 shadow-soft'
          : 'border-border bg-subtle/60',
      )}
    >
      <div className="flex flex-wrap items-center gap-1.5">
        <span
          className={cn(
            'inline-flex h-5 min-w-7 items-center justify-center rounded-md px-1.5 text-[11px] font-semibold tabular-nums',
            citation.cited ? 'bg-cite text-cite-foreground' : 'bg-border text-muted',
          )}
        >
          {citation.id}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm font-medium" title={citation.report_name}>
          {citation.report_name}
        </span>
        {citation.cited && <Badge tone="primary">Cited</Badge>}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
        <Badge className={CATEGORY_TONES[citation.category]}>
          {CATEGORY_LABELS[citation.category]}
        </Badge>
        <span className="tabular-nums">Page {citation.page}</span>
        {citation.section && <span className="truncate">· {citation.section}</span>}
        <span className="ml-auto tabular-nums">Score {formatScore(citation.score)}</span>
      </div>

      <p className="mt-2.5 whitespace-pre-wrap text-[13px] leading-relaxed">{text}</p>
      {long && (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="mt-1 rounded text-xs font-medium text-primary-text underline-offset-2 hover:underline"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}

      <Button
        variant="secondary"
        size="sm"
        className="mt-3 w-full md:h-8"
        onClick={() => onOpen(citation)}
      >
        <ExternalLink className="size-4" /> Open PDF at page {citation.page}
      </Button>
    </li>
  );
}
