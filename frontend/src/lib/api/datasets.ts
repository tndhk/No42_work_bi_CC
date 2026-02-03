import { apiClient } from '@/lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  PaginationParams,
  Dataset,
  DatasetDetail,
  DatasetUpdateRequest,
  DatasetPreview,
  S3ImportRequest,
} from '@/types';
import type { ReimportDryRunResponse } from '@/types/reimport';

export const datasetsApi = {
  list: async (params?: PaginationParams & { owner?: string }): Promise<PaginatedResponse<Dataset>> => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.owner) searchParams.set('owner', params.owner);
    return apiClient.get('datasets', { searchParams }).json<PaginatedResponse<Dataset>>();
  },

  get: async (datasetId: string): Promise<DatasetDetail> => {
    const response = await apiClient.get(`datasets/${datasetId}`).json<ApiResponse<DatasetDetail>>();
    return response.data;
  },

  create: async (formData: FormData): Promise<DatasetDetail> => {
    const response = await apiClient.post('datasets', { body: formData }).json<ApiResponse<DatasetDetail>>();
    return response.data;
  },

  update: async (datasetId: string, data: DatasetUpdateRequest): Promise<DatasetDetail> => {
    const response = await apiClient.put(`datasets/${datasetId}`, { json: data }).json<ApiResponse<DatasetDetail>>();
    return response.data;
  },

  delete: async (datasetId: string): Promise<void> => {
    await apiClient.delete(`datasets/${datasetId}`);
  },

  preview: async (datasetId: string, limit?: number): Promise<DatasetPreview> => {
    const searchParams = new URLSearchParams();
    if (limit) searchParams.set('limit', String(limit));
    const response = await apiClient.get(`datasets/${datasetId}/preview`, { searchParams }).json<ApiResponse<DatasetPreview>>();
    return response.data;
  },

  getColumnValues: async (datasetId: string, columnName: string): Promise<string[]> => {
    const response = await apiClient.get(`datasets/${datasetId}/columns/${columnName}/values`).json<ApiResponse<string[]>>();
    return response.data;
  },

  s3Import: async (data: S3ImportRequest): Promise<DatasetDetail> => {
    const response = await apiClient.post('datasets/s3-import', { json: data }).json<ApiResponse<DatasetDetail>>();
    return response.data;
  },

  reimportDryRun: async (datasetId: string): Promise<ReimportDryRunResponse> => {
    const response = await apiClient.post(`datasets/${datasetId}/reimport/dry-run`).json<ApiResponse<ReimportDryRunResponse>>();
    return response.data;
  },

  reimport: async (datasetId: string, force: boolean = false): Promise<DatasetDetail> => {
    const response = await apiClient.post(`datasets/${datasetId}/reimport`, { json: { force } }).json<ApiResponse<DatasetDetail>>();
    return response.data;
  },
};
