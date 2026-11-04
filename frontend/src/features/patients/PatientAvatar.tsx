import { cn } from '@/lib/cn';
import { initials } from '@/lib/format';

interface PatientAvatarProps {
  name: string;
  className?: string;
}

export function PatientAvatar({ name, className }: PatientAvatarProps) {
  return (
    <span
      aria-hidden
      className={cn(
        'grid size-10 shrink-0 place-items-center rounded-full bg-primary-soft text-sm font-semibold text-primary-text',
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}
