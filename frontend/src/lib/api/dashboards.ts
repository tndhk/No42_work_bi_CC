import { apiClient } from '@/lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  PaginationParams,
  Dashboard,
  DashboardDetail,
  DashboardCreateRequest,
  DashboardUpdateRequest,
} from '@/types';

export const dashboardsApi = {
  list: async (params?: PaginationParams & { owner?: string }): Promise<PaginatedResponse<Dashboard>> => {
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    if (params?.owner) searchParams.set('owner', params.owner);
    return apiClient.get('dashboards', { searchParams }).json<PaginatedResponse<Dashboard>>();
  },

  get: async (dashboardId: string): Promise<DashboardDetail> => {
    const response = await apiClient.get(`dashboards/${dashboardId}`).json<ApiResponse<DashboardDetail>>();
    return response.data;
  },

  create: async (data: DashboardCreateRequest): Promise<DashboardDetail> => {
    const response = await apiClient.post('dashboards', { json: data }).json<ApiResponse<DashboardDetail>>();
    return response.data;
  },

  update: async (dashboardId: string, data: DashboardUpdateRequest): Promise<DashboardDetail> => {
    const response = await apiClient.put(`dashboards/${dashboardId}`, { json: data }).json<ApiResponse<DashboardDetail>>();
    return response.data;
  },

  delete: async (dashboardId: string): Promise<void> => {
    await apiClient.delete(`dashboards/${dashboardId}`);
  },

  clone: async (dashboardId: string, name: string): Promise<DashboardDetail> => {
    const response = await apiClient.post(`dashboards/${dashboardId}/clone`, { json: { name } }).json<ApiResponse<DashboardDetail>>();
    return response.data;
  },

  getReferencedDatasets: async (dashboardId: string): Promise<Array<{ dataset_id: string; name: string }>> => {
    const response = await apiClient.get(`dashboards/${dashboardId}/referenced-datasets`).json<ApiResponse<Array<{ dataset_id: string; name: string }>>>();
    return response.data;
  },
};
