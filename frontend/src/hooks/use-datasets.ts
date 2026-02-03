import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { datasetsApi } from '@/lib/api';
import type { DatasetUpdateRequest, PaginationParams, S3ImportRequest } from '@/types';

export function useDatasets(params?: PaginationParams & { owner?: string }) {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: () => datasetsApi.list(params),
  });
}

export function useDataset(datasetId: string) {
  return useQuery({
    queryKey: ['datasets', datasetId],
    queryFn: () => datasetsApi.get(datasetId),
    enabled: !!datasetId,
  });
}

export function useDatasetPreview(datasetId: string, limit?: number) {
  return useQuery({
    queryKey: ['datasets', datasetId, 'preview', limit],
    queryFn: () => datasetsApi.preview(datasetId, limit),
    enabled: !!datasetId,
  });
}

export function useCreateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (formData: FormData) => datasetsApi.create(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}

export function useUpdateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ datasetId, data }: { datasetId: string; data: DatasetUpdateRequest }) =>
      datasetsApi.update(datasetId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['datasets', variables.datasetId] });
    },
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (datasetId: string) => datasetsApi.delete(datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}

export function useS3ImportDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: S3ImportRequest) => datasetsApi.s3Import(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}

export function useReimportDryRun() {
  return useMutation({
    mutationFn: (datasetId: string) => datasetsApi.reimportDryRun(datasetId),
  });
}

export function useReimportDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ datasetId, force }: { datasetId: string; force?: boolean }) =>
      datasetsApi.reimport(datasetId, force),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['datasets', variables.datasetId] });
    },
  });
}
