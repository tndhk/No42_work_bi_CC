import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, Eye, Pencil, Trash2 } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Pagination } from '@/components/common/Pagination';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { useDashboards, useCreateDashboard, useDeleteDashboard } from '@/hooks';

export function DashboardListPage() {
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const { data, isLoading } = useDashboards({ limit, offset });
  const createMutation = useCreateDashboard();
  const deleteMutation = useDeleteDashboard();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const handleCreate = () => {
    if (!newName.trim()) return;
    createMutation.mutate({ name: newName }, {
      onSuccess: (dashboard) => {
        setCreateOpen(false);
        setNewName('');
        navigate(`/dashboards/${dashboard.dashboard_id}/edit`);
      },
    });
  };

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">ダッシュボード</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          新規作成
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>名前</TableHead>
            <TableHead>カード数</TableHead>
            <TableHead>オーナー</TableHead>
            <TableHead>権限</TableHead>
            <TableHead>更新日時</TableHead>
            <TableHead className="w-[120px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.data.map((dashboard) => (
            <TableRow key={dashboard.dashboard_id}>
              <TableCell className="font-medium">{dashboard.name}</TableCell>
              <TableCell>{dashboard.card_count}</TableCell>
              <TableCell>{dashboard.owner.name}</TableCell>
              <TableCell>
                {dashboard.my_permission && (
                  <Badge variant={dashboard.my_permission === 'owner' ? 'default' : 'secondary'}>
                    {dashboard.my_permission}
                  </Badge>
                )}
              </TableCell>
              <TableCell>{new Date(dashboard.updated_at).toLocaleString('ja-JP')}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => navigate(`/dashboards/${dashboard.dashboard_id}`)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  {dashboard.my_permission !== 'viewer' && (
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/dashboards/${dashboard.dashboard_id}/edit`)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                  )}
                  {(!dashboard.my_permission || dashboard.my_permission === 'owner') && (
                    <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(dashboard.dashboard_id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
          {data?.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                ダッシュボードがありません
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

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新規ダッシュボード</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="dashboard-name">名前</Label>
              <Input
                id="dashboard-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="ダッシュボード名"
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>キャンセル</Button>
            <Button onClick={handleCreate} disabled={!newName.trim() || createMutation.isPending}>
              作成
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="ダッシュボードの削除"
        description="このダッシュボードを削除しますか？この操作は取り消せません。"
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
