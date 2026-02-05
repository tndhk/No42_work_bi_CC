import { useCallback } from 'react';
import {
  useCreateFilterView,
  useUpdateFilterView,
  useDeleteFilterView,
} from './use-filter-views';
import type { FilterView } from '@/types';

interface UseFilterViewOperationsOptions {
  dashboardId: string;
  filterValues: Record<string, unknown>;
  selectedViewId?: string;
  onSelectedViewChange?: (viewId: string | undefined) => void;
  onFiltersChange?: (filters: Record<string, unknown>) => void;
}

/**
 * フィルタービューの CRUD 操作を管理するカスタムフック
 */
export function useFilterViewOperations({
  dashboardId,
  filterValues,
  selectedViewId,
  onSelectedViewChange,
  onFiltersChange,
}: UseFilterViewOperationsOptions) {
  const createFilterView = useCreateFilterView();
  const updateFilterView = useUpdateFilterView();
  const deleteFilterView = useDeleteFilterView();

  const handleSelectView = useCallback(
    (view: FilterView) => {
      onFiltersChange?.(view.filter_state as Record<string, unknown>);
      onSelectedViewChange?.(view.id);
    },
    [onFiltersChange, onSelectedViewChange]
  );

  const handleSaveView = useCallback(
    async (name: string, options?: { is_shared: boolean }) => {
      await createFilterView.mutateAsync({
        dashboardId,
        data: {
          name,
          filter_state: filterValues,
          is_shared: options?.is_shared ?? false,
        },
      });
    },
    [dashboardId, filterValues, createFilterView]
  );

  const handleOverwriteView = useCallback(
    async (viewId: string) => {
      await updateFilterView.mutateAsync({
        filterViewId: viewId,
        data: {
          filter_state: filterValues,
        },
      });
    },
    [filterValues, updateFilterView]
  );

  const handleDeleteView = useCallback(
    async (viewId: string) => {
      await deleteFilterView.mutateAsync(viewId);
      if (selectedViewId === viewId) {
        onSelectedViewChange?.(undefined);
      }
    },
    [selectedViewId, deleteFilterView, onSelectedViewChange]
  );

  return {
    handleSelectView,
    handleSaveView,
    handleOverwriteView,
    handleDeleteView,
  };
}
