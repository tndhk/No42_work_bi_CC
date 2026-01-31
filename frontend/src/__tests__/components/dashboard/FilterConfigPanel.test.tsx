import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterConfigPanel } from '@/components/dashboard/FilterConfigPanel';
import type { FilterDefinition } from '@/types';

// Mock FilterDefinitionForm
vi.mock('@/components/dashboard/FilterDefinitionForm', () => ({
  FilterDefinitionForm: ({ onSubmit, onCancel }: any) => (
    <div data-testid="filter-form">
      <button onClick={() => onSubmit({ id: 'new-filter', type: 'category', column: 'col', label: 'New' })}>
        Submit
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

describe('FilterConfigPanel', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  const sampleFilters: FilterDefinition[] = [
    { id: 'f1', type: 'category', column: 'region', label: '地域' },
    { id: 'f2', type: 'date_range', column: 'date', label: '日付' },
  ];

  it('フィルタが空の場合はメッセージを表示する', () => {
    render(
      <FilterConfigPanel filters={[]} onFiltersChange={vi.fn()} datasetIds={[]} />
    );

    expect(screen.getByText('フィルタが設定されていません')).toBeInTheDocument();
  });

  it('フィルタ一覧を表示する', () => {
    render(
      <FilterConfigPanel filters={sampleFilters} onFiltersChange={vi.fn()} datasetIds={[]} />
    );

    expect(screen.getByText('地域')).toBeInTheDocument();
    expect(screen.getByText('日付')).toBeInTheDocument();
  });

  it('フィルタタイプのBadgeを表示する', () => {
    render(
      <FilterConfigPanel filters={sampleFilters} onFiltersChange={vi.fn()} datasetIds={[]} />
    );

    expect(screen.getByText('カテゴリ')).toBeInTheDocument();
    expect(screen.getByText('日付範囲')).toBeInTheDocument();
  });

  it('追加ボタンが存在する', () => {
    render(
      <FilterConfigPanel filters={[]} onFiltersChange={vi.fn()} datasetIds={[]} />
    );

    expect(screen.getByRole('button', { name: /追加/ })).toBeInTheDocument();
  });

  it('削除ボタンクリックでフィルタを削除する', async () => {
    const user = userEvent.setup();
    const onFiltersChange = vi.fn();

    render(
      <FilterConfigPanel
        filters={sampleFilters}
        onFiltersChange={onFiltersChange}
        datasetIds={[]}
      />
    );

    const deleteButtons = screen.getAllByLabelText(/を削除/);
    await user.click(deleteButtons[0]);

    expect(onFiltersChange).toHaveBeenCalledWith([sampleFilters[1]]);
  });

  it('data-testid="filter-config-panel"がある', () => {
    render(
      <FilterConfigPanel filters={[]} onFiltersChange={vi.fn()} datasetIds={[]} />
    );

    expect(screen.getByTestId('filter-config-panel')).toBeInTheDocument();
  });
});
