import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/react';
import { DashboardViewer } from '@/components/dashboard/DashboardViewer';
import type { DashboardDetail, CardExecuteResponse } from '@/types';

// Mock react-grid-layout
vi.mock('react-grid-layout', () => ({
  Responsive: ({ children }: any) => <div data-testid="grid-layout">{children}</div>,
  WidthProvider: (Component: any) => Component,
}));

// Mock dependencies
vi.mock('@/components/common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}));

vi.mock('@/components/dashboard/CardContainer', () => ({
  CardContainer: ({ cardId, html }: { cardId: string; html: string }) => (
    <div data-testid={`card-container-${cardId}`}>{html}</div>
  ),
}));

describe('DashboardViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('カードがない場合はメッセージを表示する', () => {
    const dashboard: DashboardDetail = {
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
      card_count: 0,
      owner: { user_id: 'user-1', name: 'Test User' },
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      cards: [],
    };

    render(<DashboardViewer dashboard={dashboard} onExecuteCard={vi.fn()} />);

    expect(screen.getByText('カードがまだ配置されていません')).toBeInTheDocument();
  });

  it('カードの読み込み中はスピナーを表示する', () => {
    const dashboard: DashboardDetail = {
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
      card_count: 1,
      owner: { user_id: 'user-1', name: 'Test User' },
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      cards: [],
      layout: {
        columns: 12,
        row_height: 100,
        cards: [
          { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
        ],
      },
    };

    const mockExecute = vi.fn(() => new Promise(() => {})); // Never resolves

    render(<DashboardViewer dashboard={dashboard} onExecuteCard={mockExecute} />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('マウント時にonExecuteCardを各カードに対して呼ぶ', () => {
    const dashboard: DashboardDetail = {
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
      card_count: 2,
      owner: { user_id: 'user-1', name: 'Test User' },
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      cards: [],
      layout: {
        columns: 12,
        row_height: 100,
        cards: [
          { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
          { card_id: 'card-2', x: 6, y: 0, w: 6, h: 4 },
        ],
      },
    };

    const mockExecute = vi.fn(() => Promise.resolve({
      card_id: 'card-1',
      html: '<div>Result</div>',
      cached: false,
      execution_time_ms: 100,
    }));

    render(<DashboardViewer dashboard={dashboard} onExecuteCard={mockExecute} />);

    expect(mockExecute).toHaveBeenCalledWith('card-1');
    expect(mockExecute).toHaveBeenCalledWith('card-2');
  });

  it('実行成功後にCardContainerを表示する', async () => {
    const dashboard: DashboardDetail = {
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
      card_count: 1,
      owner: { user_id: 'user-1', name: 'Test User' },
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      cards: [],
      layout: {
        columns: 12,
        row_height: 100,
        cards: [
          { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
        ],
      },
    };

    const mockResult: CardExecuteResponse = {
      card_id: 'card-1',
      html: '<div>Test Result</div>',
      cached: false,
      execution_time_ms: 100,
    };

    const mockExecute = vi.fn(() => Promise.resolve(mockResult));

    render(<DashboardViewer dashboard={dashboard} onExecuteCard={mockExecute} />);

    await waitFor(() => {
      const container = screen.getByTestId('card-container-card-1');
      expect(container).toHaveTextContent('Test Result');
    });
  });

  it('実行失敗時にエラーHTMLを表示する', async () => {
    const dashboard: DashboardDetail = {
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
      card_count: 1,
      owner: { user_id: 'user-1', name: 'Test User' },
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      cards: [],
      layout: {
        columns: 12,
        row_height: 100,
        cards: [
          { card_id: 'card-1', x: 0, y: 0, w: 6, h: 4 },
        ],
      },
    };

    const mockExecute = vi.fn(() => Promise.reject(new Error('Execution failed')));

    render(<DashboardViewer dashboard={dashboard} onExecuteCard={mockExecute} />);

    await waitFor(() => {
      const container = screen.getByTestId('card-container-card-1');
      expect(container).toHaveTextContent('読み込みエラー');
    });
  });
});
