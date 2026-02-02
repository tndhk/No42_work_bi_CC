import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { GroupDetailPanel } from '@/components/group/GroupDetailPanel';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { GroupDetail } from '@/types/group';

const mockRemoveMutate = vi.fn();

vi.mock('@/hooks', () => ({
  useGroup: vi.fn(),
  useRemoveMember: vi.fn(() => ({ mutate: mockRemoveMutate, isPending: false })),
  useAddMember: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

import { useGroup } from '@/hooks';
const mockUseGroup = useGroup as ReturnType<typeof vi.fn>;

function createMockGroupDetail(overrides?: Partial<GroupDetail>): GroupDetail {
  return {
    id: 'group-1',
    name: 'Test Group',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    members: [],
    ...overrides,
  };
}

describe('GroupDetailPanel', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('グループ名を表示する', () => {
    const group = createMockGroupDetail({ name: 'My Group' });
    mockUseGroup.mockReturnValue({ data: group, isLoading: false } as any);

    render(
      <GroupDetailPanel groupId="group-1" onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('My Group')).toBeInTheDocument();
  });

  it('メンバー一覧を表示する', () => {
    const group = createMockGroupDetail({
      members: [
        { group_id: 'group-1', user_id: 'user-1', added_at: '2026-01-01T00:00:00Z' },
        { group_id: 'group-1', user_id: 'user-2', added_at: '2026-01-02T00:00:00Z' },
      ],
    });
    mockUseGroup.mockReturnValue({ data: group, isLoading: false } as any);

    render(
      <GroupDetailPanel groupId="group-1" onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('user-1')).toBeInTheDocument();
    expect(screen.getByText('user-2')).toBeInTheDocument();
  });

  it('メンバー追加ボタンを表示する', () => {
    const group = createMockGroupDetail();
    mockUseGroup.mockReturnValue({ data: group, isLoading: false } as any);

    render(
      <GroupDetailPanel groupId="group-1" onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /メンバー追加/ })).toBeInTheDocument();
  });

  it('メンバー削除ボタンを表示する', () => {
    const group = createMockGroupDetail({
      members: [
        { group_id: 'group-1', user_id: 'user-1', added_at: '2026-01-01T00:00:00Z' },
      ],
    });
    mockUseGroup.mockReturnValue({ data: group, isLoading: false } as any);

    render(
      <GroupDetailPanel groupId="group-1" onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    const removeButtons = screen.getAllByRole('button', { name: /削除/ });
    expect(removeButtons.length).toBeGreaterThanOrEqual(1);
  });
});
