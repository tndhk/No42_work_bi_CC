import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { filterViewsApi } from '@/lib/api';
import type { FilterView, FilterViewCreateRequest, FilterViewUpdateRequest } from '@/types';

/**
 * デフォルトビューを取得する
 * 優先順位: 自分がownerのデフォルトビュー > 共有デフォルトビュー
 */
export function getDefaultFilterView(
  filterViews: FilterView[],
  currentUserId: string | undefined
): FilterView | undefined {
  if (!filterViews?.length) {
    return undefined;
  }

  // 優先順位1: 自分がownerのデフォルトビュー
  if (currentUserId) {
    const ownDefault = filterViews.find(
      (view) => view.is_default && view.owner_id === currentUserId
    );
    if (ownDefault) return ownDefault;
  }

  // 優先順位2: 共有されているデフォルトビュー
  return filterViews.find((view) => view.is_default && view.is_shared);
}

export function useFilterViews(dashboardId: string) {
  return useQuery({
    queryKey: ['filter-views', dashboardId],
    queryFn: () => filterViewsApi.list(dashboardId),
    enabled: !!dashboardId,
  });
}

export function useCreateFilterView() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ dashboardId, data }: { dashboardId: string; data: FilterViewCreateRequest }) =>
      filterViewsApi.create(dashboardId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-views'] });
    },
  });
}

export function useUpdateFilterView() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ filterViewId, data }: { filterViewId: string; data: FilterViewUpdateRequest }) =>
      filterViewsApi.update(filterViewId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-views'] });
    },
  });
}

export function useDeleteFilterView() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (filterViewId: string) => filterViewsApi.delete(filterViewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-views'] });
    },
  });
}
