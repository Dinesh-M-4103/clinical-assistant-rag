import * as DialogPrimitive from '@radix-ui/react-dialog';
import { cva, type VariantProps } from 'class-variance-authority';
import { X } from 'lucide-react';
import type { ComponentPropsWithoutRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';
import { restoreOpener } from '@/lib/focus';

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

const overlayVariants = cva(
  'fixed inset-0 z-50 flex animate-fade-in bg-[hsl(var(--shadow)/0.5)] backdrop-blur-[2px]',
  {
    variants: {
      placement: {
        center: 'items-center justify-center p-4',
        right: 'justify-end',
        left: 'justify-start',
      },
    },
    defaultVariants: { placement: 'center' },
  },
);

const contentVariants = cva(
  'relative flex max-h-full w-full flex-col overflow-hidden border-border bg-surface shadow-float',
  {
    variants: {
      placement: {
        center: 'max-w-lg animate-pop-in rounded-lg border',
        right: 'h-full max-w-[26rem] animate-slide-in-right border-l',
        left: 'h-full max-w-[20rem] animate-slide-in-left border-r',
      },
    },
    defaultVariants: { placement: 'center' },
  },
);

interface DialogContentProps
  extends
    ComponentPropsWithoutRef<typeof DialogPrimitive.Content>,
    VariantProps<typeof contentVariants> {
  /** Hide the corner close button when the dialog supplies its own header controls. */
  hideClose?: boolean;
}

/** Radix dialog (focus trap, Esc, scroll lock) rendered as a centered modal or an edge sheet. */
export function DialogContent({
  className,
  children,
  placement,
  hideClose = false,
  onCloseAutoFocus,
  ...props
}: DialogContentProps) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className={overlayVariants({ placement })}>
        <DialogPrimitive.Content
          className={cn(contentVariants({ placement }), className)}
          onCloseAutoFocus={(event) => {
            onCloseAutoFocus?.(event);
            if (!event.defaultPrevented) restoreOpener(event);
          }}
          {...props}
        >
          {children}
          {!hideClose && (
            <DialogPrimitive.Close
              aria-label="Close"
              className="absolute right-3 top-3 grid size-11 place-items-center rounded-md text-muted transition-colors hover:bg-subtle hover:text-foreground md:size-8"
            >
              <X className="size-4" />
            </DialogPrimitive.Close>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Overlay>
    </DialogPrimitive.Portal>
  );
}

export function DialogHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-1 px-5 pb-3 pr-14 pt-5', className)} {...props} />;
}

export function DialogBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('min-h-0 flex-1 overflow-y-auto px-5 py-3', className)} {...props} />;
}

export function DialogFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex flex-col-reverse gap-2 border-t border-border px-5 py-4 sm:flex-row sm:justify-end',
        className,
      )}
      {...props}
    />
  );
}

export function DialogTitle({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn('text-base font-semibold leading-snug', className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Description>) {
  return <DialogPrimitive.Description className={cn('text-sm text-muted', className)} {...props} />;
}
