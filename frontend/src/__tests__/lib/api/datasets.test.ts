import { describe, it, expect, vi, beforeEach } from 'vitest';
import { datasetsApi } from '@/lib/api/datasets';
import type { Dataset, DatasetDetail, DatasetPreview, ApiResponse, PaginatedResponse, S3ImportRequest } from '@/types';

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

describe('datasetsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('パラメータなしでGETリクエストを送信する', async () => {
      const mockResponse: PaginatedResponse<Dataset> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await datasetsApi.list();

      expect(mockGet).toHaveBeenCalledWith('datasets', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('limit/offset/ownerのパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<Dataset> = {
        items: [],
        total: 0,
        limit: 20,
        offset: 10,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await datasetsApi.list({ limit: 20, offset: 10, owner: 'user-1' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('20');
      expect(searchParams.get('offset')).toBe('10');
      expect(searchParams.get('owner')).toBe('user-1');
    });
  });

  describe('get', () => {
    it('指定IDのデータセット詳細を取得する', async () => {
      const mockDataset: DatasetDetail = {
        dataset_id: 'dataset-1',
        name: 'Test Dataset',
        source_type: 'csv',
        row_count: 100,
        column_count: 5,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        schema: [],
      };

      const mockApiResponse: ApiResponse<DatasetDetail> = {
        data: mockDataset,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await datasetsApi.get('dataset-1');

      expect(mockGet).toHaveBeenCalledWith('datasets/dataset-1');
      expect(result).toEqual(mockDataset);
    });
  });

  describe('create', () => {
    it('FormDataをPOSTしてデータセットを作成する', async () => {
      const formData = new FormData();
      formData.append('name', 'New Dataset');

      const mockDataset: DatasetDetail = {
        dataset_id: 'dataset-2',
        name: 'New Dataset',
        source_type: 'csv',
        row_count: 0,
        column_count: 0,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        schema: [],
      };

      const mockApiResponse: ApiResponse<DatasetDetail> = {
        data: mockDataset,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await datasetsApi.create(formData);

      expect(mockPost).toHaveBeenCalledWith('datasets', { body: formData });
      expect(result).toEqual(mockDataset);
    });
  });

  describe('update', () => {
    it('PUTリクエストでデータセットを更新する', async () => {
      const updateData = { name: 'Updated Dataset' };

      const mockDataset: DatasetDetail = {
        dataset_id: 'dataset-1',
        name: 'Updated Dataset',
        source_type: 'csv',
        row_count: 100,
        column_count: 5,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z',
        schema: [],
      };

      const mockApiResponse: ApiResponse<DatasetDetail> = {
        data: mockDataset,
      };

      mockPut.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await datasetsApi.update('dataset-1', updateData);

      expect(mockPut).toHaveBeenCalledWith('datasets/dataset-1', { json: updateData });
      expect(result).toEqual(mockDataset);
    });
  });

  describe('delete', () => {
    it('DELETEリクエストでデータセットを削除する', async () => {
      mockDelete.mockResolvedValue(undefined);

      await datasetsApi.delete('dataset-1');

      expect(mockDelete).toHaveBeenCalledWith('datasets/dataset-1');
    });
  });

  describe('preview', () => {
    it('プレビューデータを取得する', async () => {
      const mockPreview: DatasetPreview = {
        columns: ['col1', 'col2'],
        rows: [['val1', 'val2']],
        total_rows: 100,
        preview_rows: 1,
      };

      const mockApiResponse: ApiResponse<DatasetPreview> = {
        data: mockPreview,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await datasetsApi.preview('dataset-1');

      expect(mockGet).toHaveBeenCalledWith('datasets/dataset-1/preview', {
        searchParams: expect.any(URLSearchParams),
      });
      expect(result).toEqual(mockPreview);
    });

    it('limitパラメータを渡せる', async () => {
      const mockPreview: DatasetPreview = {
        columns: [],
        rows: [],
        total_rows: 0,
        preview_rows: 0,
      };

      const mockApiResponse: ApiResponse<DatasetPreview> = {
        data: mockPreview,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      await datasetsApi.preview('dataset-1', 50);

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('50');
    });
  });

  describe('s3Import', () => {
    it('S3インポートデータをPOSTリクエストで送信する', async () => {
      const mockDataset: DatasetDetail = {
        dataset_id: 'ds_test123',
        name: 'test-dataset',
        source_type: 's3_csv',
        row_count: 0,
        column_count: 0,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        schema: [],
      };

      const mockApiResponse: ApiResponse<DatasetDetail> = {
        data: mockDataset,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const importRequest: S3ImportRequest = {
        name: 'test-dataset',
        s3_bucket: 'my-bucket',
        s3_key: 'data/file.csv',
      };

      const result = await datasetsApi.s3Import(importRequest);

      expect(mockPost).toHaveBeenCalledWith('datasets/s3-import', {
        json: importRequest,
      });
      expect(result).toEqual(mockDataset);
      expect(result.name).toBe('test-dataset');
    });

    it('全オプションパラメータを含めてPOSTリクエストを送信する', async () => {
      const mockDataset: DatasetDetail = {
        dataset_id: 'ds_test456',
        name: 'full-dataset',
        source_type: 's3_csv',
        row_count: 0,
        column_count: 10,
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        schema: [],
      };

      const mockApiResponse: ApiResponse<DatasetDetail> = {
        data: mockDataset,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const importRequest: S3ImportRequest = {
        name: 'full-dataset',
        s3_bucket: 'my-bucket',
        s3_key: 'data/file.tsv',
        has_header: false,
        delimiter: '\t',
        encoding: 'shift_jis',
        partition_column: 'date',
      };

      const result = await datasetsApi.s3Import(importRequest);

      expect(mockPost).toHaveBeenCalledWith('datasets/s3-import', {
        json: importRequest,
      });
      expect(result).toEqual(mockDataset);
      expect(result.name).toBe('full-dataset');
    });
  });
});
