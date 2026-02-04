import { describe, it, expect, vi, beforeEach } from 'vitest';
import { cardsApi } from '@/lib/api/cards';
import type {
  Card,
  CardDetail,
  CardCreateRequest,
  CardUpdateRequest,
  CardExecuteResponse,
  CardPreviewResponse,
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

describe('cardsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('パラメータなしでGETリクエストを送信する', async () => {
      const mockResponse: PaginatedResponse<Card> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await cardsApi.list();

      expect(mockGet).toHaveBeenCalledWith('cards', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('limit/offset/ownerのパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<Card> = {
        items: [],
        total: 0,
        limit: 20,
        offset: 10,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await cardsApi.list({ limit: 20, offset: 10, owner: 'user-1' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('20');
      expect(searchParams.get('offset')).toBe('10');
      expect(searchParams.get('owner')).toBe('user-1');
    });

    it('offset=0でもパラメータが送信される', async () => {
      const mockResponse: PaginatedResponse<Card> = {
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await cardsApi.list({ limit: 10, offset: 0 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('10');
      expect(searchParams.get('offset')).toBe('0');
    });
  });

  describe('get', () => {
    it('指定IDのカード詳細を取得する', async () => {
      const mockCard: CardDetail = {
        card_id: 'card-1',
        name: 'Test Card',
        code: 'print("test")',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<CardDetail> = {
        data: mockCard,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.get('card-1');

      expect(mockGet).toHaveBeenCalledWith('cards/card-1');
      expect(result).toEqual(mockCard);
    });
  });

  describe('create', () => {
    it('カードを作成する', async () => {
      const createData: CardCreateRequest = {
        name: 'New Card',
        dataset_id: 'dataset-1',
        code: 'print("hello")',
      };

      const mockCard: CardDetail = {
        card_id: 'card-2',
        name: 'New Card',
        code: 'print("hello")',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<CardDetail> = {
        data: mockCard,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.create(createData);

      expect(mockPost).toHaveBeenCalledWith('cards', { json: createData });
      expect(result).toEqual(mockCard);
    });
  });

  describe('update', () => {
    it('カードを更新する', async () => {
      const updateData: CardUpdateRequest = {
        name: 'Updated Card',
        code: 'print("updated")',
      };

      const mockCard: CardDetail = {
        card_id: 'card-1',
        name: 'Updated Card',
        code: 'print("updated")',
        owner: { user_id: 'owner-1', name: 'Owner' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-02T00:00:00Z',
      };

      const mockApiResponse: ApiResponse<CardDetail> = {
        data: mockCard,
      };

      mockPut.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.update('card-1', updateData);

      expect(mockPut).toHaveBeenCalledWith('cards/card-1', { json: updateData });
      expect(result).toEqual(mockCard);
    });
  });

  describe('delete', () => {
    it('カードを削除する', async () => {
      mockDelete.mockResolvedValue(undefined);

      await cardsApi.delete('card-1');

      expect(mockDelete).toHaveBeenCalledWith('cards/card-1');
    });
  });

  describe('execute', () => {
    it('カードを実行してHTMLを取得する', async () => {
      const executeData = { filters: { year: 2026 }, use_cache: true };

      const mockExecuteResponse: CardExecuteResponse = {
        card_id: 'card-1',
        html: '<div>Result</div>',
        cached: false,
        execution_time_ms: 123,
      };

      const mockApiResponse: ApiResponse<CardExecuteResponse> = {
        data: mockExecuteResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.execute('card-1', executeData);

      expect(mockPost).toHaveBeenCalledWith('cards/card-1/execute', { json: executeData });
      expect(result).toEqual(mockExecuteResponse);
    });

    it('dataなしでも実行できる', async () => {
      const mockExecuteResponse: CardExecuteResponse = {
        card_id: 'card-1',
        html: '<div>Result</div>',
        cached: false,
        execution_time_ms: 123,
      };

      const mockApiResponse: ApiResponse<CardExecuteResponse> = {
        data: mockExecuteResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.execute('card-1');

      expect(mockPost).toHaveBeenCalledWith('cards/card-1/execute', { json: {} });
      expect(result).toEqual(mockExecuteResponse);
    });
  });

  describe('preview', () => {
    it('カードプレビューを取得する', async () => {
      const filters = { year: 2026 };

      const mockPreviewResponse: CardPreviewResponse = {
        card_id: 'card-1',
        html: '<div>Preview</div>',
        execution_time_ms: 50,
        input_row_count: 100,
        filtered_row_count: 80,
      };

      const mockApiResponse: ApiResponse<CardPreviewResponse> = {
        data: mockPreviewResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.preview('card-1', filters);

      expect(mockPost).toHaveBeenCalledWith('cards/card-1/preview', { json: { filters } });
      expect(result).toEqual(mockPreviewResponse);
    });

    it('フィルターなしでも呼べる', async () => {
      const mockPreviewResponse: CardPreviewResponse = {
        card_id: 'card-1',
        html: '<div>Preview</div>',
        execution_time_ms: 50,
        input_row_count: 100,
        filtered_row_count: 100,
      };

      const mockApiResponse: ApiResponse<CardPreviewResponse> = {
        data: mockPreviewResponse,
      };

      mockPost.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockApiResponse),
      });

      const result = await cardsApi.preview('card-1');

      expect(mockPost).toHaveBeenCalledWith('cards/card-1/preview', { json: { filters: {} } });
      expect(result).toEqual(mockPreviewResponse);
    });
  });
});
