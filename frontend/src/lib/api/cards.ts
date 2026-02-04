import { apiClient } from '@/lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  PaginationParams,
  Card,
  CardDetail,
  CardCreateRequest,
  CardUpdateRequest,
  CardExecuteRequest,
  CardExecuteResponse,
  CardPreviewResponse,
} from '@/types';

export const cardsApi = {
  list: async (params?: PaginationParams & { owner?: string }): Promise<PaginatedResponse<Card>> => {
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    if (params?.owner) searchParams.set('owner', params.owner);
    return apiClient.get('cards', { searchParams }).json<PaginatedResponse<Card>>();
  },

  get: async (cardId: string): Promise<CardDetail> => {
    const response = await apiClient.get(`cards/${cardId}`).json<ApiResponse<CardDetail>>();
    return response.data;
  },

  create: async (data: CardCreateRequest): Promise<CardDetail> => {
    const response = await apiClient.post('cards', { json: data }).json<ApiResponse<CardDetail>>();
    return response.data;
  },

  update: async (cardId: string, data: CardUpdateRequest): Promise<CardDetail> => {
    const response = await apiClient.put(`cards/${cardId}`, { json: data }).json<ApiResponse<CardDetail>>();
    return response.data;
  },

  delete: async (cardId: string): Promise<void> => {
    await apiClient.delete(`cards/${cardId}`);
  },

  execute: async (cardId: string, data?: CardExecuteRequest): Promise<CardExecuteResponse> => {
    const response = await apiClient.post(`cards/${cardId}/execute`, { json: data || {} }).json<ApiResponse<CardExecuteResponse>>();
    return response.data;
  },

  preview: async (cardId: string, filters?: Record<string, unknown>): Promise<CardPreviewResponse> => {
    const response = await apiClient.post(`cards/${cardId}/preview`, { json: { filters: filters || {} } }).json<ApiResponse<CardPreviewResponse>>();
    return response.data;
  },
};
