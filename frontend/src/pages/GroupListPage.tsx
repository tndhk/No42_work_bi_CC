import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Plus, Trash2, Eye } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { GroupCreateDialog } from '@/components/group/GroupCreateDialog';
import { GroupDetailPanel } from '@/components/group/GroupDetailPanel';
import { useGroups, useDeleteGroup } from '@/hooks';

export function GroupListPage() {
  const { data: groups, isLoading } = useGroups();
  const deleteMutation = useDeleteGroup();

  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">グループ管理</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          新規作成
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>名前</TableHead>
            <TableHead>作成日時</TableHead>
            <TableHead className="w-[120px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {groups?.map((group) => (
            <TableRow key={group.id}>
              <TableCell className="font-mono text-sm">{group.id}</TableCell>
              <TableCell className="font-medium">{group.name}</TableCell>
              <TableCell>{new Date(group.created_at).toLocaleString('ja-JP')}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedGroupId(group.id)}
                    aria-label="詳細"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteTarget(group.id)}
                    aria-label="削除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
          {groups?.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                グループがありません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {selectedGroupId && (
        <GroupDetailPanel
          groupId={selectedGroupId}
          onClose={() => setSelectedGroupId(null)}
        />
      )}

      <GroupCreateDialog open={createOpen} onOpenChange={setCreateOpen} />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="グループの削除"
        description="このグループを削除しますか？この操作は取り消せません。"
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
