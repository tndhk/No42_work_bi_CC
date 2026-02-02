import { describe, it, expect, vi, beforeEach } from 'vitest';

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
import { filterViewsApi } from '@/lib/api/filter-views';
import type { FilterView, ApiResponse } from '@/types';

const mockGet = apiClient.get as ReturnType<typeof vi.fn>;
const mockPost = apiClient.post as ReturnType<typeof vi.fn>;
const mockPut = apiClient.put as ReturnType<typeof vi.fn>;
const mockDelete = apiClient.delete as ReturnType<typeof vi.fn>;

const mockFilterView: FilterView = {
  id: 'fv_1',
  dashboard_id: 'dashboard_abc',
  name: 'View 1',
  owner_id: 'user_1',
  filter_state: { category: 'sales' },
  is_shared: false,
  is_default: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('filterViewsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('ダッシュボードIDでフィルタビュー一覧をGET取得する', async () => {
      const mockViews: FilterView[] = [
        mockFilterView,
        { ...mockFilterView, id: 'fv_2', name: 'View 2' },
      ];
      const mockApiResponse: ApiResponse<FilterView[]> = {
        data: mockViews,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await filterViewsApi.list('dashboard_abc');

      expect(mockGet).toHaveBeenCalledWith('dashboards/dashboard_abc/filter-views');
      expect(result).toEqual(mockViews);
      expect(result).toHaveLength(2);
    });
  });

  describe('create', () => {
    it('POSTリクエストでフィルタビューを作成する', async () => {
      const mockApiResponse: ApiResponse<FilterView> = {
        data: mockFilterView,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const createData = { name: 'View 1', filter_state: { category: 'sales' } };
      const result = await filterViewsApi.create('dashboard_abc', createData);

      expect(mockPost).toHaveBeenCalledWith('dashboards/dashboard_abc/filter-views', {
        json: createData,
      });
      expect(result).toEqual(mockFilterView);
      expect(result.name).toBe('View 1');
    });
  });

  describe('get', () => {
    it('IDでフィルタビュー詳細をGET取得する', async () => {
      const mockApiResponse: ApiResponse<FilterView> = {
        data: mockFilterView,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await filterViewsApi.get('fv_1');

      expect(mockGet).toHaveBeenCalledWith('filter-views/fv_1');
      expect(result).toEqual(mockFilterView);
      expect(result.id).toBe('fv_1');
    });
  });

  describe('update', () => {
    it('PUTリクエストでフィルタビューを更新する', async () => {
      const updatedView: FilterView = {
        ...mockFilterView,
        name: 'Updated View',
        updated_at: '2026-01-02T00:00:00Z',
      };
      const mockApiResponse: ApiResponse<FilterView> = {
        data: updatedView,
      };

      mockPut.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const updateData = { name: 'Updated View' };
      const result = await filterViewsApi.update('fv_1', updateData);

      expect(mockPut).toHaveBeenCalledWith('filter-views/fv_1', {
        json: updateData,
      });
      expect(result).toEqual(updatedView);
      expect(result.name).toBe('Updated View');
    });
  });

  describe('delete', () => {
    it('DELETEリクエストでフィルタビューを削除する', async () => {
      mockDelete.mockResolvedValue(undefined);

      await filterViewsApi.delete('fv_1');

      expect(mockDelete).toHaveBeenCalledWith('filter-views/fv_1');
    });
  });
});
