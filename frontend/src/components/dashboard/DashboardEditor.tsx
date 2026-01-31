import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { DashboardLayout } from '@/types';

interface DashboardEditorProps {
  layout: DashboardLayout;
  onLayoutChange: (layout: DashboardLayout) => void;
  onRemoveCard: (cardId: string) => void;
}

export function DashboardEditor({ layout, onLayoutChange, onRemoveCard }: DashboardEditorProps) {
  const cols = layout.columns || 12;
  const rowHeight = layout.row_height || 100;
  const maxY = layout.cards.reduce((max, c) => Math.max(max, c.y + c.h), 4);

  const handleResize = useCallback((cardId: string, delta: { w?: number; h?: number }) => {
    onLayoutChange({
      ...layout,
      cards: layout.cards.map((c) =>
        c.card_id === cardId
          ? {
              ...c,
              w: Math.max(1, Math.min(cols, c.w + (delta.w || 0))),
              h: Math.max(1, c.h + (delta.h || 0)),
            }
          : c
      ),
    });
  }, [layout, onLayoutChange, cols]);

  if (!layout.cards.length) {
    return (
      <div className="border-2 border-dashed rounded-lg p-12 text-center text-muted-foreground">
        カードを追加してダッシュボードを作成してください
      </div>
    );
  }

  return (
    <div
      className="relative border rounded-lg bg-muted/20"
      style={{ minHeight: maxY * rowHeight + 100 }}
    >
      {/* Grid lines */}
      <div className="absolute inset-0 opacity-10">
        {Array.from({ length: cols + 1 }).map((_, i) => (
          <div
            key={`col-${i}`}
            className="absolute top-0 bottom-0 border-l border-border"
            style={{ left: `${(i / cols) * 100}%` }}
          />
        ))}
      </div>

      {layout.cards.map((item) => (
        <div
          key={item.card_id}
          className="absolute border-2 border-primary/50 rounded-lg bg-card p-2 group"
          style={{
            left: `${(item.x / cols) * 100}%`,
            top: item.y * rowHeight,
            width: `${(item.w / cols) * 100}%`,
            height: item.h * rowHeight,
          }}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground truncate">
              {item.card_id}
            </span>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => handleResize(item.card_id, { w: 1 })}
              >
                +
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => handleResize(item.card_id, { w: -1 })}
              >
                -
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => onRemoveCard(item.card_id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div className="text-sm text-center mt-2 text-muted-foreground">
            {item.w}x{item.h}
          </div>
        </div>
      ))}
    </div>
  );
}
