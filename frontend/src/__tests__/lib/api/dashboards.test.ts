import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardsApi } from '@/lib/api/dashboards';
import type {
  Dashboard,
  DashboardDetail,
  DashboardCreateRequest,
  DashboardUpdateRequest,
  ApiResponse,
  PaginatedResponse,
} from '@/types';

// Mock apiClient
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';
const mockGet = apiClient.get as ReturnType<typeof vi.fn>;
const mockPost = apiClient.post as ReturnType<typeof vi.fn>;
const mockPut = apiClient.put as ReturnType<typeof vi.fn>;
const mockDelete = apiClient.delete as ReturnType<typeof vi.fn>;

describe('dashboardsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('パラメータなしでGETリクエストを送信する', async () => {
      const mockResponse: PaginatedResponse<Dashboard> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await dashboardsApi.list();

      expect(mockGet).toHaveBeenCalledWith('dashboards', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('limit/offset/ownerのパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<Dashboard> = {
        items: [],
        total: 0,
        limit: 20,
        offset: 10,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await dashboardsApi.list({ limit: 20, offset: 10, owner: 'user-1' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('20');
      expect(searchParams.get('offset')).toBe('10');
      expect(searchParams.get('owner')).toBe('user-1');
    });

    it('offset=0でもパラメータが送信される', async () => {
      const mockResponse: PaginatedResponse<Dashboard> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await dashboardsApi.list({ limit: 10, offset: 0 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('10');
      expect(searchParams.get('offset')).toBe('0');
    });
  });

  describe('get', () => {
    it('指定IDのダッシュボード詳細を取得する', async () => {
      const mockDashboard: DashboardDetail = {
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        card_count: 3,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        cards: [],
      };

      const mockApiResponse: ApiResponse<DashboardDetail> = {
        data: mockDashboard,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await dashboardsApi.get('dashboard-1');

      expect(mockGet).toHaveBeenCalledWith('dashboards/dashboard-1');
      expect(result).toEqual(mockDashboard);
    });
  });

  describe('create', () => {
    it('ダッシュボードを作成する', async () => {
      const createData: DashboardCreateRequest = {
        name: 'New Dashboard',
      };

      const mockDashboard: DashboardDetail = {
        dashboard_id: 'dashboard-2',
        name: 'New Dashboard',
        card_count: 0,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        cards: [],
      };

      const mockApiResponse: ApiResponse<DashboardDetail> = {
        data: mockDashboard,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await dashboardsApi.create(createData);

      expect(mockPost).toHaveBeenCalledWith('dashboards', { json: createData });
      expect(result).toEqual(mockDashboard);
    });
  });

  describe('update', () => {
    it('ダッシュボードを更新する', async () => {
      const updateData: DashboardUpdateRequest = {
        name: 'Updated Dashboard',
      };

      const mockDashboard: DashboardDetail = {
        dashboard_id: 'dashboard-1',
        name: 'Updated Dashboard',
        card_count: 3,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z',
        cards: [],
      };

      const mockApiResponse: ApiResponse<DashboardDetail> = {
        data: mockDashboard,
      };

      mockPut.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await dashboardsApi.update('dashboard-1', updateData);

      expect(mockPut).toHaveBeenCalledWith('dashboards/dashboard-1', { json: updateData });
      expect(result).toEqual(mockDashboard);
    });
  });

  describe('delete', () => {
    it('ダッシュボードを削除する', async () => {
      mockDelete.mockResolvedValue(undefined);

      await dashboardsApi.delete('dashboard-1');

      expect(mockDelete).toHaveBeenCalledWith('dashboards/dashboard-1');
    });
  });

  describe('clone', () => {
    it('ダッシュボードを複製する', async () => {
      const mockDashboard: DashboardDetail = {
        dashboard_id: 'dashboard-3',
        name: 'Cloned Dashboard',
        card_count: 3,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        cards: [],
      };

      const mockApiResponse: ApiResponse<DashboardDetail> = {
        data: mockDashboard,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await dashboardsApi.clone('dashboard-1', 'Cloned Dashboard');

      expect(mockPost).toHaveBeenCalledWith('dashboards/dashboard-1/clone', {
        json: { name: 'Cloned Dashboard' },
      });
      expect(result).toEqual(mockDashboard);
    });
  });
});
