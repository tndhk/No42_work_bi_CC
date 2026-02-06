import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useFilterViewOperations } from '@/hooks/use-filter-view-operations';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { FilterView } from '@/types';

const mockCreateFilterView = { mutateAsync: vi.fn() };
const mockUpdateFilterView = { mutateAsync: vi.fn() };
const mockDeleteFilterView = { mutateAsync: vi.fn() };

vi.mock('@/hooks/use-filter-views', () => ({
  useCreateFilterView: () => mockCreateFilterView,
  useUpdateFilterView: () => mockUpdateFilterView,
  useDeleteFilterView: () => mockDeleteFilterView,
}));

function createMockFilterView(overrides?: Partial<FilterView>): FilterView {
  return {
    id: 'view-001',
    dashboard_id: 'dashboard-001',
    name: 'Test View',
    filter_state: { filter1: 'value1' },
    is_shared: false,
    owner_id: 'user-001',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useFilterViewOperations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateFilterView.mutateAsync.mockResolvedValue(createMockFilterView());
    mockUpdateFilterView.mutateAsync.mockResolvedValue(createMockFilterView());
    mockDeleteFilterView.mutateAsync.mockResolvedValue(undefined);
  });

  it('handleSelectViewでフィルターとviewIdを設定する', () => {
    const onFiltersChange = vi.fn();
    const onSelectedViewChange = vi.fn();
    const filterView = createMockFilterView({
      filter_state: { filter1: 'value1', filter2: 'value2' },
    });

    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: {},
          onFiltersChange,
          onSelectedViewChange,
        }),
      { wrapper: createWrapper() }
    );

    result.current.handleSelectView(filterView);

    expect(onFiltersChange).toHaveBeenCalledWith({ filter1: 'value1', filter2: 'value2' });
    expect(onSelectedViewChange).toHaveBeenCalledWith('view-001');
  });

  it('handleSaveViewで新規ビューを作成する', async () => {
    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: { filter1: 'value1' },
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleSaveView('New View');

    expect(mockCreateFilterView.mutateAsync).toHaveBeenCalledWith({
      dashboardId: 'dashboard-001',
      data: {
        name: 'New View',
        filter_state: { filter1: 'value1' },
        is_shared: false,
      },
    });
  });

  it('handleSaveViewで共有ビューを作成する', async () => {
    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: { filter1: 'value1' },
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleSaveView('Shared View', { is_shared: true });

    expect(mockCreateFilterView.mutateAsync).toHaveBeenCalledWith({
      dashboardId: 'dashboard-001',
      data: {
        name: 'Shared View',
        filter_state: { filter1: 'value1' },
        is_shared: true,
      },
    });
  });

  it('handleOverwriteViewで既存ビューを上書きする', async () => {
    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: { filter1: 'new-value' },
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleOverwriteView('view-001');

    expect(mockUpdateFilterView.mutateAsync).toHaveBeenCalledWith({
      filterViewId: 'view-001',
      data: {
        filter_state: { filter1: 'new-value' },
      },
    });
  });

  it('handleDeleteViewでビューを削除する', async () => {
    const onSelectedViewChange = vi.fn();

    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: {},
          selectedViewId: 'view-002',
          onSelectedViewChange,
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleDeleteView('view-001');

    expect(mockDeleteFilterView.mutateAsync).toHaveBeenCalledWith('view-001');
    expect(onSelectedViewChange).not.toHaveBeenCalled();
  });

  it('handleDeleteViewで現在選択中のビューを削除すると選択解除される', async () => {
    const onSelectedViewChange = vi.fn();

    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: {},
          selectedViewId: 'view-001',
          onSelectedViewChange,
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleDeleteView('view-001');

    expect(mockDeleteFilterView.mutateAsync).toHaveBeenCalledWith('view-001');
    expect(onSelectedViewChange).toHaveBeenCalledWith(undefined);
  });

  it('空のフィルター値でビューを保存する', async () => {
    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: {},
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleSaveView('Empty View');

    expect(mockCreateFilterView.mutateAsync).toHaveBeenCalledWith({
      dashboardId: 'dashboard-001',
      data: {
        name: 'Empty View',
        filter_state: {},
        is_shared: false,
      },
    });
  });

  it('複雑なフィルター値でビューを保存する', async () => {
    const complexFilters = {
      dateRange: { start: '2026-01-01', end: '2026-01-31' },
      tags: ['tag1', 'tag2'],
      isActive: true,
    };

    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: complexFilters,
        }),
      { wrapper: createWrapper() }
    );

    await result.current.handleSaveView('Complex View');

    expect(mockCreateFilterView.mutateAsync).toHaveBeenCalledWith({
      dashboardId: 'dashboard-001',
      data: {
        name: 'Complex View',
        filter_state: complexFilters,
        is_shared: false,
      },
    });
  });

  it('コールバックが未指定でも動作する', () => {
    const filterView = createMockFilterView();

    const { result } = renderHook(
      () =>
        useFilterViewOperations({
          dashboardId: 'dashboard-001',
          filterValues: {},
        }),
      { wrapper: createWrapper() }
    );

    expect(() => result.current.handleSelectView(filterView)).not.toThrow();
  });
});
