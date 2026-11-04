import * as AlertDialog from '@radix-ui/react-alert-dialog';
import type { ReactNode } from 'react';
import { buttonVariants } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  pending?: boolean;
  onConfirm: () => void;
}

/** Destructive confirmation; Radix AlertDialog focuses "Cancel" first and traps focus. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  pending = false,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 z-[60] flex animate-fade-in items-center justify-center bg-[hsl(var(--shadow)/0.5)] p-4 backdrop-blur-[2px]">
          <AlertDialog.Content className="w-full max-w-md animate-pop-in space-y-4 rounded-lg border border-border bg-surface p-5 shadow-float">
            <div className="space-y-2">
              <AlertDialog.Title className="text-base font-semibold">{title}</AlertDialog.Title>
              <AlertDialog.Description className="text-sm text-muted">
                {description}
              </AlertDialog.Description>
            </div>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <AlertDialog.Cancel className={buttonVariants({ variant: 'secondary' })}>
                Cancel
              </AlertDialog.Cancel>
              <AlertDialog.Action
                className={buttonVariants({ variant: 'danger' })}
                disabled={pending}
                onClick={(event) => {
                  event.preventDefault();
                  onConfirm();
                }}
              >
                {pending && <Spinner />}
                {confirmLabel}
              </AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Overlay>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
