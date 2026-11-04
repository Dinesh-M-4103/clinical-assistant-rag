import { ArrowUp, Square } from 'lucide-react';
import { useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';

const MAX_HEIGHT_PX = 176;

interface ComposerProps {
  streaming: boolean;
  disabled: boolean;
  placeholder: string;
  onSend: (question: string) => void;
  onStop: () => void;
}

/** Enter sends, Shift+Enter inserts a newline; the textarea grows with its content. */
export function Composer({ streaming, disabled, placeholder, onSend, onStop }: ComposerProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const question = value.trim();
  const canSend = !disabled && !streaming && question.length > 0;

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!canSend) return;
    onSend(question);
    setValue('');
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form
      onSubmit={submit}
      className="flex items-end gap-2 rounded-xl border border-border bg-surface p-2 shadow-soft transition-colors focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-ring/30"
    >
      <textarea
        ref={textareaRef}
        value={value}
        rows={1}
        disabled={disabled}
        aria-label="Ask a question about this patient"
        placeholder={placeholder}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={onKeyDown}
        className="min-h-11 flex-1 resize-none bg-transparent px-2 py-2.5 text-base leading-snug placeholder:text-muted focus:outline-none focus-visible:ring-0 disabled:cursor-not-allowed md:text-sm"
      />
      {streaming ? (
        <Button
          variant="secondary"
          size="icon"
          onClick={onStop}
          aria-label="Stop generating"
          title="Stop generating"
        >
          <Square className="size-4 fill-current" />
        </Button>
      ) : (
        <Button
          type="submit"
          variant="primary"
          size="icon"
          disabled={!canSend}
          aria-label="Send message"
          title="Send (Enter)"
        >
          <ArrowUp className="size-[18px]" />
        </Button>
      )}
    </form>
  );
}
