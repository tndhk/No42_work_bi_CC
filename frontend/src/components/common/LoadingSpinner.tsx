import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const dotSizeClasses = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2 w-2',
  lg: 'h-3 w-3',
};

const gapClasses = {
  sm: 'gap-1',
  md: 'gap-1.5',
  lg: 'gap-2',
};

export function LoadingSpinner({ className, size = 'md' }: LoadingSpinnerProps) {
  return (
    <div
      className={cn('flex items-center', gapClasses[size], className)}
      role="status"
      aria-label="Loading"
    >
      {[0, 150, 300].map((delay) => (
        <div
          key={delay}
          className={cn(
            'rounded-full bg-primary animate-pulse-gentle',
            dotSizeClasses[size]
          )}
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );
}
