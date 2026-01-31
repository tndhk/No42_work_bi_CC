import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Pagination } from '@/components/common/Pagination';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { useCards, useDeleteCard } from '@/hooks';

export function CardListPage() {
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const { data, isLoading } = useCards({ limit, offset });
  const deleteMutation = useDeleteCard();
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">カード</h1>
        <Button onClick={() => navigate('/cards/new')}>
          <Plus className="h-4 w-4 mr-2" />
          新規作成
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>名前</TableHead>
            <TableHead>データセット</TableHead>
            <TableHead>オーナー</TableHead>
            <TableHead>作成日時</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.data.map((card) => (
            <TableRow key={card.card_id}>
              <TableCell className="font-medium">{card.name}</TableCell>
              <TableCell>{card.dataset?.name || '-'}</TableCell>
              <TableCell>{card.owner.name}</TableCell>
              <TableCell>{new Date(card.created_at).toLocaleString('ja-JP')}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => navigate(`/cards/${card.card_id}`)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(card.card_id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
          {data?.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                カードがありません
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
        title="カードの削除"
        description="このカードを削除しますか？この操作は取り消せません。"
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
