import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useDefaultFilterView } from '@/hooks/use-default-filter-view';
import type { FilterView } from '@/types';

// Mock getDefaultFilterView
vi.mock('@/hooks/use-filter-views', () => ({
  getDefaultFilterView: vi.fn(),
}));

import { getDefaultFilterView } from '@/hooks/use-filter-views';
const mockGetDefaultFilterView = getDefaultFilterView as ReturnType<typeof vi.fn>;

function createMockFilterView(overrides?: Partial<FilterView>): FilterView {
  return {
    id: 'view-001',
    dashboard_id: 'dashboard-001',
    name: 'Default View',
    filter_state: { filter1: 'value1' },
    is_shared: false,
    owner_id: 'user-001',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useDefaultFilterView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('デフォルトビューが存在する場合は自動適用される', () => {
    const defaultView = createMockFilterView({ name: 'My Default' });
    const filterViews = [
      defaultView,
      createMockFilterView({ id: 'view-002', name: 'Other View' }),
    ];
    const onApply = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(defaultView);

    renderHook(() =>
      useDefaultFilterView({
        filterViews,
        currentUserId: 'user-001',
        onApply,
      })
    );

    expect(mockGetDefaultFilterView).toHaveBeenCalledWith(filterViews, 'user-001');
    expect(onApply).toHaveBeenCalledWith(defaultView);
  });

  it('デフォルトビューがない場合は何もしない', () => {
    const filterViews = [
      createMockFilterView({ id: 'view-001' }),
      createMockFilterView({ id: 'view-002' }),
    ];
    const onApply = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(undefined);

    renderHook(() =>
      useDefaultFilterView({
        filterViews,
        currentUserId: 'user-001',
        onApply,
      })
    );

    expect(mockGetDefaultFilterView).toHaveBeenCalledWith(filterViews, 'user-001');
    expect(onApply).not.toHaveBeenCalled();
  });

  it('filterViewsが空の場合は何もしない', () => {
    const onApply = vi.fn();

    renderHook(() =>
      useDefaultFilterView({
        filterViews: [],
        currentUserId: 'user-001',
        onApply,
      })
    );

    expect(mockGetDefaultFilterView).not.toHaveBeenCalled();
    expect(onApply).not.toHaveBeenCalled();
  });

  it('初回のみ実行され、再レンダリング時は実行されない', () => {
    const defaultView = createMockFilterView();
    const filterViews = [defaultView];
    const onApply = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(defaultView);

    const { rerender } = renderHook(() =>
      useDefaultFilterView({
        filterViews,
        currentUserId: 'user-001',
        onApply,
      })
    );

    expect(onApply).toHaveBeenCalledTimes(1);

    rerender();

    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it('filterViewsが変わっても初回適用後は再実行されない', () => {
    const defaultView1 = createMockFilterView({ id: 'view-001' });
    const defaultView2 = createMockFilterView({ id: 'view-002' });
    const onApply = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(defaultView1);

    const { rerender } = renderHook(
      ({ filterViews }) =>
        useDefaultFilterView({
          filterViews,
          currentUserId: 'user-001',
          onApply,
        }),
      {
        initialProps: { filterViews: [defaultView1] },
      }
    );

    expect(onApply).toHaveBeenCalledTimes(1);
    expect(onApply).toHaveBeenCalledWith(defaultView1);

    mockGetDefaultFilterView.mockReturnValue(defaultView2);

    rerender({ filterViews: [defaultView2] });

    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it('currentUserIdがundefinedでも動作する', () => {
    const defaultView = createMockFilterView();
    const filterViews = [defaultView];
    const onApply = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(defaultView);

    renderHook(() =>
      useDefaultFilterView({
        filterViews,
        currentUserId: undefined,
        onApply,
      })
    );

    expect(mockGetDefaultFilterView).toHaveBeenCalledWith(filterViews, undefined);
    expect(onApply).toHaveBeenCalledWith(defaultView);
  });

  it('onApplyが変わっても再実行されない', () => {
    const defaultView = createMockFilterView();
    const filterViews = [defaultView];
    const onApply1 = vi.fn();
    const onApply2 = vi.fn();

    mockGetDefaultFilterView.mockReturnValue(defaultView);

    const { rerender } = renderHook(
      ({ onApply }) =>
        useDefaultFilterView({
          filterViews,
          currentUserId: 'user-001',
          onApply,
        }),
      {
        initialProps: { onApply: onApply1 },
      }
    );

    expect(onApply1).toHaveBeenCalledTimes(1);

    rerender({ onApply: onApply2 });

    expect(onApply1).toHaveBeenCalledTimes(1);
    expect(onApply2).not.toHaveBeenCalled();
  });
});
