import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import type { FilterDefinition } from '@/types';

interface CategoryFilterProps {
  filter: FilterDefinition;
  value: string | string[] | undefined;
  onChange: (value: string | string[] | undefined) => void;
}

export function CategoryFilter({ filter, value, onChange }: CategoryFilterProps) {
  if (filter.multi_select) {
    return (
      <MultiSelectFilter
        filter={filter}
        value={Array.isArray(value) ? value : value ? [value] : []}
        onChange={onChange}
      />
    );
  }

  return (
    <SingleSelectFilter
      filter={filter}
      value={typeof value === 'string' ? value : undefined}
      onChange={onChange}
    />
  );
}

function SingleSelectFilter({
  filter,
  value,
  onChange,
}: {
  filter: FilterDefinition;
  value: string | undefined;
  onChange: (value: string | string[] | undefined) => void;
}) {
  const options = filter.options || [];

  return (
    <div className="flex items-center gap-1">
      <Select
        value={value || ''}
        onValueChange={(v) => onChange(v || undefined)}
      >
        <SelectTrigger className="h-8 w-[180px] text-xs" aria-label={filter.label}>
          <SelectValue placeholder={filter.label} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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

function MultiSelectFilter({
  filter,
  value,
  onChange,
}: {
  filter: FilterDefinition;
  value: string[];
  onChange: (value: string | string[] | undefined) => void;
}) {
  const [open, setOpen] = useState(false);
  const options = filter.options || [];

  const handleToggle = (option: string) => {
    const newValue = value.includes(option)
      ? value.filter((v) => v !== option)
      : [...value, option];
    onChange(newValue.length > 0 ? newValue : undefined);
  };

  function getDisplayText(): string {
    if (value.length === 0) return filter.label;
    if (value.length === 1) return value[0];
    return `${value[0]} (+${value.length - 1})`;
  }
  const displayText = getDisplayText();

  return (
    <div className="flex items-center gap-1">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-[180px] justify-start text-xs font-normal"
            aria-label={filter.label}
          >
            <span className="truncate">{displayText}</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-2" align="start">
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {options.map((option) => (
              <label
                key={option}
                className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent"
              >
                <Checkbox
                  checked={value.includes(option)}
                  onCheckedChange={() => handleToggle(option)}
                />
                <span className="truncate">{option}</span>
              </label>
            ))}
          </div>
        </PopoverContent>
      </Popover>
      {value.length > 0 && (
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
