import { apiClient } from '@/lib/api-client';
import type { ApiResponse } from '@/types';
import type {
  DashboardShare,
  ShareCreateRequest,
  ShareUpdateRequest,
} from '@/types/dashboard';

export const dashboardSharesApi = {
  list: async (dashboardId: string): Promise<DashboardShare[]> => {
    const response = await apiClient
      .get(`dashboards/${dashboardId}/shares`)
      .json<ApiResponse<DashboardShare[]>>();
    return response.data;
  },

  create: async (dashboardId: string, data: ShareCreateRequest): Promise<DashboardShare> => {
    const response = await apiClient
      .post(`dashboards/${dashboardId}/shares`, { json: data })
      .json<ApiResponse<DashboardShare>>();
    return response.data;
  },

  update: async (dashboardId: string, shareId: string, data: ShareUpdateRequest): Promise<DashboardShare> => {
    const response = await apiClient
      .put(`dashboards/${dashboardId}/shares/${shareId}`, { json: data })
      .json<ApiResponse<DashboardShare>>();
    return response.data;
  },

  delete: async (dashboardId: string, shareId: string): Promise<void> => {
    await apiClient.delete(`dashboards/${dashboardId}/shares/${shareId}`);
  },
};
