import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AddCardDialog } from '@/components/dashboard/AddCardDialog';
import { createMockCard, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';

// Mock useCards hook
vi.mock('@/hooks', () => ({
  useCards: vi.fn(),
}));

import { useCards } from '@/hooks';
const mockUseCards = useCards as ReturnType<typeof vi.fn>;

describe('AddCardDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('open=trueで「カードを追加」タイトルを表示する', () => {
    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={vi.fn()}
        existingCardIds={[]}
      />
    );

    expect(screen.getByText('カードを追加')).toBeInTheDocument();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseCards.mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={vi.fn()}
        existingCardIds={[]}
      />
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('利用可能なカードの一覧を表示する', () => {
    const cards = [
      createMockCard({ card_id: 'card-1', name: 'Card 1' }),
      createMockCard({ card_id: 'card-2', name: 'Card 2' }),
    ];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    } as any);

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={vi.fn()}
        existingCardIds={[]}
      />
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
  });

  it('既に配置済みのカードは除外する', () => {
    const cards = [
      createMockCard({ card_id: 'card-1', name: 'Card 1' }),
      createMockCard({ card_id: 'card-2', name: 'Card 2' }),
      createMockCard({ card_id: 'card-3', name: 'Card 3' }),
    ];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    });

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={vi.fn()}
        existingCardIds={['card-2']}
      />
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.queryByText('Card 2')).not.toBeInTheDocument();
    expect(screen.getByText('Card 3')).toBeInTheDocument();
  });

  it('カードがない場合はメッセージを表示する', () => {
    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    });

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={vi.fn()}
        existingCardIds={[]}
      />
    );

    expect(screen.getByText('追加可能なカードがありません')).toBeInTheDocument();
  });

  it('カードクリックでonSelectが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnSelect = vi.fn();
    const cards = [
      createMockCard({ card_id: 'card-1', name: 'Card 1' }),
    ];

    mockUseCards.mockReturnValue({
      data: createMockPaginatedResponse(cards),
      isLoading: false,
    });

    render(
      <AddCardDialog
        open={true}
        onOpenChange={vi.fn()}
        onSelect={mockOnSelect}
        existingCardIds={[]}
      />
    );

    const cardButton = screen.getByText('Card 1').closest('button');
    if (cardButton) {
      await user.click(cardButton);
    }

    expect(mockOnSelect).toHaveBeenCalledWith('card-1');
  });
});
