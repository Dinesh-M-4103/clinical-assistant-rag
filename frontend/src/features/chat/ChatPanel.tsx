import type { Patient } from '@/api/schemas';
import { ChatEmptyState } from './ChatEmptyState';
import { Composer } from './Composer';
import { MessageList } from './MessageList';
import { selectSession, useChatStore } from './chatStore';
import { sendQuestion, stopAnswer } from './streamRunner';

function statusText(streaming: boolean, last: string | undefined): string {
  if (streaming) return 'Generating answer…';
  return last === 'done' ? 'Answer ready.' : '';
}

export function ChatPanel({ patient }: { patient: Patient }) {
  const { uhid } = patient;
  const { messages } = useChatStore(selectSession(uhid));

  const last = messages[messages.length - 1];
  const streaming = last?.status === 'streaming';
  const noReports = patient.report_count === 0;

  const ask = (question: string) => void sendQuestion(uhid, question);

  return (
    <section aria-label="Chat" className="flex min-h-0 flex-1 flex-col">
      {messages.length === 0 ? (
        <div className="flex min-h-0 flex-1 overflow-y-auto">
          <ChatEmptyState patient={patient} onAsk={ask} />
        </div>
      ) : (
        <MessageList key={uhid} uhid={uhid} messages={messages} />
      )}
      <p role="status" className="sr-only">
        {statusText(streaming, last?.status)}
      </p>
      <div className="border-t border-border bg-background px-4 pb-3 pt-3 md:px-6">
        <div className="mx-auto w-full max-w-3xl space-y-2">
          <Composer
            key={uhid}
            streaming={streaming}
            disabled={noReports}
            placeholder={
              noReports ? 'Upload a report to start chatting' : 'Ask about this patient’s records…'
            }
            onSend={ask}
            onStop={() => stopAnswer(uhid)}
          />
          <p className="text-center text-xs text-muted">
            Generated from uploaded records — verify before clinical use
          </p>
        </div>
      </div>
    </section>
  );
}
