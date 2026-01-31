import { CalendarIcon, X } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import type { DateRange } from 'react-day-picker';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import type { FilterDefinition } from '@/types';

interface DateRangeValue {
  start: string;
  end: string;
}

interface DateRangeFilterProps {
  filter: FilterDefinition;
  value: DateRangeValue | undefined;
  onChange: (value: DateRangeValue | undefined) => void;
}

export function DateRangeFilter({ filter, value, onChange }: DateRangeFilterProps) {
  const dateRange: DateRange | undefined = value
    ? {
        from: parseISO(value.start),
        to: parseISO(value.end),
      }
    : undefined;

  const handleSelect = (range: DateRange | undefined) => {
    if (range?.from && range?.to) {
      onChange({
        start: format(range.from, 'yyyy-MM-dd'),
        end: format(range.to, 'yyyy-MM-dd'),
      });
    } else if (range?.from) {
      onChange({
        start: format(range.from, 'yyyy-MM-dd'),
        end: format(range.from, 'yyyy-MM-dd'),
      });
    }
  };

  const displayText = value
    ? `${format(parseISO(value.start), 'yyyy/MM/dd')} - ${format(parseISO(value.end), 'yyyy/MM/dd')}`
    : filter.label;

  return (
    <div className="flex items-center gap-1">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className={cn(
              'h-8 w-[240px] justify-start text-xs font-normal',
              !value && 'text-muted-foreground'
            )}
            aria-label={filter.label}
          >
            <CalendarIcon className="mr-2 h-3 w-3" />
            <span className="truncate">{displayText}</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            selected={dateRange}
            onSelect={handleSelect}
            numberOfMonths={2}
            locale={ja}
          />
        </PopoverContent>
      </Popover>
      {value && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onChange(undefined)}
          aria-label={`${filter.label}をクリア`}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}
