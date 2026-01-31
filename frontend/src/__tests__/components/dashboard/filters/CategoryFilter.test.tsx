import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CategoryFilter } from '@/components/dashboard/filters/CategoryFilter';
import type { FilterDefinition } from '@/types';

describe('CategoryFilter', () => {
  afterEach(() => {
    cleanup();
  });

  const baseSingleFilter: FilterDefinition = {
    id: 'filter-1',
    type: 'category',
    column: 'region',
    label: '地域',
    multi_select: false,
    options: ['East', 'West', 'North'],
  };

  const baseMultiFilter: FilterDefinition = {
    id: 'filter-2',
    type: 'category',
    column: 'category',
    label: 'カテゴリ',
    multi_select: true,
    options: ['A', 'B', 'C'],
  };

  describe('単一選択モード', () => {
    it('ラベルをプレースホルダーとして表示する', () => {
      render(
        <CategoryFilter filter={baseSingleFilter} value={undefined} onChange={vi.fn()} />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('値がない場合はクリアボタンを表示しない', () => {
      render(
        <CategoryFilter filter={baseSingleFilter} value={undefined} onChange={vi.fn()} />
      );

      expect(screen.queryByLabelText('地域をクリア')).not.toBeInTheDocument();
    });

    it('値がある場合はクリアボタンを表示する', () => {
      render(
        <CategoryFilter filter={baseSingleFilter} value="East" onChange={vi.fn()} />
      );

      expect(screen.getByLabelText('地域をクリア')).toBeInTheDocument();
    });

    it('クリアボタンクリックでundefinedを渡す', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();

      render(
        <CategoryFilter filter={baseSingleFilter} value="East" onChange={onChange} />
      );

      await user.click(screen.getByLabelText('地域をクリア'));
      expect(onChange).toHaveBeenCalledWith(undefined);
    });

    it('aria-labelがフィルタラベルに設定される', () => {
      render(
        <CategoryFilter filter={baseSingleFilter} value={undefined} onChange={vi.fn()} />
      );

      expect(screen.getByRole('combobox')).toHaveAttribute('aria-label', '地域');
    });
  });

  describe('複数選択モード', () => {
    it('値がない場合はラベルを表示する', () => {
      render(
        <CategoryFilter filter={baseMultiFilter} value={undefined} onChange={vi.fn()} />
      );

      expect(screen.getByText('カテゴリ')).toBeInTheDocument();
    });

    it('値がある場合はクリアボタンを表示する', () => {
      render(
        <CategoryFilter filter={baseMultiFilter} value={['A']} onChange={vi.fn()} />
      );

      expect(screen.getByLabelText('カテゴリをクリア')).toBeInTheDocument();
    });

    it('1つの値が選択されている場合はその値を表示する', () => {
      render(
        <CategoryFilter filter={baseMultiFilter} value={['A']} onChange={vi.fn()} />
      );

      expect(screen.getByText('A')).toBeInTheDocument();
    });

    it('複数の値が選択されている場合は件数を表示する', () => {
      render(
        <CategoryFilter filter={baseMultiFilter} value={['A', 'B']} onChange={vi.fn()} />
      );

      expect(screen.getByText('A (+1)')).toBeInTheDocument();
    });
  });
});
