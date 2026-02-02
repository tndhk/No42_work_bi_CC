import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { GroupListPage } from '@/pages/GroupListPage';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { Group } from '@/types/group';

const mockCreateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('@/hooks', () => ({
  useGroups: vi.fn(),
  useCreateGroup: vi.fn(() => ({ mutate: mockCreateMutate, isPending: false })),
  useDeleteGroup: vi.fn(() => ({ mutate: mockDeleteMutate, isPending: false })),
  useGroup: vi.fn(() => ({
    data: { id: 'group-1', name: 'Group Alpha', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', members: [] },
    isLoading: false,
  })),
  useRemoveMember: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useAddMember: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

import { useGroups } from '@/hooks';
const mockUseGroups = useGroups as ReturnType<typeof vi.fn>;

function createMockGroup(overrides?: Partial<Group>): Group {
  return {
    id: 'group-1',
    name: 'Test Group',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('GroupListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseGroups.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('グループ一覧をテーブルに表示する', () => {
    const groups = [
      createMockGroup({ id: 'group-1', name: 'Group Alpha' }),
      createMockGroup({ id: 'group-2', name: 'Group Beta' }),
    ];

    mockUseGroups.mockReturnValue({ data: groups, isLoading: false } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Group Alpha')).toBeInTheDocument();
    expect(screen.getByText('Group Beta')).toBeInTheDocument();
  });

  it('グループがない場合はメッセージを表示する', () => {
    mockUseGroups.mockReturnValue({ data: [], isLoading: false } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('グループがありません')).toBeInTheDocument();
  });

  it('新規作成ボタンでダイアログを開く', () => {
    mockUseGroups.mockReturnValue({ data: [], isLoading: false } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    const createButton = screen.getByRole('button', { name: /新規作成/ });
    fireEvent.click(createButton);

    expect(screen.getByText('新規グループ')).toBeInTheDocument();
  });

  it('削除ボタンで確認ダイアログを表示する', () => {
    const groups = [createMockGroup({ id: 'group-1', name: 'Group Alpha' })];
    mockUseGroups.mockReturnValue({ data: groups, isLoading: false } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    const deleteButtons = screen.getAllByRole('button', { name: /削除/ });
    fireEvent.click(deleteButtons[0]);

    expect(screen.getByText('グループの削除')).toBeInTheDocument();
  });

  it('グループクリックで詳細パネルを表示する', () => {
    const groups = [createMockGroup({ id: 'group-1', name: 'Group Alpha' })];
    mockUseGroups.mockReturnValue({ data: groups, isLoading: false } as any);

    render(<MemoryRouter><GroupListPage /></MemoryRouter>, { wrapper: createWrapper() });

    const detailButtons = screen.getAllByRole('button', { name: /詳細/ });
    fireEvent.click(detailButtons[0]);

    // GroupDetailPanel should be rendered with member section
    expect(screen.getByText('メンバー')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /メンバー追加/ })).toBeInTheDocument();
  });
});
