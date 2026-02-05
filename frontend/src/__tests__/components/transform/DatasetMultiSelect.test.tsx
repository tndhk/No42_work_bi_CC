import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { DatasetMultiSelect } from '@/components/transform/DatasetMultiSelect';
import type { Dataset } from '@/types';

const mockDatasets: Dataset[] = [
  {
    id: 'ds-1',
    name: 'Dataset 1',
    source_type: 'csv',
    row_count: 100,
    column_count: 5,
    owner_id: 'owner-id',
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'ds-2',
    name: 'Dataset 2',
    source_type: 'csv',
    row_count: 200,
    column_count: 3,
    owner_id: 'owner-id',
    created_at: '2026-01-01T00:00:00Z',
  },
];

describe('DatasetMultiSelect', () => {
  afterEach(() => {
    cleanup();
  });

  it('データセット一覧をチェックボックスで表示する', () => {
    render(
      <DatasetMultiSelect
        datasets={mockDatasets}
        selectedIds={[]}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
    expect(screen.getByText('Dataset 2')).toBeInTheDocument();
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(2);
  });

  it('選択済みのデータセットはチェック状態になる', () => {
    render(
      <DatasetMultiSelect
        datasets={mockDatasets}
        selectedIds={['ds-1']}
        onChange={vi.fn()}
      />
    );
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).not.toBeChecked();
  });

  it('チェックボックス切替時にonChangeが呼ばれる', () => {
    const onChange = vi.fn();
    render(
      <DatasetMultiSelect
        datasets={mockDatasets}
        selectedIds={['ds-1']}
        onChange={onChange}
      />
    );
    const checkboxes = screen.getAllByRole('checkbox');
    // ds-2 をチェック
    fireEvent.click(checkboxes[1]);
    expect(onChange).toHaveBeenCalledWith(['ds-1', 'ds-2']);
  });

  it('チェック解除時にonChangeが呼ばれる', () => {
    const onChange = vi.fn();
    render(
      <DatasetMultiSelect
        datasets={mockDatasets}
        selectedIds={['ds-1', 'ds-2']}
        onChange={onChange}
      />
    );
    const checkboxes = screen.getAllByRole('checkbox');
    // ds-1 をチェック解除
    fireEvent.click(checkboxes[0]);
    expect(onChange).toHaveBeenCalledWith(['ds-2']);
  });

  it('データセットがない場合はメッセージを表示する', () => {
    render(
      <DatasetMultiSelect
        datasets={[]}
        selectedIds={[]}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByText('データセットがありません')).toBeInTheDocument();
  });
});
