import { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pencil, Filter, Share2 } from 'lucide-react';
import { ShareDialog } from '@/components/dashboard/ShareDialog';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import {
  useDashboard,
  useExecuteCard,
  useFilterViews,
  useCreateFilterView,
  useUpdateFilterView,
  useDeleteFilterView,
  getDefaultFilterView,
} from '@/hooks';
import { useAuthStore } from '@/stores/auth-store';
import { DashboardViewer } from '@/components/dashboard/DashboardViewer';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { FilterViewSelector } from '@/components/dashboard/FilterViewSelector';
import type { FilterView } from '@/types';

export function DashboardViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const executeCard = useExecuteCard();
  const [filterValues, setFilterValues] = useState<Record<string, unknown>>({});
  const [filterBarVisible, setFilterBarVisible] = useState(true);
  const [selectedViewId, setSelectedViewId] = useState<string | undefined>();
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  const { data: filterViews = [] } = useFilterViews(id!);
  const createFilterView = useCreateFilterView();
  const updateFilterView = useUpdateFilterView();
  const deleteFilterView = useDeleteFilterView();

  const currentUser = useAuthStore((state) => state.user);
  const defaultViewAppliedRef = useRef(false);

  // デフォルトビューの自動適用（初回のみ）
  useEffect(() => {
    if (defaultViewAppliedRef.current || !filterViews.length) return;

    const defaultView = getDefaultFilterView(filterViews, currentUser?.user_id);
    if (defaultView) {
      setFilterValues(defaultView.filter_state as Record<string, unknown>);
      setSelectedViewId(defaultView.id);
      defaultViewAppliedRef.current = true;
    }
  }, [filterViews, currentUser?.user_id]);

  const handleFilterChange = useCallback((filterId: string, value: unknown) => {
    setFilterValues((prev) => {
      if (value === undefined) {
        const { [filterId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [filterId]: value };
    });
  }, []);

  const handleClearAll = useCallback(() => {
    setFilterValues({});
    setSelectedViewId(undefined);
  }, []);

  const handleSelectView = useCallback((view: FilterView) => {
    setFilterValues(view.filter_state as Record<string, unknown>);
    setSelectedViewId(view.id);
  }, []);

  const handleSaveView = useCallback(async (name: string) => {
    if (!id) return;
    await createFilterView.mutateAsync({
      dashboardId: id,
      data: {
        name,
        filter_state: filterValues,
      },
    });
  }, [id, filterValues, createFilterView]);

  const handleOverwriteView = useCallback(async (viewId: string) => {
    await updateFilterView.mutateAsync({
      filterViewId: viewId,
      data: {
        filter_state: filterValues,
      },
    });
  }, [filterValues, updateFilterView]);

  const handleDeleteView = useCallback(async (viewId: string) => {
    await deleteFilterView.mutateAsync(viewId);
    if (selectedViewId === viewId) {
      setSelectedViewId(undefined);
    }
  }, [selectedViewId, deleteFilterView]);

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-muted-foreground">ダッシュボードが見つかりません</div>;
  }

  const myPermission = dashboard.my_permission;
  const hasFilters = dashboard.filters && dashboard.filters.length > 0;
  const activeFilterCount = Object.keys(filterValues).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{dashboard.name}</h1>
        <div className="flex items-center gap-2">
          {hasFilters && (
            <>
              <FilterViewSelector
                views={filterViews}
                selectedViewId={selectedViewId}
                onSelect={handleSelectView}
                onSave={handleSaveView}
                onOverwrite={handleOverwriteView}
                onDelete={handleDeleteView}
              />
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
            </>
          )}
          {myPermission !== 'viewer' && (
            <Button variant="outline" onClick={() => navigate(`/dashboards/${id}/edit`)}>
              <Pencil className="h-4 w-4 mr-2" />
              編集
            </Button>
          )}
          {myPermission === 'owner' && (
            <Button variant="outline" onClick={() => setShareDialogOpen(true)}>
              <Share2 className="h-4 w-4 mr-2" />
              共有
            </Button>
          )}
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

      {myPermission === 'owner' && (
        <ShareDialog
          open={shareDialogOpen}
          onOpenChange={setShareDialogOpen}
          dashboardId={id!}
        />
      )}
    </div>
  );
}
