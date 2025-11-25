import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'neo-button disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none',
          variant === 'outline' && 'bg-transparent border-accent text-accent hover:bg-accent/10',
          variant === 'ghost' && 'bg-transparent border-transparent hover:bg-accent/10',
          size === 'sm' && 'px-4 py-2 text-sm',
          size === 'lg' && 'px-8 py-4 text-lg',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button };

