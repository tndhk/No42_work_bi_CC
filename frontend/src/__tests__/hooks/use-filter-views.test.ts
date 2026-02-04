import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { FilterView, FilterViewCreateRequest, FilterViewUpdateRequest } from '@/types';

// Mock filterViewsApi
vi.mock('@/lib/api', () => ({
  filterViewsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

import { filterViewsApi } from '@/lib/api';
const mockList = filterViewsApi.list as ReturnType<typeof vi.fn>;
const mockCreate = filterViewsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = filterViewsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = filterViewsApi.delete as ReturnType<typeof vi.fn>;

import {
  useFilterViews,
  useCreateFilterView,
  useUpdateFilterView,
  useDeleteFilterView,
  getDefaultFilterView,
} from '@/hooks/use-filter-views';

function createMockFilterView(overrides?: Partial<FilterView>): FilterView {
  return {
    id: 'fv-1',
    dashboard_id: 'dash-1',
    name: 'Test Filter View',
    owner_id: 'owner-1',
    filter_state: { category: 'sales' },
    is_shared: false,
    is_default: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useFilterViews', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ダッシュボードIDでフィルタビュー一覧を取得する', async () => {
    const mockViews = [
      createMockFilterView(),
      createMockFilterView({ id: 'fv-2', name: 'View 2' }),
    ];
    mockList.mockResolvedValue(mockViews);

    const { result } = renderHook(() => useFilterViews('dash-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith('dash-1');
    expect(result.current.data).toEqual(mockViews);
  });

  it('dashboardIdが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useFilterViews(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockList).not.toHaveBeenCalled();
  });
});

describe('useCreateFilterView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('filterViewsApi.createを呼び出してフィルタビューを作成する', async () => {
    const mockView = createMockFilterView({ id: 'fv-new', name: 'New View' });
    mockCreate.mockResolvedValue(mockView);

    const { result } = renderHook(() => useCreateFilterView(), {
      wrapper: createWrapper(),
    });

    const createData: FilterViewCreateRequest = {
      name: 'New View',
      filter_state: { category: 'sales' },
    };

    result.current.mutate({
      dashboardId: 'dash-1',
      data: createData,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockCreate).toHaveBeenCalledWith('dash-1', createData);
    expect(result.current.data).toEqual(mockView);
  });

  it('エラー時にisErrorがtrueになる', async () => {
    mockCreate.mockRejectedValue(new Error('Failed to create filter view'));

    const { result } = renderHook(() => useCreateFilterView(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      dashboardId: 'dash-1',
      data: { name: 'Fail View', filter_state: {} },
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Failed to create filter view');
  });
});

describe('useUpdateFilterView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('filterViewsApi.updateを呼び出してフィルタビューを更新する', async () => {
    const updateData: FilterViewUpdateRequest = { name: 'Updated View' };
    const mockView = createMockFilterView({ name: 'Updated View' });
    mockUpdate.mockResolvedValue(mockView);

    const { result } = renderHook(() => useUpdateFilterView(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      filterViewId: 'fv-1',
      data: updateData,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockUpdate).toHaveBeenCalledWith('fv-1', updateData);
    expect(result.current.data).toEqual(mockView);
  });

  it('エラー時にisErrorがtrueになる', async () => {
    mockUpdate.mockRejectedValue(new Error('Filter view not found'));

    const { result } = renderHook(() => useUpdateFilterView(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      filterViewId: 'fv-nonexistent',
      data: { name: 'Updated' },
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Filter view not found');
  });
});

describe('useDeleteFilterView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('filterViewsApi.deleteを呼び出してフィルタビューを削除する', async () => {
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteFilterView(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('fv-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockDelete).toHaveBeenCalledWith('fv-1');
  });

  it('エラー時にisErrorがtrueになる', async () => {
    mockDelete.mockRejectedValue(new Error('Permission denied'));

    const { result } = renderHook(() => useDeleteFilterView(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('fv-1');

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Permission denied');
  });
});

describe('getDefaultFilterView', () => {
  it('空の配列の場合はundefinedを返す', () => {
    const result = getDefaultFilterView([], 'user-1');
    expect(result).toBeUndefined();
  });

  it('currentUserIdがundefinedでもデフォルトビューを処理できる', () => {
    const views = [
      createMockFilterView({ id: 'fv-1', is_default: false }),
      createMockFilterView({ id: 'fv-2', is_default: true, is_shared: true }),
    ];
    const result = getDefaultFilterView(views, undefined);
    expect(result?.id).toBe('fv-2');
  });

  it('自分がownerのデフォルトビューを優先して返す', () => {
    const currentUserId = 'current-user';
    const views = [
      createMockFilterView({
        id: 'fv-shared-default',
        owner_id: 'other-user',
        is_default: true,
        is_shared: true,
      }),
      createMockFilterView({
        id: 'fv-own-default',
        owner_id: currentUserId,
        is_default: true,
        is_shared: false,
      }),
    ];

    const result = getDefaultFilterView(views, currentUserId);
    expect(result?.id).toBe('fv-own-default');
  });

  it('自分のデフォルトがない場合は共有デフォルトを返す', () => {
    const currentUserId = 'current-user';
    const views = [
      createMockFilterView({
        id: 'fv-normal',
        owner_id: currentUserId,
        is_default: false,
        is_shared: false,
      }),
      createMockFilterView({
        id: 'fv-shared-default',
        owner_id: 'other-user',
        is_default: true,
        is_shared: true,
      }),
    ];

    const result = getDefaultFilterView(views, currentUserId);
    expect(result?.id).toBe('fv-shared-default');
  });

  it('デフォルトビューがない場合はundefinedを返す', () => {
    const views = [
      createMockFilterView({ id: 'fv-1', is_default: false }),
      createMockFilterView({ id: 'fv-2', is_default: false }),
    ];

    const result = getDefaultFilterView(views, 'current-user');
    expect(result).toBeUndefined();
  });

  it('is_default=trueでもis_shared=falseかつownerが異なる場合は返さない', () => {
    const views = [
      createMockFilterView({
        id: 'fv-other-default',
        owner_id: 'other-user',
        is_default: true,
        is_shared: false,
      }),
    ];

    const result = getDefaultFilterView(views, 'current-user');
    expect(result).toBeUndefined();
  });
});
