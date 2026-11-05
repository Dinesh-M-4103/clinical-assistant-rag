import { ArrowDown } from 'lucide-react';
import { useCallback, useEffect } from 'react';
import { useOpenCitation } from './useOpenCitation';
import { AssistantMessage } from './AssistantMessage';
import { UserMessage } from './UserMessage';
import { useChatStore } from './chatStore';
import { retryAnswer } from './streamRunner';
import { useStickToBottom } from './useStickToBottom';
import type { ChatMessage } from './types';
import { Button } from '@/components/ui/button';
import { useWorkspace } from '@/features/workspace/workspaceStore';

interface MessageListProps {
  uhid: string;
  messages: ChatMessage[];
}

export function MessageList({ uhid, messages }: MessageListProps) {
  const { ref, onScroll, away, scrollToBottom } = useStickToBottom<HTMLDivElement>(messages);
  // A newly sent question always jumps to the latest turn, even if the user had scrolled up.
  const turnCount = messages.length;
  useEffect(() => scrollToBottom(), [turnCount, scrollToBottom]);

  const openCitation = useOpenCitation(uhid);
  const setActive = useChatStore((state) => state.setActive);
  const openInspector = useWorkspace((state) => state.openInspector);

  // Stable handlers keep settled messages from re-rendering on every streamed token.
  const showSources = useCallback(
    (id: string) => {
      setActive(uhid, id);
      openInspector('evidence');
    },
    [uhid, setActive, openInspector],
  );
  const showTrace = useCallback(
    (id: string) => {
      setActive(uhid, id);
      openInspector('trace');
    },
    [uhid, setActive, openInspector],
  );
  const regenerate = useCallback((id: string) => void retryAnswer(uhid, id), [uhid]);

  const lastId = messages[messages.length - 1]?.id;
  const streaming = messages.some((message) => message.status === 'streaming');

  return (
    <div className="relative min-h-0 flex-1">
      <div ref={ref} onScroll={onScroll} className="h-full overflow-y-auto overscroll-contain">
        <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6 md:px-6">
          {messages.map((message) =>
            message.role === 'user' ? (
              <UserMessage key={message.id} content={message.content} />
            ) : (
              <AssistantMessage
                key={message.id}
                message={message}
                isLast={message.id === lastId}
                onOpenCitation={openCitation}
                onRegenerate={regenerate}
                onShowSources={showSources}
                onShowTrace={showTrace}
              />
            ),
          )}
        </div>
      </div>
      {away && streaming && (
        <Button
          variant="secondary"
          size="sm"
          onClick={scrollToBottom}
          className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full shadow-float md:h-8"
        >
          <ArrowDown className="size-4" /> Jump to latest
        </Button>
      )}
    </div>
  );
}
