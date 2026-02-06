import { BarChart3, LineChart, PieChart, Table, Hash, Grid3x3 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChartType } from '@/types/card';
import { chartTemplates } from '@/lib/chart-templates';

interface ChartTypePickerProps {
  value?: ChartType;
  onSelect: (chartType: ChartType) => void;
  disabled?: boolean;
}

const chartIcons: Record<ChartType, React.ComponentType<{ className?: string }>> = {
  'summary-number': Hash,
  bar: BarChart3,
  line: LineChart,
  pie: PieChart,
  table: Table,
  pivot: Grid3x3,
};

export function ChartTypePicker({ value, onSelect, disabled }: ChartTypePickerProps) {
  const chartTypes = Object.values(chartTemplates);

  return (
    <div className="grid grid-cols-3 gap-3">
      {chartTypes.map((template) => {
        const Icon = chartIcons[template.type];
        const isSelected = value === template.type;

        return (
          <button
            key={template.type}
            type="button"
            onClick={() => !disabled && onSelect(template.type)}
            disabled={disabled}
            className={cn(
              'flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all',
              'hover:border-primary hover:bg-primary/5',
              isSelected
                ? 'border-primary bg-primary/10'
                : 'border-border bg-card',
              disabled && 'opacity-50 cursor-not-allowed',
            )}
          >
            <Icon className={cn('w-6 h-6 mb-2', isSelected ? 'text-primary' : 'text-muted-foreground')} />
            <span className={cn('text-sm font-medium', isSelected ? 'text-primary' : 'text-foreground')}>
              {template.name}
            </span>
            <span className="text-xs text-muted-foreground mt-1">{template.description}</span>
          </button>
        );
      })}
    </div>
  );
}
