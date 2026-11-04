import { cn } from '@/lib/cn';

interface BrandProps {
  /** Hide the wordmark and keep only the logo (icon rail). */
  compact?: boolean;
  className?: string;
}

export function Brand({ compact = false, className }: BrandProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground shadow-soft"
      >
        <svg
          viewBox="0 0 24 24"
          className="size-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
        >
          <path d="M12 5v14M5 12h14" />
        </svg>
      </span>
      {!compact && (
        <span className="text-[15px] font-semibold tracking-tight">Clinical Assistant</span>
      )}
    </div>
  );
}
