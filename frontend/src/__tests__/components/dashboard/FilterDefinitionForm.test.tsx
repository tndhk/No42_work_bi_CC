import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterDefinitionForm } from '@/components/dashboard/FilterDefinitionForm';

// Mock datasetsApi
vi.mock('@/lib/api', () => ({
  datasetsApi: {
    getColumnValues: vi.fn(() => Promise.resolve(['Value1', 'Value2', 'Value3'])),
  },
}));

describe('FilterDefinitionForm', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('ラベル入力フィールドがある', () => {
    render(
      <FilterDefinitionForm datasetIds={[]} onSubmit={vi.fn()} onCancel={vi.fn()} />
    );

    expect(screen.getByLabelText('ラベル')).toBeInTheDocument();
  });

  it('タイプ選択フィールドがある', () => {
    render(
      <FilterDefinitionForm datasetIds={[]} onSubmit={vi.fn()} onCancel={vi.fn()} />
    );

    expect(screen.getByLabelText('タイプ')).toBeInTheDocument();
  });

  it('カラム名入力フィールドがある', () => {
    render(
      <FilterDefinitionForm datasetIds={[]} onSubmit={vi.fn()} onCancel={vi.fn()} />
    );

    expect(screen.getByLabelText('カラム名')).toBeInTheDocument();
  });

  it('初期値がフォームに反映される', () => {
    render(
      <FilterDefinitionForm
        initialValue={{
          id: 'f1',
          type: 'category',
          column: 'region',
          label: '地域',
        }}
        datasetIds={[]}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue('地域')).toBeInTheDocument();
    expect(screen.getByDisplayValue('region')).toBeInTheDocument();
  });

  it('空のラベルでSubmitするとエラーを表示する', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <FilterDefinitionForm datasetIds={[]} onSubmit={onSubmit} onCancel={vi.fn()} />
    );

    await user.click(screen.getByRole('button', { name: '追加' }));

    expect(screen.getByText('ラベルを入力してください')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('キャンセルボタンでonCancelが呼ばれる', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(
      <FilterDefinitionForm datasetIds={[]} onSubmit={vi.fn()} onCancel={onCancel} />
    );

    await user.click(screen.getByRole('button', { name: 'キャンセル' }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
