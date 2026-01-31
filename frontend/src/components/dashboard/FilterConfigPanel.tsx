import { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { FilterDefinitionForm } from './FilterDefinitionForm';
import type { FilterDefinition } from '@/types';

interface FilterConfigPanelProps {
  filters: FilterDefinition[];
  onFiltersChange: (filters: FilterDefinition[]) => void;
  datasetIds: string[];
}

export function FilterConfigPanel({
  filters,
  onFiltersChange,
  datasetIds,
}: FilterConfigPanelProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingFilter, setEditingFilter] = useState<FilterDefinition | undefined>();

  const handleAdd = () => {
    setEditingFilter(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (filter: FilterDefinition) => {
    setEditingFilter(filter);
    setDialogOpen(true);
  };

  const handleDelete = (filterId: string) => {
    onFiltersChange(filters.filter((f) => f.id !== filterId));
  };

  const handleSubmit = (filter: FilterDefinition) => {
    if (editingFilter) {
      onFiltersChange(filters.map((f) => (f.id === filter.id ? filter : f)));
    } else {
      onFiltersChange([...filters, filter]);
    }
    setDialogOpen(false);
    setEditingFilter(undefined);
  };

  return (
    <div className="space-y-3 rounded-lg border p-4" data-testid="filter-config-panel">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">フィルタ設定</h3>
        <Button variant="outline" size="sm" onClick={handleAdd}>
          <Plus className="h-3 w-3 mr-1" />
          追加
        </Button>
      </div>

      {filters.length === 0 ? (
        <p className="text-sm text-muted-foreground py-2">
          フィルタが設定されていません
        </p>
      ) : (
        <div className="space-y-2">
          {filters.map((filter) => (
            <div
              key={filter.id}
              className="flex items-center justify-between rounded border px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px]">
                  {filter.type === 'category' ? 'カテゴリ' : '日付範囲'}
                </Badge>
                <span className="text-sm font-medium">{filter.label}</span>
                <span className="text-xs text-muted-foreground">{filter.column}</span>
                {filter.multi_select && (
                  <Badge variant="secondary" className="text-[10px]">複数</Badge>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => handleEdit(filter)}
                  aria-label={`${filter.label}を編集`}
                >
                  <Pencil className="h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-destructive"
                  onClick={() => handleDelete(filter.id)}
                  aria-label={`${filter.label}を削除`}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingFilter ? 'フィルタを編集' : 'フィルタを追加'}
            </DialogTitle>
          </DialogHeader>
          <FilterDefinitionForm
            initialValue={editingFilter}
            datasetIds={datasetIds}
            onSubmit={handleSubmit}
            onCancel={() => setDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
