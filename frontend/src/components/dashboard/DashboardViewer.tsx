import { useState, useEffect } from 'react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { CardContainer } from './CardContainer';
import type { DashboardDetail, CardExecuteResponse } from '@/types';

interface DashboardViewerProps {
  dashboard: DashboardDetail;
  onExecuteCard: (cardId: string, filters?: Record<string, unknown>) => Promise<CardExecuteResponse>;
}

export function DashboardViewer({ dashboard, onExecuteCard }: DashboardViewerProps) {
  const [cardResults, setCardResults] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!dashboard.layout?.cards) return;

    dashboard.layout.cards.forEach((item) => {
      setLoading((prev) => ({ ...prev, [item.card_id]: true }));
      onExecuteCard(item.card_id)
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
  }, [dashboard.layout?.cards, onExecuteCard]);

  if (!dashboard.layout?.cards?.length) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        カードがまだ配置されていません
      </div>
    );
  }

  const cols = dashboard.layout.columns || 12;
  const rowHeight = dashboard.layout.row_height || 100;

  return (
    <div className="relative" style={{ minHeight: 400 }}>
      {dashboard.layout.cards.map((item) => (
        <div
          key={item.card_id}
          className="absolute border rounded-lg bg-card overflow-hidden"
          style={{
            left: `${(item.x / cols) * 100}%`,
            top: item.y * rowHeight,
            width: `${(item.w / cols) * 100}%`,
            height: item.h * rowHeight,
          }}
        >
          {loading[item.card_id] ? (
            <div className="flex items-center justify-center h-full">
              <LoadingSpinner />
            </div>
          ) : (
            <CardContainer cardId={item.card_id} html={cardResults[item.card_id] || ''} />
          )}
        </div>
      ))}
    </div>
  );
}
