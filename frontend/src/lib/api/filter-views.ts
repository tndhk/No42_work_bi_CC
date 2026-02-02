import { apiClient } from '@/lib/api-client';
import type {
  ApiResponse,
  FilterView,
  FilterViewCreateRequest,
  FilterViewUpdateRequest,
} from '@/types';

export const filterViewsApi = {
  list: async (dashboardId: string): Promise<FilterView[]> => {
    const response = await apiClient
      .get(`dashboards/${dashboardId}/filter-views`)
      .json<ApiResponse<FilterView[]>>();
    return response.data;
  },

  create: async (dashboardId: string, data: FilterViewCreateRequest): Promise<FilterView> => {
    const response = await apiClient
      .post(`dashboards/${dashboardId}/filter-views`, { json: data })
      .json<ApiResponse<FilterView>>();
    return response.data;
  },

  get: async (filterViewId: string): Promise<FilterView> => {
    const response = await apiClient
      .get(`filter-views/${filterViewId}`)
      .json<ApiResponse<FilterView>>();
    return response.data;
  },

  update: async (filterViewId: string, data: FilterViewUpdateRequest): Promise<FilterView> => {
    const response = await apiClient
      .put(`filter-views/${filterViewId}`, { json: data })
      .json<ApiResponse<FilterView>>();
    return response.data;
  },

  delete: async (filterViewId: string): Promise<void> => {
    await apiClient.delete(`filter-views/${filterViewId}`);
  },
};
