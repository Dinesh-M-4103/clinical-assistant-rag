import { FileUp, MessagesSquare } from 'lucide-react';
import type { Patient } from '@/api/schemas';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { SuggestedQuestions } from './SuggestedQuestions';

interface ChatEmptyStateProps {
  patient: Patient;
  onAsk: (question: string) => void;
}

export function ChatEmptyState({ patient, onAsk }: ChatEmptyStateProps) {
  const setUploadOpen = useWorkspace((state) => state.setUploadOpen);

  if (patient.report_count === 0) {
    return (
      <EmptyState
        className="m-auto"
        icon={<FileUp className="size-5" />}
        title="Upload a report to begin"
        description={`${patient.name} has no records yet. Upload a PDF report and you can start asking questions about it.`}
        action={
          <Button variant="primary" onClick={() => setUploadOpen(true)}>
            <FileUp className="size-4" /> Upload report
          </Button>
        }
      />
    );
  }

  const firstName = patient.name.split(' ')[0];
  return (
    <div className="m-auto flex w-full max-w-2xl flex-col items-center px-4 py-8 text-center">
      <div className="mb-4 grid size-12 place-items-center rounded-full bg-primary-soft text-primary-text">
        <MessagesSquare className="size-5" />
      </div>
      <h2 className="text-lg font-semibold">Ask about {firstName}&rsquo;s records</h2>
      <p className="mb-6 mt-1.5 max-w-md text-sm text-muted">
        Answers come only from the uploaded reports, with citations you can open on the exact page.
      </p>
      <SuggestedQuestions onPick={onAsk} />
    </div>
  );
}
