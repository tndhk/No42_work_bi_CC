import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {
  useGroups,
  useGroup,
  useCreateGroup,
  useUpdateGroup,
  useDeleteGroup,
  useAddMember,
  useRemoveMember,
} from '@/hooks/use-groups';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { Group, GroupDetail, GroupMember } from '@/types/group';

vi.mock('@/lib/api', () => ({
  groupsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn(),
  },
}));

import { groupsApi } from '@/lib/api';
const mockList = groupsApi.list as ReturnType<typeof vi.fn>;
const mockGet = groupsApi.get as ReturnType<typeof vi.fn>;
const mockCreate = groupsApi.create as ReturnType<typeof vi.fn>;
const mockUpdate = groupsApi.update as ReturnType<typeof vi.fn>;
const mockDelete = groupsApi.delete as ReturnType<typeof vi.fn>;
const mockAddMember = groupsApi.addMember as ReturnType<typeof vi.fn>;
const mockRemoveMember = groupsApi.removeMember as ReturnType<typeof vi.fn>;

const mockGroup: Group = {
  id: 'group_1',
  name: 'Engineering',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockGroupDetail: GroupDetail = {
  ...mockGroup,
  members: [
    { group_id: 'group_1', user_id: 'user_1', added_at: '2026-01-01T00:00:00Z' },
  ],
};

describe('useGroups', () => {
  beforeEach(() => vi.clearAllMocks());

  it('グループ一覧を取得する', async () => {
    mockList.mockResolvedValue([mockGroup]);
    const { result } = renderHook(() => useGroups(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockList).toHaveBeenCalled();
    expect(result.current.data).toEqual([mockGroup]);
  });
});

describe('useGroup', () => {
  beforeEach(() => vi.clearAllMocks());

  it('グループ詳細を取得する', async () => {
    mockGet.mockResolvedValue(mockGroupDetail);
    const { result } = renderHook(() => useGroup('group_1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith('group_1');
    expect(result.current.data).toEqual(mockGroupDetail);
  });

  it('IDが空の場合はクエリを無効にする', async () => {
    const { result } = renderHook(() => useGroup(''), { wrapper: createWrapper() });
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useCreateGroup', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にgroupsクエリを無効化する', async () => {
    mockCreate.mockResolvedValue(mockGroup);
    const { result } = renderHook(() => useCreateGroup(), { wrapper: createWrapper() });
    result.current.mutate({ name: 'Engineering' });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockCreate).toHaveBeenCalledWith({ name: 'Engineering' });
  });
});

describe('useUpdateGroup', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にgroupsクエリを無効化する', async () => {
    mockUpdate.mockResolvedValue({ ...mockGroup, name: 'Updated' });
    const { result } = renderHook(() => useUpdateGroup(), { wrapper: createWrapper() });
    result.current.mutate({ groupId: 'group_1', data: { name: 'Updated' } });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockUpdate).toHaveBeenCalledWith('group_1', { name: 'Updated' });
  });
});

describe('useDeleteGroup', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にgroupsクエリを無効化する', async () => {
    mockDelete.mockResolvedValue(undefined);
    const { result } = renderHook(() => useDeleteGroup(), { wrapper: createWrapper() });
    result.current.mutate('group_1');
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockDelete).toHaveBeenCalledWith('group_1');
  });
});

describe('useAddMember', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にグループ詳細クエリを無効化する', async () => {
    const member: GroupMember = { group_id: 'group_1', user_id: 'user_2', added_at: '2026-01-01T00:00:00Z' };
    mockAddMember.mockResolvedValue(member);
    const { result } = renderHook(() => useAddMember(), { wrapper: createWrapper() });
    result.current.mutate({ groupId: 'group_1', userId: 'user_2' });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockAddMember).toHaveBeenCalledWith('group_1', { user_id: 'user_2' });
  });
});

describe('useRemoveMember', () => {
  beforeEach(() => vi.clearAllMocks());

  it('成功時にグループ詳細クエリを無効化する', async () => {
    mockRemoveMember.mockResolvedValue(undefined);
    const { result } = renderHook(() => useRemoveMember(), { wrapper: createWrapper() });
    result.current.mutate({ groupId: 'group_1', userId: 'user_2' });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockRemoveMember).toHaveBeenCalledWith('group_1', 'user_2');
  });
});
