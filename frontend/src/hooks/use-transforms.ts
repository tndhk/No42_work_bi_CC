import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { transformsApi } from '@/lib/api';
import type {
  TransformCreateRequest,
  TransformUpdateRequest,
  PaginationParams,
} from '@/types';

export function useTransforms(params?: PaginationParams) {
  return useQuery({
    queryKey: ['transforms', params],
    queryFn: () => transformsApi.list(params),
  });
}

export function useTransform(transformId: string) {
  return useQuery({
    queryKey: ['transforms', transformId],
    queryFn: () => transformsApi.get(transformId),
    enabled: !!transformId,
  });
}

export function useCreateTransform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TransformCreateRequest) => transformsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transforms'] });
    },
  });
}

export function useUpdateTransform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ transformId, data }: { transformId: string; data: TransformUpdateRequest }) =>
      transformsApi.update(transformId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transforms'] });
      queryClient.invalidateQueries({ queryKey: ['transforms', variables.transformId] });
    },
  });
}

export function useDeleteTransform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transformId: string) => transformsApi.delete(transformId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transforms'] });
    },
  });
}

export function useExecuteTransform() {
  return useMutation({
    mutationFn: (transformId: string) => transformsApi.execute(transformId),
  });
}

export function useTransformExecutions(transformId: string, params?: PaginationParams) {
  return useQuery({
    queryKey: ['transform-executions', transformId, params],
    queryFn: () => transformsApi.listExecutions(transformId, params),
    enabled: !!transformId,
  });
}
