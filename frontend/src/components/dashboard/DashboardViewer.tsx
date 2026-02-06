import { useState, useEffect } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { CardContainer } from './CardContainer';
import { toRGLLayout } from '@/lib/layout-utils';
import type { DashboardDetail, CardExecuteResponse } from '@/types';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardViewerProps {
  dashboard: DashboardDetail;
  filters?: Record<string, unknown>;
  onExecuteCard: (cardId: string, filters?: Record<string, unknown>) => Promise<CardExecuteResponse>;
}

export function DashboardViewer({ dashboard, filters, onExecuteCard }: DashboardViewerProps) {
  const [cardResults, setCardResults] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const filtersJson = JSON.stringify(filters || {});

  useEffect(() => {
    if (!dashboard.layout?.cards) return;

    const currentFilters = filters && Object.keys(filters).length > 0 ? filters : undefined;

    dashboard.layout.cards.forEach((item) => {
      setLoading((prev) => ({ ...prev, [item.card_id]: true }));
      onExecuteCard(item.card_id, currentFilters)
        .then((result) => {
          setCardResults((prev) => ({ ...prev, [item.card_id]: result.html }));
        })
        .catch(() => {
          setCardResults((prev) => ({ ...prev, [item.card_id]: '<div style="color:red">読み込みエラー</div>' }));
        })
        .finally(() => {
          setLoading((prev) => ({ ...prev, [item.card_id]: false }));
        });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dashboard.layout?.cards, filtersJson]);

  if (!dashboard.layout?.cards?.length) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        カードがまだ配置されていません
      </div>
    );
  }

  const cols = dashboard.layout.columns || 12;
  const rowHeight = dashboard.layout.row_height || 100;
  const layout = toRGLLayout(dashboard.layout.cards);
  const hasActiveFilters = filters && Object.keys(filters).length > 0;

  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={{ lg: layout }}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: cols, md: cols, sm: cols, xs: cols, xxs: cols }}
      rowHeight={rowHeight}
      isDraggable={false}
      isResizable={false}
      compactType="vertical"
    >
      {dashboard.layout.cards.map((item) => (
        <div
          key={item.card_id}
          className="border border-border rounded-lg bg-card overflow-hidden shadow-sm hover:shadow-lg transition-all duration-200"
        >
          {loading[item.card_id] ? (
            <div className="flex items-center justify-center h-full min-h-[200px]">
              <LoadingSpinner />
            </div>
          ) : (
            <CardContainer
              cardId={item.card_id}
              html={cardResults[item.card_id] || ''}
              filterApplied={hasActiveFilters}
            />
          )}
        </div>
      ))}
    </ResponsiveGridLayout>
  );
}
