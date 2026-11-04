import { Check, Copy, FileSearch, ListTree, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { pluralize } from '@/lib/format';

interface MessageActionsProps {
  content: string;
  citedCount: number;
  canRegenerate: boolean;
  onRegenerate: () => void;
  onShowSources: () => void;
  onShowTrace: () => void;
}

const action = 'text-muted md:h-8';
const iconAction = cn(action, 'w-11 px-0 md:w-8');

export function MessageActions({
  content,
  citedCount,
  canRegenerate,
  onRegenerate,
  onShowSources,
  onShowTrace,
}: MessageActionsProps) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error('Could not copy to the clipboard');
    }
  };

  return (
    <div className="-ml-2 flex flex-wrap items-center gap-x-1 gap-y-0.5 pt-1">
      <Button
        variant="ghost"
        size="sm"
        className={iconAction}
        onClick={() => void copy()}
        aria-label={copied ? 'Copied' : 'Copy answer'}
        title="Copy answer"
      >
        {copied ? <Check className="size-4 text-success" /> : <Copy className="size-4" />}
      </Button>
      {canRegenerate && (
        <Button
          variant="ghost"
          size="sm"
          className={iconAction}
          onClick={onRegenerate}
          aria-label="Regenerate answer"
          title="Regenerate answer"
        >
          <RotateCcw className="size-4" />
        </Button>
      )}
      <Button variant="ghost" size="sm" className={action} onClick={onShowSources}>
        <FileSearch className="size-4" />
        {citedCount > 0 ? pluralize(citedCount, 'source') : 'Sources'}
      </Button>
      <Button variant="ghost" size="sm" className={action} onClick={onShowTrace}>
        <ListTree className="size-4" />
        How it was made
      </Button>
    </div>
  );
}
