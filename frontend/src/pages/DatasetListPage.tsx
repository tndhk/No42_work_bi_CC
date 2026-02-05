import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Plus, Eye, Trash2 } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Pagination } from '@/components/common/Pagination';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { useDatasets, useDeleteDataset } from '@/hooks';

export function DatasetListPage() {
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const { data, isLoading } = useDatasets({ limit, offset });
  const deleteMutation = useDeleteDataset();
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">データセット</h1>
        <Button onClick={() => navigate('/datasets/import')}>
          <Plus className="h-4 w-4 mr-2" />
          インポート
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>名前</TableHead>
            <TableHead>ソース</TableHead>
            <TableHead>行数</TableHead>
            <TableHead>列数</TableHead>
            <TableHead>オーナー</TableHead>
            <TableHead>作成日時</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.data.map((dataset) => (
            <TableRow key={dataset.id}>
              <TableCell className="font-medium">{dataset.name}</TableCell>
              <TableCell>{dataset.source_type}</TableCell>
              <TableCell>{dataset.row_count.toLocaleString()}</TableCell>
              <TableCell>{dataset.column_count}</TableCell>
              <TableCell>{dataset.owner_id ?? '-'}</TableCell>
              <TableCell>{new Date(dataset.created_at).toLocaleString('ja-JP')}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => navigate(`/datasets/${dataset.id}`)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(dataset.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
          {data?.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                データセットがありません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {data?.pagination && (
        <Pagination
          total={data.pagination.total}
          limit={data.pagination.limit}
          offset={data.pagination.offset}
          onPageChange={setOffset}
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="データセットの削除"
        description="このデータセットを削除しますか？この操作は取り消せません。"
        confirmLabel="削除"
        variant="destructive"
        onConfirm={() => {
          if (deleteTarget) {
            deleteMutation.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
          }
        }}
      />
    </div>
  );
}
