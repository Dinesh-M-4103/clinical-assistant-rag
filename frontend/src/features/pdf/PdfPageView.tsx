import { useCallback, useRef } from 'react';
import { Document, Page } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import { EmptyState } from '@/components/EmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { useElementWidth } from '@/hooks/useElementWidth';
import { FileWarning } from 'lucide-react';
import { findHighlightedItems } from './highlight';
import './pdfWorker';

const TEXT_ITEM_SELECTOR = '.react-pdf__Page__textContent span[role="presentation"]';
const PAGE_PADDING_PX = 32;
const MIN_PAGE_WIDTH_PX = 200;

/**
 * Scrolls only the viewer container. `scrollIntoView` would also scroll the page and text-layer
 * boxes (both clip their overflow), which shifts the text layer away from the canvas.
 */
function centreInView(container: HTMLElement, target: HTMLElement) {
  const area = container.getBoundingClientRect();
  const box = target.getBoundingClientRect();
  container.scrollTop += box.top - area.top - (area.height - box.height) / 2;
}

interface PdfPageViewProps {
  file: Blob;
  page: number;
  scale: number;
  highlight: string | null;
  onLoaded: (pageCount: number) => void;
}

/** One PDF page, sized to the container width (scale 1 = fit width) with the cited text marked. */
export function PdfPageView({ file, page, scale, highlight, onLoaded }: PdfPageViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const containerWidth = useElementWidth(containerRef);
  const pageWidth = Math.max(containerWidth - PAGE_PADDING_PX, MIN_PAGE_WIDTH_PX) * scale;

  const markHighlight = useCallback(() => {
    const container = containerRef.current;
    if (!container || !highlight) return;
    const spans = Array.from(container.querySelectorAll<HTMLElement>(TEXT_ITEM_SELECTOR));
    const hits = findHighlightedItems(
      spans.map((span) => span.textContent ?? ''),
      highlight,
    );
    spans.forEach((span, index) => span.classList.toggle('pdf-highlight', hits.has(index)));
    const first = spans[Math.min(...hits)];
    if (first) centreInView(container, first);
  }, [highlight]);

  return (
    <div ref={containerRef} className="min-h-0 flex-1 overflow-auto bg-subtle p-4">
      {containerWidth > 0 && (
        <Document
          file={file}
          onLoadSuccess={({ numPages }) => onLoaded(numPages)}
          loading={<Spinner className="mx-auto mt-10 size-6 text-muted" />}
          error={
            <EmptyState
              icon={<FileWarning className="size-5" />}
              title="This PDF could not be displayed"
              description="The file may be damaged or no longer available."
            />
          }
          className="mx-auto w-fit"
        >
          <Page
            pageNumber={page}
            width={pageWidth}
            renderAnnotationLayer={false}
            onRenderTextLayerSuccess={markHighlight}
            loading={
              <Skeleton
                className="bg-surface"
                style={{ width: pageWidth, height: pageWidth * 1.3 }}
              />
            }
            className="overflow-hidden rounded-sm bg-white shadow-float"
          />
        </Document>
      )}
    </div>
  );
}
