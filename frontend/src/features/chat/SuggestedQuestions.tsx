import { MessageSquareText } from 'lucide-react';

const SUGGESTIONS = [
  'Summarise this patient’s key diagnoses and history',
  'What is the latest HbA1c result?',
  'List current medications with doses',
  'Which lab values are outside the reference range?',
] as const;

interface SuggestedQuestionsProps {
  onPick: (question: string) => void;
}

export function SuggestedQuestions({ onPick }: SuggestedQuestionsProps) {
  return (
    <ul className="grid w-full gap-2 sm:grid-cols-2">
      {SUGGESTIONS.map((question) => (
        <li key={question}>
          <button
            type="button"
            onClick={() => onPick(question)}
            className="flex min-h-14 w-full items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3 text-left text-sm shadow-soft transition-colors hover:border-primary/50 hover:bg-primary-soft/60"
          >
            <MessageSquareText aria-hidden className="size-4 shrink-0 text-primary-text" />
            <span>{question}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
