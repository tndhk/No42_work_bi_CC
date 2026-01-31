import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CardListPage } from '@/pages/CardListPage';
import { createWrapper, createMockCard, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/hooks', () => ({
  useCards: vi.fn(),
  useDeleteCard: vi.fn(() => ({ mutate: mockDeleteMutate })),
}));

import { useCards } from '@/hooks';
const mockUseCards = useCards as ReturnType<typeof vi.fn>;

describe('CardListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseCards.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('カード一覧をテーブルに表示する', () => {
    const cards = [
      createMockCard({ card_id: 'card-1', name: 'Card 1' }),
      createMockCard({ card_id: 'card-2', name: 'Card 2' }),
    ];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
  });

  it('カードがない場合はメッセージを表示する', () => {
    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('カードがありません')).toBeInTheDocument();
  });

  it('新規作成ボタンがある', () => {
    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('button', { name: /新規作成/ })).toBeInTheDocument();
  });

  it('編集ボタンクリックで遷移する', async () => {
    const cards = [createMockCard({ card_id: 'card-1', name: 'Card 1' })];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('削除ボタンクリックで確認ダイアログを表示する', () => {
    const cards = [createMockCard({ card_id: 'card-1', name: 'Card 1' })];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('ページネーションが表示される', () => {
    const cards = Array.from({ length: 10 }, (_, i) =>
      createMockCard({ card_id: `card-${i}` })
    );

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards, 100),
      isLoading: false,
    } as any);

    render(<MemoryRouter><CardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText(/100件中/)).toBeInTheDocument();
  });
});
