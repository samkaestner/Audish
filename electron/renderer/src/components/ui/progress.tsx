import * as React from 'react';
import { cn } from '../../lib/utils';

export interface ProgressProps
  extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value, ...props }, ref) => {
    if (value === undefined) {
      // Indeterminate progress bar (animated)
      return (
        <div
          ref={ref}
          className={cn(
            'relative h-2 w-full overflow-hidden rounded-full bg-secondary',
            className
          )}
          {...props}
        >
          <div className="absolute h-full w-full bg-primary animate-[progress_1.5s_ease-in-out_infinite]" />
        </div>
      );
    }

    // Determinate progress bar
    return (
      <div
        ref={ref}
        className={cn(
          'relative h-2 w-full overflow-hidden rounded-full bg-secondary',
          className
        )}
        {...props}
      >
        <div
          className="h-full bg-primary transition-all duration-300 ease-in-out"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    );
  }
);
Progress.displayName = 'Progress';

export { Progress };

