import { forwardRef } from 'react';
import { Button, type ButtonProps } from './button';

interface IconButtonProps extends Omit<ButtonProps, 'children' | 'aria-label'> {
  /** Accessible name; also shown as the native tooltip. */
  label: string;
  icon: React.ReactNode;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, icon, variant = 'ghost', size = 'icon', ...props }, ref) => (
    <Button ref={ref} variant={variant} size={size} aria-label={label} title={label} {...props}>
      {icon}
    </Button>
  ),
);
IconButton.displayName = 'IconButton';
