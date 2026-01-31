import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useCards,
  useCard,
  useCreateCard,
  useUpdateCard,
  useDeleteCard,
  useExecuteCard,
  usePreviewCard,
} from '@/hooks/use-cards';
import { createWrapper, createMockCard, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';
import type {
  CardDetail,
  CardCreateRequest,
  CardUpdateRequest,
  CardExecuteResponse,
  CardPreviewResponse,
} from '@/types';

// Mock cardsApi
vi.mock('@/lib/api', () => ({
  cardsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    execute: vi.fn(),
    preview: vi.fn(),
  },
}));

import { cardsApi } from '@/lib/api';
const mockList = cardsApi.list as ReturnType<typeof vi.fn>;
const mockGet = cardsApi.get as ReturnType<typeof vi.fn>;
const mockCreate = cardsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = cardsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = cardsApi.delete as ReturnType<typeof vi.fn>;
const mockExecute = cardsApi.execute as ReturnType<typeof vi.fn>;
const mockPreview = cardsApi.preview as ReturnType<typeof vi.fn>;

describe('useCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('カード一覧を取得する', async () => {
    const mockCards = [createMockCard(), createMockCard({ card_id: 'card-2' })];
    const mockResponse = createMockPaginatedResponse(mockCards);

    mockList.mockResolvedValue(mockResponse.data);

    const { result } = renderHook(() => useCards(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(undefined);
    expect(result.current.data).toEqual(mockResponse.data);
  });
});

describe('useCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('カード詳細を取得する', async () => {
    const mockCard: CardDetail = {
      ...createMockCard(),
      code: 'print("test")',
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockGet.mockResolvedValue(mockCard);

    const { result } = renderHook(() => useCard('card-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGet).toHaveBeenCalledWith('card-1');
    expect(result.current.data).toEqual(mockCard);
  });

  it('IDが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useCard(''), { wrapper: createWrapper() });

    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useCreateCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にcardsクエリを無効化する', async () => {
    const createData: CardCreateRequest = {
      name: 'New Card',
      dataset_id: 'dataset-1',
      code: 'print("hello")',
    };

    const mockCard: CardDetail = {
      ...createMockCard({ card_id: 'card-new', name: 'New Card' }),
      code: 'print("hello")',
      updated_at: '2026-01-01T00:00:00Z',
    };

    mockCreate.mockResolvedValue(mockCard);

    const { result } = renderHook(() => useCreateCard(), { wrapper: createWrapper() });

    result.current.mutate(createData);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockCreate).toHaveBeenCalledWith(createData);
    expect(result.current.data).toEqual(mockCard);
  });
});

describe('useUpdateCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にcardsと個別クエリを無効化する', async () => {
    const updateData: CardUpdateRequest = { name: 'Updated Card' };
    const mockCard: CardDetail = {
      ...createMockCard({ name: 'Updated Card' }),
      code: 'print("test")',
      updated_at: '2026-01-02T00:00:00Z',
    };

    mockUpdate.mockResolvedValue(mockCard);

    const { result } = renderHook(() => useUpdateCard(), { wrapper: createWrapper() });

    result.current.mutate({ cardId: 'card-1', data: updateData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockUpdate).toHaveBeenCalledWith('card-1', updateData);
    expect(result.current.data).toEqual(mockCard);
  });
});

describe('useDeleteCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にcardsクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteCard(), { wrapper: createWrapper() });

    result.current.mutate('card-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockDelete).toHaveBeenCalledWith('card-1');
  });
});

describe('useExecuteCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('カード実行リクエストを送信する', async () => {
    const executeData = { filters: { year: 2026 } };
    const mockResponse: CardExecuteResponse = {
      card_id: 'card-1',
      html: '<div>Result</div>',
      cached: false,
      execution_time_ms: 123,
    };

    mockExecute.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useExecuteCard(), { wrapper: createWrapper() });

    result.current.mutate({ cardId: 'card-1', data: executeData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockExecute).toHaveBeenCalledWith('card-1', executeData);
    expect(result.current.data).toEqual(mockResponse);
  });
});

describe('usePreviewCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('カードプレビューリクエストを送信する', async () => {
    const filters = { year: 2026 };
    const mockResponse: CardPreviewResponse = {
      card_id: 'card-1',
      html: '<div>Preview</div>',
      execution_time_ms: 50,
      input_row_count: 100,
      filtered_row_count: 80,
    };

    mockPreview.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => usePreviewCard(), { wrapper: createWrapper() });

    result.current.mutate({ cardId: 'card-1', filters });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockPreview).toHaveBeenCalledWith('card-1', filters);
    expect(result.current.data).toEqual(mockResponse);
  });
});
