import { apiClient } from '@/lib/api-client';
import type { ApiResponse, LoginRequest, LoginResponse, UserWithGroups } from '@/types';

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('auth/login', { json: data }).json<ApiResponse<LoginResponse>>();
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('auth/logout').json();
  },

  me: async (): Promise<UserWithGroups> => {
    const response = await apiClient.get('auth/me').json<ApiResponse<UserWithGroups>>();
    return response.data;
  },
};
