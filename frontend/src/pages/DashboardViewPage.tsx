import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShareDialog } from '@/components/dashboard/ShareDialog';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import {
  useDashboard,
  useExecuteCard,
  useFilterViews,
} from '@/hooks';
import { useAuthStore } from '@/stores/auth-store';
import { DashboardViewer } from '@/components/dashboard/DashboardViewer';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { useDashboardFilters } from '@/hooks/use-dashboard-filters';
import { useFilterViewOperations } from '@/hooks/use-filter-view-operations';
import { useDefaultFilterView } from '@/hooks/use-default-filter-view';
import type { FilterView } from '@/types';

export function DashboardViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useDashboard(id!);
  const executeCard = useExecuteCard();
  const [filterBarVisible, setFilterBarVisible] = useState(true);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  const { data: filterViews = [] } = useFilterViews(id!);
  const currentUser = useAuthStore((state) => state.user);

  const {
    filterValues,
    selectedViewId,
    handleFilterChange,
    handleClearAll,
    setFilters,
    setSelectedView,
  } = useDashboardFilters();

  const {
    handleSelectView,
    handleSaveView,
    handleOverwriteView,
    handleDeleteView,
  } = useFilterViewOperations({
    dashboardId: id!,
    filterValues,
    selectedViewId,
    onSelectedViewChange: setSelectedView,
    onFiltersChange: setFilters,
  });

  // デフォルトビューの自動適用（初回のみ）
  const handleApplyDefaultView = useCallback((view: FilterView) => {
    setFilters(view.filter_state as Record<string, unknown>);
    setSelectedView(view.id);
  }, [setFilters, setSelectedView]);

  useDefaultFilterView({
    filterViews,
    currentUserId: currentUser?.user_id,
    onApply: handleApplyDefaultView,
  });

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-muted-foreground">ダッシュボードが見つかりません</div>;
  }

  const myPermission = dashboard.my_permission;
  const hasFilters = (dashboard.filters?.length ?? 0) > 0;
  const activeFilterCount = Object.keys(filterValues).length;

  return (
    <div className="space-y-4">
      <DashboardHeader
        dashboardName={dashboard.name}
        filterViews={filterViews}
        selectedViewId={selectedViewId}
        activeFilterCount={activeFilterCount}
        filterBarVisible={filterBarVisible}
        myPermission={myPermission}
        hasFilters={hasFilters}
        dashboardId={id!}
        onToggleFilterBar={() => setFilterBarVisible(!filterBarVisible)}
        onSelectView={handleSelectView}
        onSaveView={handleSaveView}
        onOverwriteView={handleOverwriteView}
        onDeleteView={handleDeleteView}
        onEdit={() => navigate(`/dashboards/${id}/edit`)}
        onShare={() => setShareDialogOpen(true)}
      />

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
