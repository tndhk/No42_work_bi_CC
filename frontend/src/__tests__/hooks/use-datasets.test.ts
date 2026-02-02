import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useDatasets,
  useDataset,
  useDatasetPreview,
  useCreateDataset,
  useUpdateDataset,
  useDeleteDataset,
  useS3ImportDataset,
} from '@/hooks/use-datasets';
import { createWrapper, createMockDataset, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';
import type { DatasetDetail, DatasetPreview, DatasetUpdateRequest, S3ImportRequest } from '@/types';

// Mock datasetsApi
vi.mock('@/lib/api', () => ({
  datasetsApi: {
    list: vi.fn(),
    get: vi.fn(),
    preview: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    s3Import: vi.fn(),
  },
}));

import { datasetsApi } from '@/lib/api';
const mockList = datasetsApi.list as ReturnType<typeof vi.fn>;
const mockGet = datasetsApi.get as ReturnType<typeof vi.fn>;
const mockPreview = datasetsApi.preview as ReturnType<typeof vi.fn>;
const mockCreate = datasetsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = datasetsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = datasetsApi.delete as ReturnType<typeof vi.fn>;
const mockS3Import = datasetsApi.s3Import as ReturnType<typeof vi.fn>;

describe('useDatasets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('データセット一覧を取得する', async () => {
    const mockDatasets = [createMockDataset(), createMockDataset({ dataset_id: 'dataset-2' })];
    const mockResponse = createMockPaginatedResponse(mockDatasets);

    mockList.mockResolvedValue(mockResponse.data);

    const { result } = renderHook(() => useDatasets(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(undefined);
    expect(result.current.data).toEqual(mockResponse.data);
  });
});

describe('useDataset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('データセット詳細を取得する', async () => {
    const mockDataset: DatasetDetail = {
      ...createMockDataset(),
      schema: [],
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockGet.mockResolvedValue(mockDataset);

    const { result } = renderHook(() => useDataset('dataset-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGet).toHaveBeenCalledWith('dataset-1');
    expect(result.current.data).toEqual(mockDataset);
  });

  it('IDが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useDataset(''), { wrapper: createWrapper() });

    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useDatasetPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('プレビューデータを取得する', async () => {
    const mockPreviewData: DatasetPreview = {
      columns: ['col1', 'col2'],
      rows: [['val1', 'val2']],
      total_rows: 100,
      preview_rows: 1,
    };

    mockPreview.mockResolvedValue(mockPreviewData);

    const { result } = renderHook(() => useDatasetPreview('dataset-1', 10), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockPreview).toHaveBeenCalledWith('dataset-1', 10);
    expect(result.current.data).toEqual(mockPreviewData);
  });
});

describe('useCreateDataset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdatasetsクエリを無効化する', async () => {
    const mockDataset: DatasetDetail = {
      ...createMockDataset({ dataset_id: 'dataset-new' }),
      schema: [],
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockCreate.mockResolvedValue(mockDataset);

    const { result } = renderHook(() => useCreateDataset(), { wrapper: createWrapper() });

    const formData = new FormData();
    formData.append('name', 'New Dataset');

    result.current.mutate(formData);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockCreate).toHaveBeenCalledWith(formData);
    expect(result.current.data).toEqual(mockDataset);
  });
});

describe('useUpdateDataset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdatasetsと個別クエリを無効化する', async () => {
    const updateData: DatasetUpdateRequest = { name: 'Updated Dataset' };
    const mockDataset: DatasetDetail = {
      ...createMockDataset({ name: 'Updated Dataset' }),
      schema: [],
      updated_at: '2026-01-02T00:00:00Z',
    };

    mockUpdate.mockResolvedValue(mockDataset);

    const { result } = renderHook(() => useUpdateDataset(), { wrapper: createWrapper() });

    result.current.mutate({ datasetId: 'dataset-1', data: updateData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockUpdate).toHaveBeenCalledWith('dataset-1', updateData);
    expect(result.current.data).toEqual(mockDataset);
  });
});

describe('useDeleteDataset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdatasetsクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteDataset(), { wrapper: createWrapper() });

    result.current.mutate('dataset-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockDelete).toHaveBeenCalledWith('dataset-1');
  });
});

describe('useS3ImportDataset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('S3インポートAPIを呼び出してデータセットを作成する', async () => {
    const mockDataset: DatasetDetail = {
      ...createMockDataset({ dataset_id: 'ds-imported', name: 'S3 Imported', source_type: 's3_csv' }),
      schema: [],
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockS3Import.mockResolvedValue(mockDataset);

    const { result } = renderHook(() => useS3ImportDataset(), { wrapper: createWrapper() });

    const importRequest: S3ImportRequest = {
      name: 'test-dataset',
      s3_bucket: 'my-bucket',
      s3_key: 'data/file.csv',
    };

    result.current.mutate(importRequest);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockS3Import).toHaveBeenCalledWith(importRequest);
    expect(result.current.data).toEqual(mockDataset);
  });

  it('オプションパラメータ付きでS3インポートを呼び出す', async () => {
    const mockDataset: DatasetDetail = {
      ...createMockDataset({ dataset_id: 'ds-imported-2', name: 'S3 TSV', source_type: 's3_csv' }),
      schema: [],
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockS3Import.mockResolvedValue(mockDataset);

    const { result } = renderHook(() => useS3ImportDataset(), { wrapper: createWrapper() });

    const importRequest: S3ImportRequest = {
      name: 'tsv-dataset',
      s3_bucket: 'my-bucket',
      s3_key: 'data/file.tsv',
      has_header: true,
      delimiter: '\t',
    };

    result.current.mutate(importRequest);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockS3Import).toHaveBeenCalledWith(importRequest);
    expect(result.current.data).toEqual(mockDataset);
  });

  it('エラー時にisErrorがtrueになる', async () => {
    mockS3Import.mockRejectedValue(new Error('S3 bucket not found'));

    const { result } = renderHook(() => useS3ImportDataset(), { wrapper: createWrapper() });

    result.current.mutate({
      name: 'fail-dataset',
      s3_bucket: 'nonexistent-bucket',
      s3_key: 'data/file.csv',
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('S3 bucket not found');
  });
});
