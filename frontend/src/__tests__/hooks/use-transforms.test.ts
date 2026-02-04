import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useTransforms,
  useTransform,
  useCreateTransform,
  useUpdateTransform,
  useDeleteTransform,
  useExecuteTransform,
  useTransformExecutions,
} from '@/hooks/use-transforms';
import { createWrapper, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';
import type {
  Transform,
  TransformCreateRequest,
  TransformUpdateRequest,
  TransformExecuteResponse,
} from '@/types';

// Mock transformsApi
vi.mock('@/lib/api', () => ({
  transformsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    execute: vi.fn(),
    listExecutions: vi.fn(),
  },
}));

import { transformsApi } from '@/lib/api';
const mockList = transformsApi.list as ReturnType<typeof vi.fn>;
const mockGet = transformsApi.get as ReturnType<typeof vi.fn>;
const mockCreate = transformsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = transformsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = transformsApi.delete as ReturnType<typeof vi.fn>;
const mockExecute = transformsApi.execute as ReturnType<typeof vi.fn>;
const mockListExecutions = transformsApi.listExecutions as ReturnType<typeof vi.fn>;

function createMockTransform(overrides?: Partial<Transform>): Transform {
  return {
    id: 'transform-1',
    name: 'Test Transform',
    owner_id: 'owner-id',
    input_dataset_ids: ['dataset-1'],
    code: 'df.groupby("col").sum()',
    owner: { user_id: 'owner-id', name: 'Test Owner' },
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useTransforms', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transform一覧を取得する', async () => {
    const mockTransforms = [
      createMockTransform(),
      createMockTransform({ id: 'transform-2', name: 'Second Transform' }),
    ];
    const mockResponse = createMockPaginatedResponse(mockTransforms);

    mockList.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useTransforms(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(undefined);
    expect(result.current.data).toEqual(mockResponse);
  });

  it('パラメータ付きでTransform一覧を取得する', async () => {
    const params = { limit: 10, offset: 0 };
    const mockResponse = createMockPaginatedResponse([createMockTransform()]);

    mockList.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useTransforms(params), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(params);
  });
});

describe('useTransform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transform詳細を取得する', async () => {
    const mockTransform = createMockTransform();

    mockGet.mockResolvedValue(mockTransform);

    const { result } = renderHook(() => useTransform('transform-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGet).toHaveBeenCalledWith('transform-1');
    expect(result.current.data).toEqual(mockTransform);
  });

  it('IDが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useTransform(''), { wrapper: createWrapper() });

    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useCreateTransform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transformを作成し成功時にtransformsクエリを無効化する', async () => {
    const createData: TransformCreateRequest = {
      name: 'New Transform',
      input_dataset_ids: ['dataset-1'],
      code: 'df.head()',
    };

    const mockTransform = createMockTransform({
      id: 'transform-new',
      name: 'New Transform',
      code: 'df.head()',
    });

    mockCreate.mockResolvedValue(mockTransform);

    const { result } = renderHook(() => useCreateTransform(), { wrapper: createWrapper() });

    result.current.mutate(createData);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockCreate).toHaveBeenCalledWith(createData);
    expect(result.current.data).toEqual(mockTransform);
  });
});

describe('useUpdateTransform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transformを更新し成功時にtransformsと個別クエリを無効化する', async () => {
    const updateData: TransformUpdateRequest = { name: 'Updated Transform' };
    const mockTransform = createMockTransform({
      name: 'Updated Transform',
      updated_at: '2026-01-02T00:00:00Z',
    });

    mockUpdate.mockResolvedValue(mockTransform);

    const { result } = renderHook(() => useUpdateTransform(), { wrapper: createWrapper() });

    result.current.mutate({ transformId: 'transform-1', data: updateData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockUpdate).toHaveBeenCalledWith('transform-1', updateData);
    expect(result.current.data).toEqual(mockTransform);
  });
});

describe('useDeleteTransform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transformを削除し成功時にtransformsクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteTransform(), { wrapper: createWrapper() });

    result.current.mutate('transform-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockDelete).toHaveBeenCalledWith('transform-1');
  });
});

describe('useExecuteTransform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Transform実行リクエストを送信する', async () => {
    const mockResponse: TransformExecuteResponse = {
      execution_id: 'exec-001',
      output_dataset_id: 'output-dataset-1',
      row_count: 50,
      column_names: ['col1', 'col2'],
      execution_time_ms: 200,
    };

    mockExecute.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useExecuteTransform(), { wrapper: createWrapper() });

    result.current.mutate('transform-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockExecute).toHaveBeenCalledWith('transform-1');
    expect(result.current.data).toEqual(mockResponse);
  });
});

describe('useTransformExecutions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('transformIdを指定して実行履歴を取得する', async () => {
    const mockExecution = {
      execution_id: 'exec-001',
      transform_id: 'transform-1',
      status: 'success',
      started_at: '2026-02-04T10:00:00Z',
      finished_at: '2026-02-04T10:00:05Z',
      duration_ms: 5000,
      output_row_count: 100,
      triggered_by: 'manual',
    };
    const mockResponse = createMockPaginatedResponse([mockExecution]);
    mockListExecutions.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useTransformExecutions('transform-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockListExecutions).toHaveBeenCalledWith('transform-1', undefined);
    expect(result.current.data).toEqual(mockResponse);
  });

  it('transformIdが空の場合はクエリを無効化する', async () => {
    const { result } = renderHook(() => useTransformExecutions(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockListExecutions).not.toHaveBeenCalled();
  });
});
