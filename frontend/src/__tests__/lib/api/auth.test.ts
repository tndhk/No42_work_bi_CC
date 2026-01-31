import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authApi } from '@/lib/api/auth';
import type { LoginRequest, LoginResponse, UserWithGroups, ApiResponse } from '@/types';

// Mock apiClient
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';
const mockPost = apiClient.post as ReturnType<typeof vi.fn>;
const mockGet = apiClient.get as ReturnType<typeof vi.fn>;

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('正しいエンドポイントにPOSTしてLoginResponseを返す', async () => {
      const loginRequest: LoginRequest = {
        email: 'test@example.com',
        password: 'password123',
      };

      const mockLoginResponse: LoginResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          user_id: 'user-1',
          email: 'test@example.com',
          created_at: '2026-01-01T00:00:00Z',
        },
      };

      const mockApiResponse: ApiResponse<LoginResponse> = {
        data: mockLoginResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await authApi.login(loginRequest);

      expect(mockPost).toHaveBeenCalledWith('auth/login', { json: loginRequest });
      expect(result).toEqual(mockLoginResponse);
    });
  });

  describe('logout', () => {
    it('正しいエンドポイントにPOSTする', async () => {
      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue({}),
      });

      await authApi.logout();

      expect(mockPost).toHaveBeenCalledWith('auth/logout');
    });
  });

  describe('me', () => {
    it('正しいエンドポイントにGETしてUserWithGroupsを返す', async () => {
      const mockUser: UserWithGroups = {
        user_id: 'user-1',
        email: 'test@example.com',
        created_at: '2026-01-01T00:00:00Z',
        groups: [
          { group_id: 'group-1', name: 'Admin' },
          { group_id: 'group-2', name: 'Users' },
        ],
      };

      const mockApiResponse: ApiResponse<UserWithGroups> = {
        data: mockUser,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await authApi.me();

      expect(mockGet).toHaveBeenCalledWith('auth/me');
      expect(result).toEqual(mockUser);
    });
  });
});
