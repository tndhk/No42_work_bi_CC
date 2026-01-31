import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterBar } from '@/components/dashboard/FilterBar';
import type { FilterDefinition } from '@/types';

// Mock child components
vi.mock('@/components/dashboard/filters/CategoryFilter', () => ({
  CategoryFilter: ({ filter }: { filter: FilterDefinition }) => (
    <div data-testid={`category-filter-${filter.id}`}>{filter.label}</div>
  ),
}));

vi.mock('@/components/dashboard/filters/DateRangeFilter', () => ({
  DateRangeFilter: ({ filter }: { filter: FilterDefinition }) => (
    <div data-testid={`date-filter-${filter.id}`}>{filter.label}</div>
  ),
}));

describe('FilterBar', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  const categoryFilter: FilterDefinition = {
    id: 'f1',
    type: 'category',
    column: 'region',
    label: '地域',
    options: ['East', 'West'],
  };

  const dateFilter: FilterDefinition = {
    id: 'f2',
    type: 'date_range',
    column: 'date',
    label: '日付',
  };

  it('フィルタが空の場合はnullを返す', () => {
    const { container } = render(
      <FilterBar filters={[]} values={{}} onFilterChange={vi.fn()} onClearAll={vi.fn()} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('カテゴリフィルタをレンダリングする', () => {
    render(
      <FilterBar
        filters={[categoryFilter]}
        values={{}}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByTestId('category-filter-f1')).toBeInTheDocument();
  });

  it('日付範囲フィルタをレンダリングする', () => {
    render(
      <FilterBar
        filters={[dateFilter]}
        values={{}}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByTestId('date-filter-f2')).toBeInTheDocument();
  });

  it('複数フィルタを同時にレンダリングする', () => {
    render(
      <FilterBar
        filters={[categoryFilter, dateFilter]}
        values={{}}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByTestId('category-filter-f1')).toBeInTheDocument();
    expect(screen.getByTestId('date-filter-f2')).toBeInTheDocument();
  });

  it('アクティブフィルタがない場合はクリアボタンを表示しない', () => {
    render(
      <FilterBar
        filters={[categoryFilter]}
        values={{}}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.queryByText('クリア')).not.toBeInTheDocument();
  });

  it('アクティブフィルタがある場合はクリアボタンを表示する', () => {
    render(
      <FilterBar
        filters={[categoryFilter]}
        values={{ f1: 'East' }}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByText('クリア')).toBeInTheDocument();
  });

  it('クリアボタンクリックでonClearAllが呼ばれる', async () => {
    const user = userEvent.setup();
    const onClearAll = vi.fn();

    render(
      <FilterBar
        filters={[categoryFilter]}
        values={{ f1: 'East' }}
        onFilterChange={vi.fn()}
        onClearAll={onClearAll}
      />
    );

    await user.click(screen.getByText('クリア'));
    expect(onClearAll).toHaveBeenCalledOnce();
  });

  it('data-testid="filter-bar"がある', () => {
    render(
      <FilterBar
        filters={[categoryFilter]}
        values={{}}
        onFilterChange={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByTestId('filter-bar')).toBeInTheDocument();
  });
});
