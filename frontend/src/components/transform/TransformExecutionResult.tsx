import { Link } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import type { TransformExecuteResponse } from '@/types';

interface TransformExecutionResultProps {
  result: TransformExecuteResponse | null;
}

export function TransformExecutionResult({ result }: TransformExecutionResultProps) {
  if (!result) return null;

  return (
    <div className="space-y-3 rounded-md border p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">行数</span>
        <span className="text-sm font-medium">{result.row_count}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">実行時間</span>
        <span className="text-sm font-medium">{result.execution_time_ms}ms</span>
      </div>
      <div>
        <span className="text-sm text-muted-foreground">カラム</span>
        <div className="mt-1 flex flex-wrap gap-1">
          {result.column_names.map((col) => (
            <span
              key={col}
              className="rounded bg-muted px-2 py-0.5 text-xs"
            >
              {col}
            </span>
          ))}
        </div>
      </div>
      <div className="pt-2 border-t">
        <Link
          to={`/datasets/${result.output_dataset_id}`}
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ExternalLink className="h-3 w-3" />
          出力データセットを表示
        </Link>
      </div>
    </div>
  );
}
