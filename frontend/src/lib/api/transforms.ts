import { apiClient } from '@/lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  PaginationParams,
  Transform,
  TransformCreateRequest,
  TransformUpdateRequest,
  TransformExecuteResponse,
  TransformExecution,
} from '@/types';

export const transformsApi = {
  list: async (params?: PaginationParams): Promise<PaginatedResponse<Transform>> => {
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    return apiClient.get('transforms', { searchParams }).json<PaginatedResponse<Transform>>();
  },

  get: async (transformId: string): Promise<Transform> => {
    const response = await apiClient.get(`transforms/${transformId}`).json<ApiResponse<Transform>>();
    return response.data;
  },

  create: async (data: TransformCreateRequest): Promise<Transform> => {
    const response = await apiClient.post('transforms', { json: data }).json<ApiResponse<Transform>>();
    return response.data;
  },

  update: async (transformId: string, data: TransformUpdateRequest): Promise<Transform> => {
    const response = await apiClient.put(`transforms/${transformId}`, { json: data }).json<ApiResponse<Transform>>();
    return response.data;
  },

  delete: async (transformId: string): Promise<void> => {
    await apiClient.delete(`transforms/${transformId}`);
  },

  execute: async (transformId: string): Promise<TransformExecuteResponse> => {
    const response = await apiClient.post(`transforms/${transformId}/execute`, { json: {} }).json<ApiResponse<TransformExecuteResponse>>();
    return response.data;
  },

  listExecutions: async (
    transformId: string,
    params?: PaginationParams,
  ): Promise<PaginatedResponse<TransformExecution>> => {
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    return apiClient
      .get(`transforms/${transformId}/executions`, { searchParams })
      .json<PaginatedResponse<TransformExecution>>();
  },
};
