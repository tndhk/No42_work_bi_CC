import { describe, it, expect, vi, beforeEach } from 'vitest';
import type {
  Transform,
  TransformCreateRequest,
  TransformUpdateRequest,
  TransformExecuteResponse,
  TransformExecution,
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

import { transformsApi } from '@/lib/api/transforms';
import { apiClient } from '@/lib/api-client';

const mockGet = apiClient.get as ReturnType<typeof vi.fn>;
const mockPost = apiClient.post as ReturnType<typeof vi.fn>;
const mockPut = apiClient.put as ReturnType<typeof vi.fn>;
const mockDelete = apiClient.delete as ReturnType<typeof vi.fn>;

describe('transformsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('パラメータなしでGETリクエストを送信する', async () => {
      const mockResponse: PaginatedResponse<Transform> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await transformsApi.list();

      expect(mockGet).toHaveBeenCalledWith('transforms', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('limit/offsetのパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<Transform> = {
        items: [],
        total: 0,
        limit: 20,
        offset: 10,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await transformsApi.list({ limit: 20, offset: 10 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('20');
      expect(searchParams.get('offset')).toBe('10');
    });
  });

  describe('get', () => {
    it('指定IDのTransformを取得する', async () => {
      const mockTransform: Transform = {
        id: 'transform-1',
        name: 'Test Transform',
        owner_id: 'owner-1',
        input_dataset_ids: ['ds-1', 'ds-2'],
        output_dataset_id: 'ds-out-1',
        code: 'SELECT * FROM ds1 JOIN ds2',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<Transform> = {
        data: mockTransform,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await transformsApi.get('transform-1');

      expect(mockGet).toHaveBeenCalledWith('transforms/transform-1');
      expect(result).toEqual(mockTransform);
    });
  });

  describe('create', () => {
    it('Transformを作成する', async () => {
      const createData: TransformCreateRequest = {
        name: 'New Transform',
        input_dataset_ids: ['ds-1'],
        code: 'SELECT * FROM ds1',
      };

      const mockTransform: Transform = {
        id: 'transform-2',
        name: 'New Transform',
        owner_id: 'owner-1',
        input_dataset_ids: ['ds-1'],
        code: 'SELECT * FROM ds1',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<Transform> = {
        data: mockTransform,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await transformsApi.create(createData);

      expect(mockPost).toHaveBeenCalledWith('transforms', { json: createData });
      expect(result).toEqual(mockTransform);
    });
  });

  describe('update', () => {
    it('Transformを更新する', async () => {
      const updateData: TransformUpdateRequest = {
        name: 'Updated Transform',
        code: 'SELECT id FROM ds1',
      };

      const mockTransform: Transform = {
        id: 'transform-1',
        name: 'Updated Transform',
        owner_id: 'owner-1',
        input_dataset_ids: ['ds-1'],
        code: 'SELECT id FROM ds1',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<Transform> = {
        data: mockTransform,
      };

      mockPut.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await transformsApi.update('transform-1', updateData);

      expect(mockPut).toHaveBeenCalledWith('transforms/transform-1', { json: updateData });
      expect(result).toEqual(mockTransform);
    });
  });

  describe('delete', () => {
    it('Transformを削除する', async () => {
      mockDelete.mockResolvedValue(undefined);

      await transformsApi.delete('transform-1');

      expect(mockDelete).toHaveBeenCalledWith('transforms/transform-1');
    });
  });

  describe('execute', () => {
    it('Transformを実行して結果を取得する', async () => {
      const mockExecuteResponse: TransformExecuteResponse = {
        execution_id: 'exec-001',
        output_dataset_id: 'ds-out-1',
        row_count: 42,
        column_names: ['id', 'name', 'value'],
        execution_time_ms: 256,
      };

      const mockApiResponse: ApiResponse<TransformExecuteResponse> = {
        data: mockExecuteResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await transformsApi.execute('transform-1');

      expect(mockPost).toHaveBeenCalledWith('transforms/transform-1/execute', { json: {} });
      expect(result).toEqual(mockExecuteResponse);
    });
  });

  describe('listExecutions', () => {
    it('GET /transforms/{id}/executions を呼び出す', async () => {
      const mockResponse: PaginatedResponse<TransformExecution> = {
        data: [],
        pagination: { total: 0, limit: 20, offset: 0, has_next: false },
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await transformsApi.listExecutions('transform-1');

      expect(mockGet).toHaveBeenCalledWith('transforms/transform-1/executions', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('paginationパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<TransformExecution> = {
        data: [],
        pagination: { total: 0, limit: 10, offset: 5, has_next: false },
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await transformsApi.listExecutions('transform-1', { limit: 10, offset: 5 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('10');
      expect(searchParams.get('offset')).toBe('5');
    });
  });
});
