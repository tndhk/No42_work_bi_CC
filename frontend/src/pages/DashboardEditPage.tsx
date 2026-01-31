import { useParams, useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Save, ArrowLeft, Plus } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDashboard, useUpdateDashboard } from '@/hooks';
import { DashboardEditor } from '@/components/dashboard/DashboardEditor';
import { AddCardDialog } from '@/components/dashboard/AddCardDialog';
import type { DashboardLayout, LayoutItem } from '@/types';

export function DashboardEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const updateMutation = useUpdateDashboard();
  const [addCardOpen, setAddCardOpen] = useState(false);
  const [name, setName] = useState('');
  const [layout, setLayout] = useState<DashboardLayout | null>(null);

  // Initialize state from data
  if (dashboard && !layout) {
    setName(dashboard.name);
    setLayout(dashboard.layout || { cards: [], columns: 12, row_height: 100 });
  }

  const handleSave = () => {
    if (!id || !layout) return;
    updateMutation.mutate({
      dashboardId: id,
      data: { name, layout },
    }, {
      onSuccess: () => navigate(`/dashboards/${id}`),
    });
  };

  const handleAddCard = useCallback((cardId: string) => {
    setLayout((prev) => {
      if (!prev) return prev;
      const maxY = prev.cards.reduce((max, c) => Math.max(max, c.y + c.h), 0);
      const newItem: LayoutItem = { card_id: cardId, x: 0, y: maxY, w: 6, h: 4 };
      return { ...prev, cards: [...prev.cards, newItem] };
    });
    setAddCardOpen(false);
  }, []);

  const handleRemoveCard = useCallback((cardId: string) => {
    setLayout((prev) => {
      if (!prev) return prev;
      return { ...prev, cards: prev.cards.filter((c) => c.card_id !== cardId) };
    });
  }, []);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-muted-foreground">ダッシュボードが見つかりません</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/dashboards/${id}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="text-lg font-bold max-w-md"
        />
        <div className="ml-auto flex gap-2">
          <Button variant="outline" onClick={() => setAddCardOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            カード追加
          </Button>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            保存
          </Button>
        </div>
      </div>

      {layout && (
        <DashboardEditor
          layout={layout}
          onLayoutChange={setLayout}
          onRemoveCard={handleRemoveCard}
        />
      )}

      <AddCardDialog
        open={addCardOpen}
        onOpenChange={setAddCardOpen}
        onSelect={handleAddCard}
        existingCardIds={layout?.cards.map((c) => c.card_id) || []}
      />
    </div>
  );
}
