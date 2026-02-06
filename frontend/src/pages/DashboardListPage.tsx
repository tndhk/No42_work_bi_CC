import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, Eye, Pencil, Trash2, MoreVertical, LayoutDashboard } from 'lucide-react';
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

      {data?.data.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          ダッシュボードがありません
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {data?.data.map((dashboard) => (
            <Card
              key={dashboard.dashboard_id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/dashboards/${dashboard.dashboard_id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <LayoutDashboard className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    <CardTitle className="text-lg truncate">{dashboard.name}</CardTitle>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/dashboards/${dashboard.dashboard_id}`);
                      }}>
                        <Eye className="h-4 w-4 mr-2" />
                        表示
                      </DropdownMenuItem>
                      {dashboard.my_permission !== 'viewer' && (
                        <DropdownMenuItem onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/dashboards/${dashboard.dashboard_id}/edit`);
                        }}>
                          <Pencil className="h-4 w-4 mr-2" />
                          編集
                        </DropdownMenuItem>
                      )}
                      {(!dashboard.my_permission || dashboard.my_permission === 'owner') && (
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(dashboard.dashboard_id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          削除
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">カード数</span>
                    <span className="font-medium">{dashboard.card_count}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">オーナー</span>
                    <span className="font-medium truncate ml-2">{dashboard.owner.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground text-sm">権限</span>
                    {dashboard.my_permission && (
                      <Badge variant={dashboard.my_permission === 'owner' ? 'default' : 'secondary'}>
                        {dashboard.my_permission}
                      </Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    更新: {new Date(dashboard.updated_at).toLocaleDateString('ja-JP')}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

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
