import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DateRangeFilter } from '@/components/dashboard/filters/DateRangeFilter';
import type { FilterDefinition } from '@/types';

describe('DateRangeFilter', () => {
  afterEach(() => {
    cleanup();
  });

  const baseFilter: FilterDefinition = {
    id: 'filter-date',
    type: 'date_range',
    column: 'created_at',
    label: '作成日',
  };

  it('値がない場合はラベルを表示する', () => {
    render(
      <DateRangeFilter filter={baseFilter} value={undefined} onChange={vi.fn()} />
    );

    expect(screen.getByText('作成日')).toBeInTheDocument();
  });

  it('値がある場合は日付範囲を表示する', () => {
    render(
      <DateRangeFilter
        filter={baseFilter}
        value={{ start: '2026-01-01', end: '2026-01-31' }}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByText('2026/01/01 - 2026/01/31')).toBeInTheDocument();
  });

  it('値がない場合はクリアボタンを表示しない', () => {
    render(
      <DateRangeFilter filter={baseFilter} value={undefined} onChange={vi.fn()} />
    );

    expect(screen.queryByLabelText('作成日をクリア')).not.toBeInTheDocument();
  });

  it('値がある場合はクリアボタンを表示する', () => {
    render(
      <DateRangeFilter
        filter={baseFilter}
        value={{ start: '2026-01-01', end: '2026-01-31' }}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByLabelText('作成日をクリア')).toBeInTheDocument();
  });

  it('クリアボタンクリックでundefinedを渡す', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <DateRangeFilter
        filter={baseFilter}
        value={{ start: '2026-01-01', end: '2026-01-31' }}
        onChange={onChange}
      />
    );

    await user.click(screen.getByLabelText('作成日をクリア'));
    expect(onChange).toHaveBeenCalledWith(undefined);
  });

  it('カレンダーアイコンが表示される', () => {
    render(
      <DateRangeFilter filter={baseFilter} value={undefined} onChange={vi.fn()} />
    );

    expect(screen.getByLabelText('作成日')).toBeInTheDocument();
  });
});
