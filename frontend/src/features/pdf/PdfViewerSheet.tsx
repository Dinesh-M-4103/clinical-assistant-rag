import { FileWarning } from 'lucide-react';
import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import { useReportPdf } from '@/api/hooks/pdf';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Spinner } from '@/components/ui/spinner';
import { describeError } from '@/lib/errors';
import { useWorkspace, type PdfTarget } from '@/features/workspace/workspaceStore';
import { PdfPageView } from './PdfPageView';
import { MAX_SCALE, MIN_SCALE, PdfToolbar, SCALE_STEP } from './PdfToolbar';

function PdfBody({ target }: { target: PdfTarget }) {
  const pdf = useReportPdf(target.fileUrl);
  const [page, setPage] = useState(target.page);
  const [pageCount, setPageCount] = useState(0);
  const [scale, setScale] = useState(1);

  const goTo = (next: number) => setPage(Math.min(Math.max(next, 1), Math.max(pageCount, 1)));
  const zoomBy = (delta: number) =>
    setScale((current) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, current + delta)));

  // Keyboard shortcuts live on the dialog root so they work wherever focus sits inside it.
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => rootRef.current?.focus(), []);
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.target instanceof HTMLInputElement) return;
    const actions: Record<string, () => void> = {
      ArrowLeft: () => goTo(page - 1),
      PageUp: () => goTo(page - 1),
      ArrowRight: () => goTo(page + 1),
      PageDown: () => goTo(page + 1),
      '+': () => zoomBy(SCALE_STEP),
      '=': () => zoomBy(SCALE_STEP),
      '-': () => zoomBy(-SCALE_STEP),
      '0': () => setScale(1),
    };
    const action = actions[event.key];
    if (action) {
      event.preventDefault();
      action();
    }
  };

  let content: ReactNode;
  if (pdf.isPending) {
    content = (
      <div
        role="status"
        className="flex flex-1 items-center justify-center gap-2 text-sm text-muted"
      >
        <Spinner /> Loading PDF…
      </div>
    );
  } else if (pdf.isError) {
    content = (
      <EmptyState
        className="m-auto"
        icon={<FileWarning className="size-5" />}
        title="Couldn't load this PDF"
        description={describeError(pdf.error)}
        action={<Button onClick={() => void pdf.refetch()}>Retry</Button>}
      />
    );
  } else {
    content = (
      <>
        <PdfToolbar
          page={page}
          pageCount={pageCount || 1}
          scale={scale}
          onPage={goTo}
          onScale={setScale}
        />
        <PdfPageView
          file={pdf.data}
          page={page}
          scale={scale}
          highlight={target.highlight}
          onLoaded={setPageCount}
        />
      </>
    );
  }

  return (
    <div
      ref={rootRef}
      tabIndex={-1}
      onKeyDown={onKeyDown}
      className="flex min-h-0 flex-1 flex-col focus:outline-none focus-visible:ring-0"
    >
      <DialogHeader className="pb-3">
        <DialogTitle className="truncate">{target.reportName}</DialogTitle>
        <DialogDescription>
          {target.highlight
            ? 'The cited passage is highlighted where it can be located.'
            : 'Use the arrow keys to change page.'}
        </DialogDescription>
      </DialogHeader>
      {content}
    </div>
  );
}

/** Slide-over PDF reader opened from citations and report cards; Esc closes it. */
export default function PdfViewerSheet() {
  const target = useWorkspace((state) => state.pdf);
  const close = useWorkspace((state) => state.closePdf);

  return (
    <Dialog open={target !== null} onOpenChange={(open) => !open && close()}>
      {target && (
        <DialogContent
          placement="right"
          className="max-w-[56rem]"
          onOpenAutoFocus={(event) => event.preventDefault()}
        >
          <PdfBody key={`${target.reportId}:${target.page}`} target={target} />
        </DialogContent>
      )}
    </Dialog>
  );
}
