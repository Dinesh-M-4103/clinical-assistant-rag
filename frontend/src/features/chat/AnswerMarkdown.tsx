import { memo, useMemo } from 'react';
import ReactMarkdown, { defaultUrlTransform, type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Citation } from '@/api/schemas';
import { CitationChip } from './CitationChip';
import { citationIdFromHref, isCitationHref, linkifyCitations } from './citations';

interface AnswerMarkdownProps {
  content: string;
  citations: Citation[];
  onOpenCitation: (citation: Citation) => void;
}

const remarkPlugins = [remarkGfm];

const allowCitationLinks = (url: string) => (isCitationHref(url) ? url : defaultUrlTransform(url));

/** Renders an answer as markdown (tables, lists, bold) with `[C#]` markers shown as chips. */
export const AnswerMarkdown = memo(function AnswerMarkdown({
  content,
  citations,
  onOpenCitation,
}: AnswerMarkdownProps) {
  const components = useMemo<Components>(
    () => ({
      a: ({ href, children }) => {
        const id = citationIdFromHref(href);
        if (id) {
          return (
            <CitationChip
              id={id}
              citation={citations.find((citation) => citation.id === id)}
              onOpen={onOpenCitation}
            />
          );
        }
        return (
          <a href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        );
      },
      table: ({ children }) => (
        <div className="table-wrap">
          <table>{children}</table>
        </div>
      ),
    }),
    [citations, onOpenCitation],
  );

  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={remarkPlugins}
        urlTransform={allowCitationLinks}
        components={components}
      >
        {linkifyCitations(content)}
      </ReactMarkdown>
    </div>
  );
});
