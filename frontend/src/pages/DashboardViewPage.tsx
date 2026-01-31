import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pencil, Filter } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDashboard, useExecuteCard } from '@/hooks';
import { DashboardViewer } from '@/components/dashboard/DashboardViewer';
import { FilterBar } from '@/components/dashboard/FilterBar';

export function DashboardViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const executeCard = useExecuteCard();
  const [filterValues, setFilterValues] = useState<Record<string, unknown>>({});
  const [filterBarVisible, setFilterBarVisible] = useState(true);

  const handleFilterChange = useCallback((filterId: string, value: unknown) => {
    setFilterValues((prev) => {
      const next = { ...prev };
      if (value === undefined) {
        delete next[filterId];
      } else {
        next[filterId] = value;
      }
      return next;
    });
  }, []);

  const handleClearAll = useCallback(() => {
    setFilterValues({});
  }, []);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-muted-foreground">ダッシュボードが見つかりません</div>;
  }

  const hasFilters = dashboard.filters && dashboard.filters.length > 0;
  const activeFilterCount = Object.keys(filterValues).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{dashboard.name}</h1>
        <div className="flex items-center gap-2">
          {hasFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilterBarVisible(!filterBarVisible)}
              aria-label="フィルタ表示切替"
            >
              <Filter className="h-4 w-4 mr-2" />
              フィルタ
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 min-w-[20px] px-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate(`/dashboards/${id}/edit`)}>
            <Pencil className="h-4 w-4 mr-2" />
            編集
          </Button>
        </div>
      </div>

      {hasFilters && filterBarVisible && (
        <FilterBar
          filters={dashboard.filters}
          values={filterValues}
          onFilterChange={handleFilterChange}
          onClearAll={handleClearAll}
        />
      )}

      <DashboardViewer
        dashboard={dashboard}
        filters={filterValues}
        onExecuteCard={(cardId, filters) =>
          executeCard.mutateAsync({ cardId, data: { filters, use_cache: true } })
        }
      />
    </div>
  );
}
