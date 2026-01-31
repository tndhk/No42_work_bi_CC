import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DashboardEditor } from '@/components/dashboard/DashboardEditor';
import type { DashboardLayout } from '@/types';

// Mock react-grid-layout
vi.mock('react-grid-layout', () => ({
  Responsive: ({ children, onLayoutChange }: any) => (
    <div data-testid="grid-layout" data-on-layout-change={!!onLayoutChange}>
      {children}
    </div>
  ),
  WidthProvider: (Component: any) => Component,
}));

describe('DashboardEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('カードがない場合はプレースホルダーを表示する', () => {
    const layout: DashboardLayout = {
      columns: 12,
      row_height: 100,
      cards: [],
    };

    render(
      <DashboardEditor
        layout={layout}
        onLayoutChange={vi.fn()}
        onRemoveCard={vi.fn()}
      />
    );

    expect(screen.getByText('カードを追加してダッシュボードを作成してください')).toBeInTheDocument();
  });

  it('カードのcard_idとサイズを表示する', () => {
    const layout: DashboardLayout = {
      columns: 12,
      row_height: 100,
      cards: [
        { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
        { card_id: 'card-2', x: 6, y: 0, w: 6, h: 3 },
      ],
    };

    render(
      <DashboardEditor
        layout={layout}
        onLayoutChange={vi.fn()}
        onRemoveCard={vi.fn()}
      />
    );

    expect(screen.getByText('card-1')).toBeInTheDocument();
    expect(screen.getByText('6x4')).toBeInTheDocument();
    expect(screen.getByText('card-2')).toBeInTheDocument();
    expect(screen.getByText('6x3')).toBeInTheDocument();
  });

  it('削除ボタンクリックでonRemoveCardが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnRemoveCard = vi.fn();
    const layout: DashboardLayout = {
      columns: 12,
      row_height: 100,
      cards: [
        { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
      ],
    };

    render(
      <DashboardEditor
        layout={layout}
        onLayoutChange={vi.fn()}
        onRemoveCard={mockOnRemoveCard}
      />
    );

    const deleteButton = screen.getByRole('button');
    await user.click(deleteButton);

    expect(mockOnRemoveCard).toHaveBeenCalledWith('card-1');
  });

  it('レイアウト変更でonLayoutChangeが呼ばれる', () => {
    const mockOnLayoutChange = vi.fn();
    const layout: DashboardLayout = {
      columns: 12,
      row_height: 100,
      cards: [
        { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
      ],
    };

    render(
      <DashboardEditor
        layout={layout}
        onLayoutChange={mockOnLayoutChange}
        onRemoveCard={vi.fn()}
      />
    );

    const gridLayout = screen.getByTestId('grid-layout');
    expect(gridLayout).toHaveAttribute('data-on-layout-change', 'true');
  });
});
