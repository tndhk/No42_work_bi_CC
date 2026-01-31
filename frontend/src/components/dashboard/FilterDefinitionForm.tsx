import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { datasetsApi } from '@/lib/api';
import type { FilterDefinition } from '@/types';

interface FilterDefinitionFormProps {
  initialValue?: FilterDefinition;
  datasetIds: string[];
  onSubmit: (filter: FilterDefinition) => void;
  onCancel: () => void;
}

export function FilterDefinitionForm({
  initialValue,
  datasetIds,
  onSubmit,
  onCancel,
}: FilterDefinitionFormProps) {
  const [label, setLabel] = useState(initialValue?.label || '');
  const [column, setColumn] = useState(initialValue?.column || '');
  const [type, setType] = useState<'category' | 'date_range'>(
    initialValue?.type || 'category'
  );
  const [multiSelect, setMultiSelect] = useState(initialValue?.multi_select || false);
  const [options, setOptions] = useState<string[]>(initialValue?.options || []);
  const [selectedDatasetId, setSelectedDatasetId] = useState(datasetIds[0] || '');
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [error, setError] = useState('');

  const handleFetchOptions = async () => {
    if (!selectedDatasetId || !column) {
      setError('データセットとカラム名を入力してください');
      return;
    }

    setLoadingOptions(true);
    setError('');

    try {
      const values = await datasetsApi.getColumnValues(selectedDatasetId, column);
      setOptions(values);
    } catch {
      setError('選択肢の取得に失敗しました');
    } finally {
      setLoadingOptions(false);
    }
  };

  const handleSubmit = () => {
    if (!label.trim()) {
      setError('ラベルを入力してください');
      return;
    }
    if (!column.trim()) {
      setError('カラム名を入力してください');
      return;
    }

    const isCategory = type === 'category';
    const filter: FilterDefinition = {
      id: initialValue?.id || crypto.randomUUID(),
      type,
      column: column.trim(),
      label: label.trim(),
      multi_select: isCategory && multiSelect,
      options: isCategory && options.length > 0 ? options : undefined,
    };

    onSubmit(filter);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="filter-label">ラベル</Label>
        <Input
          id="filter-label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="例: 地域"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="filter-type">タイプ</Label>
        <Select value={type} onValueChange={(v) => setType(v as 'category' | 'date_range')}>
          <SelectTrigger id="filter-type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="category">カテゴリ</SelectItem>
            <SelectItem value="date_range">日付範囲</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="filter-column">カラム名</Label>
        <Input
          id="filter-column"
          value={column}
          onChange={(e) => setColumn(e.target.value)}
          placeholder="例: region"
        />
      </div>

      {type === 'category' && (
        <>
          <div className="flex items-center gap-2">
            <Checkbox
              id="filter-multi"
              checked={multiSelect}
              onCheckedChange={(checked) => setMultiSelect(checked === true)}
            />
            <Label htmlFor="filter-multi" className="text-sm font-normal cursor-pointer">
              複数選択を許可
            </Label>
          </div>

          {datasetIds.length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="filter-dataset">データセット</Label>
              <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
                <SelectTrigger id="filter-dataset">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {datasetIds.map((dsId) => (
                    <SelectItem key={dsId} value={dsId}>
                      {dsId}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={handleFetchOptions}
                disabled={loadingOptions || !column}
              >
                {loadingOptions && <Loader2 className="mr-2 h-3 w-3 animate-spin" />}
                選択肢を取得
              </Button>

              {options.length > 0 && (
                <div className="rounded border p-2 text-xs max-h-[120px] overflow-y-auto">
                  <p className="text-muted-foreground mb-1">{options.length} 件の選択肢:</p>
                  {options.map((opt) => (
                    <span
                      key={opt}
                      className="inline-block mr-1 mb-1 rounded bg-secondary px-1.5 py-0.5"
                    >
                      {opt}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          キャンセル
        </Button>
        <Button size="sm" onClick={handleSubmit}>
          {initialValue ? '更新' : '追加'}
        </Button>
      </div>
    </div>
  );
}
