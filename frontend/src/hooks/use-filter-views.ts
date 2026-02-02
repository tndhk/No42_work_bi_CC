import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { filterViewsApi } from '@/lib/api';
import type { FilterViewCreateRequest, FilterViewUpdateRequest } from '@/types';

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
