import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useShares,
  useCreateShare,
  useUpdateShare,
  useDeleteShare,
} from '@/hooks/use-dashboard-shares';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { DashboardShare } from '@/types/dashboard';

vi.mock('@/lib/api', () => ({
  dashboardSharesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

import { dashboardSharesApi } from '@/lib/api';
const mockList = dashboardSharesApi.list as ReturnType<typeof vi.fn>;
const mockCreate = dashboardSharesApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = dashboardSharesApi.update as ReturnType<typeof vi.fn>;
const mockDelete = dashboardSharesApi.delete as ReturnType<typeof vi.fn>;

const mockShare: DashboardShare = {
  id: 'share_1',
  dashboard_id: 'dash_1',
  shared_to_type: 'user',
  shared_to_id: 'user_2',
  permission: 'viewer',
  shared_by: 'user_1',
  created_at: '2026-01-01T00:00:00Z',
};

describe('useShares', () => {
  beforeEach(() => vi.clearAllMocks());

  it('共有一覧を取得する', async () => {
    mockList.mockResolvedValue([mockShare]);
    const { result } = renderHook(() => useShares('dash_1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockList).toHaveBeenCalledWith('dash_1');
    expect(result.current.data).toEqual([mockShare]);
  });

  it('dashboardIdが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useShares(''), { wrapper: createWrapper() });
    expect(result.current.isFetching).toBe(false);
    expect(mockList).not.toHaveBeenCalled();
  });
});

describe('useCreateShare', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にsharesクエリを無効化する', async () => {
    mockCreate.mockResolvedValue(mockShare);
    const { result } = renderHook(() => useCreateShare(), { wrapper: createWrapper() });
    result.current.mutate({
      dashboardId: 'dash_1',
      data: { shared_to_type: 'user', shared_to_id: 'user_2', permission: 'viewer' },
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockCreate).toHaveBeenCalledWith('dash_1', {
      shared_to_type: 'user', shared_to_id: 'user_2', permission: 'viewer',
    });
  });
});

describe('useUpdateShare', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にsharesクエリを無効化する', async () => {
    const updatedShare = { ...mockShare, permission: 'editor' as const };
    mockUpdate.mockResolvedValue(updatedShare);
    const { result } = renderHook(() => useUpdateShare(), { wrapper: createWrapper() });
    result.current.mutate({
      dashboardId: 'dash_1',
      shareId: 'share_1',
      data: { permission: 'editor' },
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockUpdate).toHaveBeenCalledWith('dash_1', 'share_1', { permission: 'editor' });
  });
});

describe('useDeleteShare', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にsharesクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);
    const { result } = renderHook(() => useDeleteShare(), { wrapper: createWrapper() });
    result.current.mutate({ dashboardId: 'dash_1', shareId: 'share_1' });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockDelete).toHaveBeenCalledWith('dash_1', 'share_1');
  });
});
