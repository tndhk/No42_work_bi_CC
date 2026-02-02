import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CategoryFilter } from './filters/CategoryFilter';
import { DateRangeFilter } from './filters/DateRangeFilter';
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
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card/80 backdrop-blur-sm shadow-sm p-3" data-testid="filter-bar">
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
          className="h-8 text-xs text-muted-foreground"
          onClick={onClearAll}
        >
          <X className="mr-1 h-3 w-3" />
          クリア
        </Button>
      )}
    </div>
  );
}
