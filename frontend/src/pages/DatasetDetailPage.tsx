import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDataset, useDatasetPreview } from '@/hooks';

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dataset, isLoading } = useDataset(id!);
  const { data: preview, isLoading: previewLoading } = useDatasetPreview(id!, 100);

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
              {dataset.schema.map((col) => (
                <TableRow key={col.name}>
                  <TableCell className="font-mono">{col.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{col.type}</Badge>
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
    </div>
  );
}
