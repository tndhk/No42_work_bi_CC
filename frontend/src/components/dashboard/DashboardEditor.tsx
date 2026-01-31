import { useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import type { Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { toRGLLayout, fromRGLLayout } from '@/lib/layout-utils';
import type { DashboardLayout } from '@/types';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardEditorProps {
  layout: DashboardLayout;
  onLayoutChange: (layout: DashboardLayout) => void;
  onRemoveCard: (cardId: string) => void;
}

export function DashboardEditor({ layout, onLayoutChange, onRemoveCard }: DashboardEditorProps) {
  const cols = layout.columns || 12;
  const rowHeight = layout.row_height || 100;

  const handleLayoutChange = useCallback((newLayout: Layout[]) => {
    const updatedCards = fromRGLLayout(newLayout);
    onLayoutChange({
      ...layout,
      cards: updatedCards,
    });
  }, [layout, onLayoutChange]);

  if (!layout.cards.length) {
    return (
      <div className="border-2 border-dashed rounded-lg p-12 text-center text-muted-foreground">
        カードを追加してダッシュボードを作成してください
      </div>
    );
  }

  const rglLayout = toRGLLayout(layout.cards);

  return (
    <div className="border rounded-lg bg-muted/20 p-4">
      <ResponsiveGridLayout
        className="layout"
        layouts={{ lg: rglLayout }}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: cols, md: cols, sm: cols, xs: cols, xxs: cols }}
        rowHeight={rowHeight}
        isDraggable={true}
        isResizable={true}
        compactType="vertical"
        onLayoutChange={handleLayoutChange}
      >
        {layout.cards.map((item) => (
          <div
            key={item.card_id}
            className="border-2 border-primary/50 rounded-lg bg-card p-2 group relative"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-muted-foreground truncate">
                {item.card_id}
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => onRemoveCard(item.card_id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
            <div className="text-sm text-center mt-2 text-muted-foreground">
              {item.w}x{item.h}
            </div>
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  );
}
