import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

/** Controls are 44px tall on touch-sized screens and tighten up from the `md` breakpoint. */
export const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground shadow-soft hover:bg-primary/90',
        secondary: 'border border-border bg-surface text-foreground shadow-soft hover:bg-subtle',
        ghost: 'text-muted hover:bg-subtle hover:text-foreground',
        danger: 'bg-danger text-surface shadow-soft hover:bg-danger/90',
      },
      size: {
        sm: 'h-11 px-3 md:h-8',
        md: 'h-11 px-4 md:h-10',
        icon: 'h-11 w-11 md:h-10 md:w-10',
        iconSm: 'h-11 w-11 md:h-8 md:w-8',
      },
    },
    defaultVariants: { variant: 'secondary', size: 'md' },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, type = 'button', ...props }, ref) => {
    const Component = asChild ? Slot : 'button';
    return (
      <Component
        ref={ref}
        type={asChild ? undefined : type}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  },
);
Button.displayName = 'Button';
