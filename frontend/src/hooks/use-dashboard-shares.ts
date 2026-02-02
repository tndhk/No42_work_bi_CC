import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardSharesApi } from '@/lib/api';
import type { ShareCreateRequest, ShareUpdateRequest } from '@/types/dashboard';

export function useShares(dashboardId: string) {
  return useQuery({
    queryKey: ['shares', dashboardId],
    queryFn: () => dashboardSharesApi.list(dashboardId),
    enabled: !!dashboardId,
  });
}

export function useCreateShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, data }: { dashboardId: string; data: ShareCreateRequest }) =>
      dashboardSharesApi.create(dashboardId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['shares', variables.dashboardId] });
    },
  });
}

export function useUpdateShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      dashboardId,
      shareId,
      data,
    }: {
      dashboardId: string;
      shareId: string;
      data: ShareUpdateRequest;
    }) => dashboardSharesApi.update(dashboardId, shareId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['shares', variables.dashboardId] });
    },
  });
}

export function useDeleteShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, shareId }: { dashboardId: string; shareId: string }) =>
      dashboardSharesApi.delete(dashboardId, shareId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['shares', variables.dashboardId] });
    },
  });
}
