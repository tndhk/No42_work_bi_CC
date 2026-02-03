import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import type { SchemaChange, SchemaChangeType } from '@/types/reimport';

interface SchemaChangeWarningDialogProps {
  open: boolean;
  changes: SchemaChange[];
  onConfirm: () => void;
  onCancel: () => void;
}

const changeTypeLabels: Record<SchemaChangeType, string> = {
  added: '追加',
  removed: '削除',
  type_changed: '型変更',
  nullable_changed: 'NULL許容変更',
};

export function SchemaChangeWarningDialog({
  open,
  changes,
  onConfirm,
  onCancel,
}: SchemaChangeWarningDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>スキーマ変更の警告</DialogTitle>
          <DialogDescription>
            以下のスキーマ変更が検出されました。続行すると既存のカードやフィルタに影響する可能性があります。
          </DialogDescription>
        </DialogHeader>

        {changes.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>変更タイプ</TableHead>
                <TableHead>カラム名</TableHead>
                <TableHead>変更前</TableHead>
                <TableHead>変更後</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {changes.map((change, index) => (
                <TableRow key={`${change.column_name}-${index}`}>
                  <TableCell>{changeTypeLabels[change.change_type]}</TableCell>
                  <TableCell>{change.column_name}</TableCell>
                  <TableCell>{change.old_value ?? '-'}</TableCell>
                  <TableCell>{change.new_value ?? '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            キャンセル
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            続行
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
