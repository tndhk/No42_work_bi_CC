import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import type { FilterDefinition, FilterView } from '@/types';

interface FilterBarProps {
  filters: FilterDefinition[];
  values: Record<string, unknown>;
  filterViews: FilterView[];
  selectedViewId?: string;
  onFilterChange: (filterId: string, value: unknown) => void;
  onClearAll: () => void;
  onSelectView: (view: FilterView) => void;
  onSaveView: (name: string, options?: { is_shared: boolean }) => void | Promise<void>;
  permission?: 'owner' | 'editor' | 'viewer';
}

export function FilterBar({ 
  filters, 
  values, 
  filterViews,
  selectedViewId,
  onFilterChange, 
  onClearAll,
  onSelectView,
  onSaveView,
  permission,
}: FilterBarProps) {
  const activeCount = Object.values(values).filter((v) => v !== undefined).length;
  const selectedView = filterViews.find((v) => v.id === selectedViewId);

  if (filters.length === 0) return null;

  // Get active filter pills
  const activeFilterPills: Array<{ filter: FilterDefinition; value: string | string[] }> = [];
  filters.forEach((filter) => {
    const filterValue = values[filter.id];
    if (filterValue !== undefined) {
      if (filter.type === 'category') {
        if (Array.isArray(filterValue)) {
          activeFilterPills.push({ filter, value: filterValue });
        } else if (typeof filterValue === 'string') {
          activeFilterPills.push({ filter, value: [filterValue] });
        }
      } else if (filter.type === 'date_range' && typeof filterValue === 'object' && filterValue !== null) {
        const dateValue = filterValue as { start: string; end: string };
        activeFilterPills.push({ 
          filter, 
          value: [`${dateValue.start} - ${dateValue.end}`] 
        });
      }
    }
  });

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-2 bg-blue-600 text-white rounded-md',
        'animate-in fade-in-0 slide-in-from-top-1 duration-200'
      )}
      data-testid="filter-bar"
    >
      {/* Filter View Selector */}
      <Select
        value={selectedViewId || ''}
        onValueChange={(value) => {
          const view = filterViews.find((v) => v.id === value);
          if (view) onSelectView(view);
        }}
      >
        <SelectTrigger className="h-8 w-[140px] bg-blue-700 border-blue-500 text-white text-xs">
          <SelectValue placeholder="DEF (DEFAULT)">
            {selectedView ? selectedView.name : 'DEF (DEFAULT)'}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {filterViews.map((view) => (
            <SelectItem key={view.id} value={view.id}>
              {view.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Active Filter Pills */}
      <div className="flex items-center gap-2 flex-1 overflow-x-auto">
        {activeFilterPills.map(({ filter, value }) => {
          const displayValues = Array.isArray(value) ? value : [value];
          return displayValues.map((val, idx) => (
            <Badge
              key={`${filter.id}-${idx}`}
              className="bg-blue-500 hover:bg-blue-400 text-white px-2 py-1 text-xs flex items-center gap-1"
            >
              <span>{filter.label}: {val}</span>
              <button
                onClick={() => {
                  if (filter.type === 'category') {
                    if (filter.multi_select && Array.isArray(values[filter.id])) {
                      const currentValues = values[filter.id] as string[];
                      const newValues = currentValues.filter((v) => v !== val);
                      onFilterChange(filter.id, newValues.length > 0 ? newValues : undefined);
                    } else {
                      onFilterChange(filter.id, undefined);
                    }
                  } else {
                    onFilterChange(filter.id, undefined);
                  }
                }}
                className="ml-1 hover:bg-blue-600 rounded-full p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ));
        })}
      </div>

      {/* Save Filters Button */}
      {permission !== 'viewer' && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs text-white hover:bg-blue-700"
          onClick={() => {
            const name = prompt('フィルター名を入力してください:');
            if (name) {
              onSaveView(name.trim(), { is_shared: permission === 'owner' });
            }
          }}
        >
          SAVE FILTERS
        </Button>
      )}

      {/* Clear All */}
      {activeCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs text-white hover:bg-blue-700"
          onClick={onClearAll}
        >
          <X className="mr-1 h-3 w-3" />
          すべてクリア
        </Button>
      )}
    </div>
  );
}
