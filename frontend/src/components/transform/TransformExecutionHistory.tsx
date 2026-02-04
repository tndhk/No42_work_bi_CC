import { useTransformExecutions } from '@/hooks';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import type { TransformExecution } from '@/types';

const STATUS_STYLES: Record<string, string> = {
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  running: 'bg-yellow-100 text-yellow-800',
};

interface TransformExecutionHistoryProps {
  transformId: string;
}

export function TransformExecutionHistory({ transformId }: TransformExecutionHistoryProps) {
  const { data, isLoading } = useTransformExecutions(transformId);

  if (isLoading) return <LoadingSpinner size="sm" />;
  if (!data?.data?.length) return <p className="text-sm text-muted-foreground">実行履歴がありません</p>;

  return (
    <div className="space-y-2">
      {data.data.map((execution: TransformExecution) => (
        <div key={execution.execution_id} className="rounded-md border p-3 space-y-1">
          <div className="flex items-center gap-2">
            {/* Status badge */}
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              STATUS_STYLES[execution.status] ?? STATUS_STYLES.running
            }`}>
              {execution.status}
            </span>
            {/* Start time */}
            <span className="text-sm text-muted-foreground">
              {new Date(execution.started_at).toLocaleString('ja-JP')}
            </span>
            {/* Duration */}
            {execution.duration_ms != null && (
              <span className="text-sm text-muted-foreground">
                {(execution.duration_ms / 1000).toFixed(1)}s
              </span>
            )}
            {/* Row count */}
            {execution.output_row_count != null && (
              <span className="text-sm text-muted-foreground">
                {execution.output_row_count}行
              </span>
            )}
          </div>
          <div className="text-xs text-muted-foreground">
            {execution.triggered_by === 'manual' ? '手動実行' : 'スケジュール実行'}
          </div>
          {/* Error message for failed */}
          {execution.error && (
            <div className="text-xs text-red-600 mt-1">
              {execution.error}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
