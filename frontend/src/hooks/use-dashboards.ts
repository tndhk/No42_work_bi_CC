import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardsApi } from '@/lib/api';
import type {
  DashboardCreateRequest,
  DashboardUpdateRequest,
  PaginationParams,
} from '@/types';

export function useDashboards(params?: PaginationParams & { owner?: string }) {
  return useQuery({
    queryKey: ['dashboards', params],
    queryFn: () => dashboardsApi.list(params),
  });
}

export function useDashboard(dashboardId: string) {
  return useQuery({
    queryKey: ['dashboards', dashboardId],
    queryFn: () => dashboardsApi.get(dashboardId),
    enabled: !!dashboardId,
  });
}

export function useCreateDashboard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DashboardCreateRequest) => dashboardsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}

export function useUpdateDashboard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ dashboardId, data }: { dashboardId: string; data: DashboardUpdateRequest }) =>
      dashboardsApi.update(dashboardId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      queryClient.invalidateQueries({ queryKey: ['dashboards', variables.dashboardId] });
    },
  });
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (dashboardId: string) => dashboardsApi.delete(dashboardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}

export function useCloneDashboard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ dashboardId, name }: { dashboardId: string; name: string }) =>
      dashboardsApi.clone(dashboardId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}
