interface TypingIndicatorProps {
  label?: string;
}

export function TypingIndicator({ label }: TypingIndicatorProps) {
  return (
    <div className="flex items-center gap-2.5 text-sm text-muted">
      <span aria-hidden className="flex items-center gap-1">
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className="size-1.5 animate-dot-bounce rounded-full bg-muted"
            style={{ animationDelay: `${index * 160}ms` }}
          />
        ))}
      </span>
      {label && <span>{label}</span>}
    </div>
  );
}
