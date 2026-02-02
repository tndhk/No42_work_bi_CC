import { useState } from 'react';
import { useShares, useCreateShare, useUpdateShare, useDeleteShare } from '@/hooks';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Trash2 } from 'lucide-react';
import type { Permission, SharedToType } from '@/types/dashboard';

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  dashboardId: string;
}

export function ShareDialog({ open, onOpenChange, dashboardId }: ShareDialogProps) {
  const { data: shares = [], isLoading } = useShares(dashboardId);
  const createShare = useCreateShare();
  const updateShare = useUpdateShare();
  const deleteShare = useDeleteShare();

  const [sharedToType, setSharedToType] = useState<SharedToType>('user');
  const [sharedToId, setSharedToId] = useState('');
  const [permission, setPermission] = useState<Permission>('viewer');

  const handleAdd = () => {
    if (!sharedToId.trim()) return;
    createShare.mutate(
      {
        dashboardId,
        data: {
          shared_to_type: sharedToType,
          shared_to_id: sharedToId,
          permission,
        },
      },
      {
        onSuccess: () => {
          setSharedToId('');
        },
      },
    );
  };

  const handlePermissionChange = (shareId: string, newPermission: Permission) => {
    updateShare.mutate({
      dashboardId,
      shareId,
      data: { permission: newPermission },
    });
  };

  const handleDelete = (shareId: string) => {
    deleteShare.mutate({ dashboardId, shareId });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>共有設定</DialogTitle>
          <DialogDescription>ダッシュボードの共有先と権限を管理します</DialogDescription>
        </DialogHeader>

        {/* 追加フォーム */}
        <div className="space-y-4 py-4">
          <div className="flex gap-2 items-end">
            <div className="space-y-1">
              <Label htmlFor="share-type">共有タイプ</Label>
              <Select
                value={sharedToType}
                onValueChange={(v) => setSharedToType(v as SharedToType)}
              >
                <SelectTrigger id="share-type" aria-label="共有タイプ">
                  <SelectValue placeholder="タイプ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">user</SelectItem>
                  <SelectItem value="group">group</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 space-y-1">
              <Label htmlFor="share-target-id">共有先ID</Label>
              <Input
                id="share-target-id"
                aria-label="共有先ID"
                value={sharedToId}
                onChange={(e) => setSharedToId(e.target.value)}
                placeholder="ユーザーIDまたはグループID"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="share-permission">権限</Label>
              <Select
                value={permission}
                onValueChange={(v) => setPermission(v as Permission)}
              >
                <SelectTrigger id="share-permission" aria-label="権限">
                  <SelectValue placeholder="権限" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">viewer</SelectItem>
                  <SelectItem value="editor">editor</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleAdd} disabled={createShare.isPending}>
              追加
            </Button>
          </div>
        </div>

        {/* 共有一覧 */}
        {isLoading ? (
          <div className="flex justify-center py-4">
            <LoadingSpinner />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>タイプ</TableHead>
                <TableHead>共有先</TableHead>
                <TableHead>権限</TableHead>
                <TableHead>共有者</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {shares.map((share) => (
                <TableRow key={share.id}>
                  <TableCell>{share.shared_to_type}</TableCell>
                  <TableCell>{share.shared_to_id}</TableCell>
                  <TableCell>
                    <Select
                      value={share.permission}
                      onValueChange={(v) =>
                        handlePermissionChange(share.id, v as Permission)
                      }
                    >
                      <SelectTrigger aria-label={`権限変更 ${share.shared_to_id}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="viewer">viewer</SelectItem>
                        <SelectItem value="editor">editor</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>{share.shared_by}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(share.id)}
                      aria-label="削除"
                      disabled={deleteShare.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {shares.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-center text-muted-foreground py-4"
                  >
                    共有設定がありません
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </DialogContent>
    </Dialog>
  );
}
