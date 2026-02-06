import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDashboardFilters } from '@/hooks/use-dashboard-filters';

describe('useDashboardFilters', () => {
  beforeEach(() => {
    // No cleanup needed for this simple hook
  });

  it('初期状態では空のフィルターとviewIdが設定される', () => {
    const { result } = renderHook(() => useDashboardFilters());

    expect(result.current.filterValues).toEqual({});
    expect(result.current.selectedViewId).toBeUndefined();
  });

  it('handleFilterChangeでフィルター値を更新する', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.handleFilterChange('filter1', 'value1');
    });

    expect(result.current.filterValues).toEqual({ filter1: 'value1' });

    act(() => {
      result.current.handleFilterChange('filter2', 'value2');
    });

    expect(result.current.filterValues).toEqual({
      filter1: 'value1',
      filter2: 'value2',
    });
  });

  it('handleFilterChangeで同じフィルターを上書きする', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.handleFilterChange('filter1', 'value1');
    });

    expect(result.current.filterValues).toEqual({ filter1: 'value1' });

    act(() => {
      result.current.handleFilterChange('filter1', 'value2');
    });

    expect(result.current.filterValues).toEqual({ filter1: 'value2' });
  });

  it('handleClearAllで全フィルターとviewIdをクリアする', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.handleFilterChange('filter1', 'value1');
      result.current.handleFilterChange('filter2', 'value2');
      result.current.setSelectedView('view-001');
    });

    expect(result.current.filterValues).toEqual({
      filter1: 'value1',
      filter2: 'value2',
    });
    expect(result.current.selectedViewId).toBe('view-001');

    act(() => {
      result.current.handleClearAll();
    });

    expect(result.current.filterValues).toEqual({});
    expect(result.current.selectedViewId).toBeUndefined();
  });

  it('setFiltersで複数フィルターを一括設定する', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.setFilters({
        filter1: 'value1',
        filter2: 'value2',
        filter3: 'value3',
      });
    });

    expect(result.current.filterValues).toEqual({
      filter1: 'value1',
      filter2: 'value2',
      filter3: 'value3',
    });
  });

  it('setFiltersで既存フィルターを置き換える', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.setFilters({ filter1: 'value1', filter2: 'value2' });
    });

    expect(result.current.filterValues).toEqual({
      filter1: 'value1',
      filter2: 'value2',
    });

    act(() => {
      result.current.setFilters({ filter3: 'value3' });
    });

    expect(result.current.filterValues).toEqual({ filter3: 'value3' });
  });

  it('setSelectedViewでviewIdを設定する', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.setSelectedView('view-001');
    });

    expect(result.current.selectedViewId).toBe('view-001');

    act(() => {
      result.current.setSelectedView('view-002');
    });

    expect(result.current.selectedViewId).toBe('view-002');
  });

  it('setSelectedViewでundefinedを設定してクリアする', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.setSelectedView('view-001');
    });

    expect(result.current.selectedViewId).toBe('view-001');

    act(() => {
      result.current.setSelectedView(undefined);
    });

    expect(result.current.selectedViewId).toBeUndefined();
  });

  it('複雑なフィルター値を扱う', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.handleFilterChange('dateRange', { start: '2026-01-01', end: '2026-01-31' });
      result.current.handleFilterChange('tags', ['tag1', 'tag2']);
      result.current.handleFilterChange('isActive', true);
    });

    expect(result.current.filterValues).toEqual({
      dateRange: { start: '2026-01-01', end: '2026-01-31' },
      tags: ['tag1', 'tag2'],
      isActive: true,
    });
  });
});
