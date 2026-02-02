import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { BookmarkIcon } from 'lucide-react';
import type { FilterView } from '@/types';

interface FilterViewSelectorProps {
  views: FilterView[];
  selectedViewId?: string;
  onSelect: (view: FilterView) => void;
  onSave: (name: string) => void | Promise<void>;
  onOverwrite: (viewId: string) => void | Promise<void>;
  onDelete: (viewId: string) => void | Promise<void>;
}

export function FilterViewSelector({
  views,
  selectedViewId,
  onSelect,
  onSave,
  onOverwrite,
  onDelete,
}: FilterViewSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [newName, setNewName] = useState('');

  const handleSave = async () => {
    if (!newName.trim()) return;
    await onSave(newName.trim());
    setNewName('');
    setIsSaving(false);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="ビュー"
      >
        <BookmarkIcon className="h-4 w-4 mr-2" />
        ビュー
      </Button>

      {isOpen && (
        <div className="absolute top-full mt-1 right-0 z-50 w-72 bg-popover border rounded-md shadow-md p-2 space-y-1">
          {views.map((view) => (
            <button
              key={view.id}
              className="w-full text-left px-3 py-2 rounded hover:bg-accent flex items-center justify-between text-sm"
              onClick={() => {
                onSelect(view);
                setIsOpen(false);
              }}
            >
              <span>{view.name}</span>
              <Badge variant={view.is_shared ? 'default' : 'secondary'} className="ml-2 text-xs">
                {view.is_shared ? '共有' : '個人'}
              </Badge>
            </button>
          ))}

          {views.length === 0 && (
            <p className="text-sm text-muted-foreground px-3 py-2">保存済みビューはありません</p>
          )}

          <div className="border-t pt-2 mt-2 space-y-1">
            {isSaving ? (
              <div className="flex gap-2 px-1">
                <Input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="ビュー名"
                  className="h-8 text-sm"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSave();
                  }}
                />
                <Button size="sm" className="h-8" onClick={handleSave}>
                  保存
                </Button>
              </div>
            ) : (
              <button
                className="w-full text-left px-3 py-2 rounded hover:bg-accent text-sm text-primary"
                onClick={() => setIsSaving(true)}
              >
                名前を付けて保存
              </button>
            )}

            {selectedViewId && (
              <>
                <button
                  className="w-full text-left px-3 py-2 rounded hover:bg-accent text-sm"
                  onClick={() => {
                    onOverwrite(selectedViewId);
                    setIsOpen(false);
                  }}
                >
                  上書き保存
                </button>
                <button
                  className="w-full text-left px-3 py-2 rounded hover:bg-accent text-sm text-destructive"
                  onClick={() => {
                    onDelete(selectedViewId);
                    setIsOpen(false);
                  }}
                >
                  削除
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
