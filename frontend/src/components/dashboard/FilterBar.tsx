import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CategoryFilter } from './filters/CategoryFilter';
import { DateRangeFilter } from './filters/DateRangeFilter';
import { cn } from '@/lib/utils';
import type { FilterDefinition } from '@/types';

interface FilterBarProps {
  filters: FilterDefinition[];
  values: Record<string, unknown>;
  onFilterChange: (filterId: string, value: unknown) => void;
  onClearAll: () => void;
}

export function FilterBar({ filters, values, onFilterChange, onClearAll }: FilterBarProps) {
  const activeCount = Object.values(values).filter((v) => v !== undefined).length;

  if (filters.length === 0) return null;

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-2 rounded-lg border border-border bg-background p-2 shadow-sm',
        'animate-in fade-in-0 slide-in-from-top-1 duration-200'
      )}
      data-testid="filter-bar"
    >
      {filters.map((filter) => {
        if (filter.type === 'category') {
          return (
            <CategoryFilter
              key={filter.id}
              filter={filter}
              value={values[filter.id] as string | string[] | undefined}
              onChange={(v) => onFilterChange(filter.id, v)}
            />
          );
        }

        if (filter.type === 'date_range') {
          return (
            <DateRangeFilter
              key={filter.id}
              filter={filter}
              value={values[filter.id] as { start: string; end: string } | undefined}
              onChange={(v) => onFilterChange(filter.id, v)}
            />
          );
        }

        return null;
      })}

      {activeCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs text-muted-foreground hover:text-foreground"
          onClick={onClearAll}
        >
          <X className="mr-1 h-3 w-3" />
          すべてクリア
        </Button>
      )}
    </div>
  );
}
