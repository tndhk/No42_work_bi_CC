import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDataset, useDatasetPreview } from '@/hooks';
import { SchemaChangeWarningDialog } from '@/components/datasets/SchemaChangeWarningDialog';
import { SchemaTable } from '@/components/dataset/SchemaTable';
import { PreviewTable } from '@/components/dataset/PreviewTable';
import { useReimportFlow } from '@/hooks/use-reimport-flow';

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dataset, isLoading } = useDataset(id!);
  const { data: preview, isLoading: previewLoading } = useDatasetPreview(id!, 100);

  const {
    dialogOpen,
    changes,
    isPending,
    handleReimport,
    handleConfirm,
    handleCancel,
  } = useReimportFlow({ datasetId: id! });

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dataset) {
    return <div className="text-center py-12 text-muted-foreground">データセットが見つかりません</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/datasets')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {dataset.source_type === 's3_csv' && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleReimport}
            disabled={isPending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            再取り込み
          </Button>
        )}
        <div>
          <h1 className="text-2xl font-bold">{dataset.name}</h1>
          <p className="text-sm text-muted-foreground">
            {dataset.row_count.toLocaleString()}行 / {dataset.column_count}列
          </p>
        </div>
      </div>

      <SchemaTable columns={dataset.columns} />

      <PreviewTable preview={preview} isLoading={previewLoading} />

      <SchemaChangeWarningDialog
        open={dialogOpen}
        changes={changes}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </div>
  );
}
