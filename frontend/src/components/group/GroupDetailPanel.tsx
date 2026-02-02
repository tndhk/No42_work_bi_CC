import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { X, UserPlus, Trash2 } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { MemberAddDialog } from '@/components/group/MemberAddDialog';
import { useGroup, useRemoveMember } from '@/hooks';

interface GroupDetailPanelProps {
  groupId: string;
  onClose: () => void;
}

export function GroupDetailPanel({ groupId, onClose }: GroupDetailPanelProps) {
  const { data: group, isLoading } = useGroup(groupId);
  const removeMutation = useRemoveMember();

  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [removeTarget, setRemoveTarget] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (!group) {
    return null;
  }

  return (
    <div className="border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{group.name}</h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">メンバー</h3>
        <Button size="sm" onClick={() => setAddMemberOpen(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          メンバー追加
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ユーザーID</TableHead>
            <TableHead>追加日時</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {group.members.map((member) => (
            <TableRow key={member.user_id}>
              <TableCell>{member.user_id}</TableCell>
              <TableCell>{new Date(member.added_at).toLocaleString('ja-JP')}</TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRemoveTarget(member.user_id)}
                  aria-label="削除"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
          {group.members.length === 0 && (
            <TableRow>
              <TableCell colSpan={3} className="text-center text-muted-foreground py-4">
                メンバーがいません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <MemberAddDialog
        open={addMemberOpen}
        onOpenChange={setAddMemberOpen}
        groupId={groupId}
      />

      <ConfirmDialog
        open={!!removeTarget}
        onOpenChange={() => setRemoveTarget(null)}
        title="メンバーの削除"
        description="このメンバーをグループから削除しますか？"
        confirmLabel="削除"
        variant="destructive"
        onConfirm={() => {
          if (removeTarget) {
            removeMutation.mutate(
              { groupId, userId: removeTarget },
              { onSuccess: () => setRemoveTarget(null) }
            );
          }
        }}
      />
    </div>
  );
}
