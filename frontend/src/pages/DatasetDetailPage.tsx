import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDataset, useDatasetPreview, useReimportDryRun, useReimportDataset } from '@/hooks';
import { SchemaChangeWarningDialog } from '@/components/datasets/SchemaChangeWarningDialog';
import type { SchemaChange } from '@/types/reimport';

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dataset, isLoading } = useDataset(id!);
  const { data: preview, isLoading: previewLoading } = useDatasetPreview(id!, 100);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [changes, setChanges] = useState<SchemaChange[]>([]);

  const { mutateAsync: dryRunMutateAsync, isPending: isDryRunPending } = useReimportDryRun();
  const { mutateAsync: reimportMutateAsync, isPending: isReimportPending } = useReimportDataset();

  const isPending = isDryRunPending || isReimportPending;

  useEffect(() => {
    const rowsIsArray = Array.isArray(preview?.rows);
    const firstRow = rowsIsArray ? preview?.rows?.[0] : undefined;
    const firstRowType = firstRow === null ? 'null' : Array.isArray(firstRow) ? 'array' : typeof firstRow;
    const firstRowKeys = firstRow && typeof firstRow === 'object' && !Array.isArray(firstRow) ? Object.keys(firstRow) : null;
    const columnsLength = Array.isArray(preview?.columns) ? preview.columns.length : null;

    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/78a5a759-9581-4a4e-9ccc-07469b56efc6', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sessionId: 'debug-session', runId: 'pre-fix', hypothesisId: 'A', location: 'DatasetDetailPage.useEffect.preview', message: 'preview effect triggered', data: { hasPreview: Boolean(preview), rowsIsArray, columnsLength }, timestamp: Date.now() }) }).catch(() => {});
    // #endregion
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/78a5a759-9581-4a4e-9ccc-07469b56efc6', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sessionId: 'debug-session', runId: 'pre-fix', hypothesisId: 'B', location: 'DatasetDetailPage.useEffect.preview', message: 'preview first row shape', data: { rowsIsArray, firstRowType, firstRowKeys, columnsLength }, timestamp: Date.now() }) }).catch(() => {});
    // #endregion
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/78a5a759-9581-4a4e-9ccc-07469b56efc6', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sessionId: 'debug-session', runId: 'pre-fix', hypothesisId: 'C', location: 'DatasetDetailPage.useEffect.preview', message: 'preview row counts', data: { rowsLength: rowsIsArray ? preview?.rows?.length ?? null : null, previewRows: preview?.preview_rows ?? null, totalRows: preview?.total_rows ?? null }, timestamp: Date.now() }) }).catch(() => {});
    // #endregion
  }, [preview]);

  const handleReimport = async () => {
    const result = await dryRunMutateAsync(id!);
    if (result.has_schema_changes) {
      setChanges(result.changes);
      setDialogOpen(true);
    } else {
      await reimportMutateAsync({ datasetId: id!, force: false });
    }
  };

  const handleConfirm = async () => {
    await reimportMutateAsync({ datasetId: id!, force: true });
    setDialogOpen(false);
  };

  const handleCancel = () => {
    setDialogOpen(false);
    setChanges([]);
  };

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

      <Card>
        <CardHeader>
          <CardTitle>スキーマ</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>カラム名</TableHead>
                <TableHead>型</TableHead>
                <TableHead>NULL許容</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dataset.columns.map((col) => (
                <TableRow key={col.name}>
                  <TableCell className="font-mono">{col.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{col.data_type}</Badge>
                  </TableCell>
                  <TableCell>{col.nullable ? 'Yes' : 'No'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>プレビュー</CardTitle>
        </CardHeader>
        <CardContent>
          {previewLoading ? (
            <div className="flex justify-center py-4"><LoadingSpinner /></div>
          ) : preview ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {preview.columns.map((col) => (
                      <TableHead key={col}>{col}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {preview.rows.slice(0, 20).map((row, i) => (
                    <TableRow key={i}>
                      {row.map((cell, j) => (
                        <TableCell key={j} className="font-mono text-sm">
                          {cell === null ? <span className="text-muted-foreground">NULL</span> : String(cell)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <p className="text-sm text-muted-foreground mt-2">
                {preview.total_rows.toLocaleString()}件中 {Math.min(20, preview.preview_rows)}件を表示
              </p>
            </div>
          ) : (
            <p className="text-muted-foreground">プレビューデータがありません</p>
          )}
        </CardContent>
      </Card>

      <SchemaChangeWarningDialog
        open={dialogOpen}
        changes={changes}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </div>
  );
}
