import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { cardsApi } from '@/lib/api';
import type {
  CardCreateRequest,
  CardUpdateRequest,
  CardExecuteRequest,
  PaginationParams,
} from '@/types';

export function useCards(params?: PaginationParams & { owner?: string }) {
  return useQuery({
    queryKey: ['cards', params],
    queryFn: () => cardsApi.list(params),
  });
}

export function useCard(cardId: string) {
  return useQuery({
    queryKey: ['cards', cardId],
    queryFn: () => cardsApi.get(cardId),
    enabled: !!cardId,
  });
}

export function useCreateCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CardCreateRequest) => cardsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    },
  });
}

export function useUpdateCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cardId, data }: { cardId: string; data: CardUpdateRequest }) =>
      cardsApi.update(cardId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
      queryClient.invalidateQueries({ queryKey: ['cards', variables.cardId] });
    },
  });
}

export function useDeleteCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (cardId: string) => cardsApi.delete(cardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    },
  });
}

export function useExecuteCard() {
  return useMutation({
    mutationFn: ({ cardId, data }: { cardId: string; data?: CardExecuteRequest }) =>
      cardsApi.execute(cardId, data),
  });
}

export function usePreviewCard() {
  return useMutation({
    mutationFn: ({ cardId, filters }: { cardId: string; filters?: Record<string, unknown> }) =>
      cardsApi.preview(cardId, filters),
  });
}

export function useCardData(cardId: string, limit?: number) {
  return useQuery({
    queryKey: ['cards', cardId, 'data', limit],
    queryFn: () => cardsApi.getData(cardId, limit),
    enabled: !!cardId,
  });
}
