import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Pencil } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDashboard, useExecuteCard } from '@/hooks';
import { DashboardViewer } from '@/components/dashboard/DashboardViewer';

export function DashboardViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const executeCard = useExecuteCard();

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-muted-foreground">ダッシュボードが見つかりません</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{dashboard.name}</h1>
        <Button variant="outline" onClick={() => navigate(`/dashboards/${id}/edit`)}>
          <Pencil className="h-4 w-4 mr-2" />
          編集
        </Button>
      </div>
      <DashboardViewer
        dashboard={dashboard}
        onExecuteCard={(cardId, filters) =>
          executeCard.mutateAsync({ cardId, data: { filters, use_cache: true } })
        }
      />
    </div>
  );
}
