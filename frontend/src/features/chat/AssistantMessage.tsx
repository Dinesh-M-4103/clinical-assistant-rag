import { AlertCircle, RotateCcw, Sparkles } from 'lucide-react';
import { memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AnswerMarkdown } from './AnswerMarkdown';
import { MessageActions } from './MessageActions';
import { TypingIndicator } from './TypingIndicator';
import type { ChatMessage } from './types';
import type { Citation } from '@/api/schemas';

interface AssistantMessageProps {
  message: ChatMessage;
  isLast: boolean;
  onOpenCitation: (citation: Citation) => void;
  /** Handlers take the message id so the parent can pass the same functions to every message. */
  onRegenerate: (id: string) => void;
  onShowSources: (id: string) => void;
  onShowTrace: (id: string) => void;
}

function typingLabel(message: ChatMessage): string {
  return message.citations.length > 0 ? 'Writing the answer…' : 'Searching the records…';
}

export const AssistantMessage = memo(function AssistantMessage({
  message,
  isLast,
  onOpenCitation,
  onRegenerate,
  onShowSources,
  onShowTrace,
}: AssistantMessageProps) {
  const { status, content, citations, trace, error } = message;
  const streaming = status === 'streaming';
  const settled = status === 'done';
  const citedCount = citations.filter((citation) => citation.cited).length;
  const regenerate = () => onRegenerate(message.id);

  return (
    <article aria-label="Assistant answer" className="flex gap-3">
      <span
        aria-hidden
        className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-full bg-primary-soft text-primary-text"
      >
        <Sparkles className="size-4" />
      </span>
      <div className="min-w-0 flex-1 space-y-2">
        {streaming && content === '' && <TypingIndicator label={typingLabel(message)} />}
        {content !== '' && (
          <AnswerMarkdown content={content} citations={citations} onOpenCitation={onOpenCitation} />
        )}
        {streaming && content !== '' && <TypingIndicator />}

        {trace?.insufficient_evidence && (
          <Badge tone="warning">Not enough evidence in the uploaded records</Badge>
        )}
        {status === 'stopped' && (
          <div className="flex flex-wrap items-center gap-2">
            <Badge>Stopped</Badge>
            <Button variant="secondary" size="sm" className="md:h-8" onClick={regenerate}>
              <RotateCcw className="size-4" /> Regenerate
            </Button>
          </div>
        )}
        {status === 'error' && (
          <div
            role="alert"
            className="flex flex-wrap items-center gap-3 rounded-md bg-danger-soft px-3 py-2.5 text-sm text-danger"
          >
            <AlertCircle className="size-4 shrink-0" />
            <span className="min-w-0 flex-1">{error ?? 'The answer could not be generated.'}</span>
            <Button variant="secondary" size="sm" className="md:h-8" onClick={regenerate}>
              <RotateCcw className="size-4" /> Retry
            </Button>
          </div>
        )}
        {settled && content !== '' && (
          <MessageActions
            content={content}
            citedCount={citedCount}
            canRegenerate={isLast}
            onRegenerate={regenerate}
            onShowSources={() => onShowSources(message.id)}
            onShowTrace={() => onShowTrace(message.id)}
          />
        )}
      </div>
    </article>
  );
});
