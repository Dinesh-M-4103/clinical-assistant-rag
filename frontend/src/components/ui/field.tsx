import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/cn';

const control =
  'block w-full rounded-md border border-border bg-surface px-3 text-base text-foreground shadow-soft transition-colors placeholder:text-muted/80 hover:border-muted/50 disabled:cursor-not-allowed disabled:opacity-60 aria-[invalid=true]:border-danger md:text-sm';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn(control, 'h-11 md:h-10', className)} {...props} />
  ),
);
Input.displayName = 'Input';

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea ref={ref} className={cn(control, 'min-h-20 resize-y py-2.5', className)} {...props} />
));
Textarea.displayName = 'Textarea';

/** Native select keeps the OS picker on phones; only the chrome is restyled. */
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(control, 'h-11 appearance-none pr-9 md:h-10', className)}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        aria-hidden
        className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted"
      />
    </div>
  ),
);
Select.displayName = 'Select';

interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  /** Receives the ids that wire the control to its label and messages. */
  children: (ids: { id: string; describedBy: string | undefined; invalid: boolean }) => ReactNode;
}

/** Label + control + error/hint with correct `for`, `aria-describedby` and `aria-invalid` wiring. */
export function Field({ label, error, hint, children }: FieldProps) {
  const id = useId();
  const messageId = `${id}-message`;
  const message = error ?? hint;
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      {children({ id, describedBy: message ? messageId : undefined, invalid: Boolean(error) })}
      {message && (
        <p id={messageId} className={cn('text-xs', error ? 'text-danger' : 'text-muted')}>
          {message}
        </p>
      )}
    </div>
  );
}
