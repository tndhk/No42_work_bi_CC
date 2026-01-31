import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useDashboards,
  useDashboard,
  useCreateDashboard,
  useUpdateDashboard,
  useDeleteDashboard,
  useCloneDashboard,
} from '@/hooks/use-dashboards';
import { createWrapper, createMockDashboard, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';
import type {
  DashboardDetail,
  DashboardCreateRequest,
  DashboardUpdateRequest,
} from '@/types';

// Mock dashboardsApi
vi.mock('@/lib/api', () => ({
  dashboardsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    clone: vi.fn(),
  },
}));

import { dashboardsApi } from '@/lib/api';
const mockList = dashboardsApi.list as ReturnType<typeof vi.fn>;
const mockGet = dashboardsApi.get as ReturnType<typeof vi.fn>;
const mockCreate = dashboardsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = dashboardsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = dashboardsApi.delete as ReturnType<typeof vi.fn>;
const mockClone = dashboardsApi.clone as ReturnType<typeof vi.fn>;

describe('useDashboards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ダッシュボード一覧を取得する', async () => {
    const mockDashboards = [createMockDashboard(), createMockDashboard({ dashboard_id: 'dashboard-2' })];
    const mockResponse = createMockPaginatedResponse(mockDashboards);

    mockList.mockResolvedValue(mockResponse.data);

    const { result } = renderHook(() => useDashboards(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(undefined);
    expect(result.current.data).toEqual(mockResponse.data);
  });
});

describe('useDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ダッシュボード詳細を取得する', async () => {
    const mockDashboard: DashboardDetail = {
      ...createMockDashboard(),
      cards: [],
    };

    mockGet.mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useDashboard('dashboard-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGet).toHaveBeenCalledWith('dashboard-1');
    expect(result.current.data).toEqual(mockDashboard);
  });

  it('IDが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useDashboard(''), { wrapper: createWrapper() });

    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useCreateDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdashboardsクエリを無効化する', async () => {
    const createData: DashboardCreateRequest = {
      name: 'New Dashboard',
    };

    const mockDashboard: DashboardDetail = {
      ...createMockDashboard({ dashboard_id: 'dashboard-new', name: 'New Dashboard' }),
      cards: [],
    };

    mockCreate.mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useCreateDashboard(), { wrapper: createWrapper() });

    result.current.mutate(createData);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockCreate).toHaveBeenCalledWith(createData);
    expect(result.current.data).toEqual(mockDashboard);
  });
});

describe('useUpdateDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdashboardsと個別クエリを無効化する', async () => {
    const updateData: DashboardUpdateRequest = { name: 'Updated Dashboard' };
    const mockDashboard: DashboardDetail = {
      ...createMockDashboard({ name: 'Updated Dashboard' }),
      cards: [],
    };

    mockUpdate.mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useUpdateDashboard(), { wrapper: createWrapper() });

    result.current.mutate({ dashboardId: 'dashboard-1', data: updateData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockUpdate).toHaveBeenCalledWith('dashboard-1', updateData);
    expect(result.current.data).toEqual(mockDashboard);
  });
});

describe('useDeleteDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdashboardsクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteDashboard(), { wrapper: createWrapper() });

    result.current.mutate('dashboard-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockDelete).toHaveBeenCalledWith('dashboard-1');
  });
});

describe('useCloneDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('成功時にdashboardsクエリを無効化する', async () => {
    const mockDashboard: DashboardDetail = {
      ...createMockDashboard({ dashboard_id: 'dashboard-clone', name: 'Cloned Dashboard' }),
      cards: [],
    };

    mockClone.mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useCloneDashboard(), { wrapper: createWrapper() });

    result.current.mutate({ dashboardId: 'dashboard-1', name: 'Cloned Dashboard' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockClone).toHaveBeenCalledWith('dashboard-1', 'Cloned Dashboard');
    expect(result.current.data).toEqual(mockDashboard);
  });
});
