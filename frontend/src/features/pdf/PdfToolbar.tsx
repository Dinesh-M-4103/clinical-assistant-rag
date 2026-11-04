import { ChevronLeft, ChevronRight, Maximize2, ZoomIn, ZoomOut } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { IconButton } from '@/components/ui/icon-button';

export const MIN_SCALE = 0.5;
export const MAX_SCALE = 3;
export const SCALE_STEP = 0.25;

interface PdfToolbarProps {
  page: number;
  pageCount: number;
  scale: number;
  onPage: (page: number) => void;
  onScale: (scale: number) => void;
}

function PageJump({
  page,
  pageCount,
  onPage,
}: Pick<PdfToolbarProps, 'page' | 'pageCount' | 'onPage'>) {
  const [draft, setDraft] = useState(String(page));

  const commit = () => {
    const next = Number.parseInt(draft, 10);
    if (Number.isNaN(next)) setDraft(String(page));
    else onPage(Math.min(Math.max(next, 1), pageCount));
  };

  return (
    <span className="flex items-center gap-1.5 text-sm tabular-nums">
      <label htmlFor="pdf-page" className="sr-only">
        Page number
      </label>
      <input
        id="pdf-page"
        inputMode="numeric"
        value={draft}
        onChange={(event) => setDraft(event.target.value.replace(/\D/g, ''))}
        onBlur={commit}
        onKeyDown={(event) => event.key === 'Enter' && commit()}
        className="h-11 w-12 rounded-md border border-border bg-surface text-center text-base md:h-8 md:text-sm"
      />
      <span className="text-muted">of {pageCount}</span>
    </span>
  );
}

export function PdfToolbar({ page, pageCount, scale, onPage, onScale }: PdfToolbarProps) {
  const clamp = (value: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));
  return (
    <div
      role="toolbar"
      aria-label="PDF controls"
      className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-y border-border bg-surface px-3 py-1.5"
    >
      <div className="flex items-center gap-1">
        <IconButton
          label="Previous page"
          size="iconSm"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          icon={<ChevronLeft className="size-4" />}
        />
        <PageJump key={page} page={page} pageCount={pageCount} onPage={onPage} />
        <IconButton
          label="Next page"
          size="iconSm"
          disabled={page >= pageCount}
          onClick={() => onPage(page + 1)}
          icon={<ChevronRight className="size-4" />}
        />
      </div>
      <div className="flex items-center gap-1">
        <IconButton
          label="Zoom out"
          size="iconSm"
          disabled={scale <= MIN_SCALE}
          onClick={() => onScale(clamp(scale - SCALE_STEP))}
          icon={<ZoomOut className="size-4" />}
        />
        <span aria-live="polite" className="w-11 text-center text-sm tabular-nums">
          {Math.round(scale * 100)}%
        </span>
        <IconButton
          label="Zoom in"
          size="iconSm"
          disabled={scale >= MAX_SCALE}
          onClick={() => onScale(clamp(scale + SCALE_STEP))}
          icon={<ZoomIn className="size-4" />}
        />
        <Button variant="ghost" size="sm" className="md:h-8" onClick={() => onScale(1)}>
          <Maximize2 className="size-4" /> Fit width
        </Button>
      </div>
    </div>
  );
}
