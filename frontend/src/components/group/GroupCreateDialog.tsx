import { useState } from 'react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useCreateGroup } from '@/hooks';

interface GroupCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GroupCreateDialog({ open, onOpenChange }: GroupCreateDialogProps) {
  const [name, setName] = useState('');
  const createMutation = useCreateGroup();

  const handleCreate = () => {
    if (!name.trim()) return;
    createMutation.mutate({ name: name.trim() }, {
      onSuccess: () => {
        onOpenChange(false);
        setName('');
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新規グループ</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="group-name">名前</Label>
            <Input
              id="group-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="グループ名"
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>キャンセル</Button>
          <Button onClick={handleCreate} disabled={!name.trim() || createMutation.isPending}>
            作成
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
