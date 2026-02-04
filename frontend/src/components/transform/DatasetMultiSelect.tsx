import type { Dataset } from '@/types';

interface DatasetMultiSelectProps {
  datasets: Dataset[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function DatasetMultiSelect({ datasets, selectedIds, onChange }: DatasetMultiSelectProps) {
  const handleToggle = (datasetId: string) => {
    if (selectedIds.includes(datasetId)) {
      onChange(selectedIds.filter((id) => id !== datasetId));
    } else {
      onChange([...selectedIds, datasetId]);
    }
  };

  if (datasets.length === 0) {
    return <p className="text-sm text-muted-foreground">データセットがありません</p>;
  }

  return (
    <div className="space-y-2 max-h-60 overflow-y-auto">
      {datasets.map((dataset) => (
        <label
          key={dataset.dataset_id}
          className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-muted cursor-pointer"
        >
          <input
            type="checkbox"
            checked={selectedIds.includes(dataset.dataset_id)}
            onChange={() => handleToggle(dataset.dataset_id)}
            className="rounded border-input"
          />
          <span className="text-sm">{dataset.name}</span>
        </label>
      ))}
    </div>
  );
}
