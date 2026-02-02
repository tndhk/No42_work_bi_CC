import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { MemberAddDialog } from '@/components/group/MemberAddDialog';
import { createWrapper } from '@/__tests__/helpers/test-utils';

const mockAddMutate = vi.fn();

vi.mock('@/hooks', () => ({
  useAddMember: vi.fn(() => ({ mutate: mockAddMutate, isPending: false })),
}));

describe('MemberAddDialog', () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('openがtrueの時にダイアログを表示する', () => {
    render(
      <MemberAddDialog open={true} onOpenChange={mockOnOpenChange} groupId="group-1" />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('メンバー追加')).toBeInTheDocument();
  });

  it('openがfalseの時はダイアログを表示しない', () => {
    render(
      <MemberAddDialog open={false} onOpenChange={mockOnOpenChange} groupId="group-1" />,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByText('メンバー追加')).not.toBeInTheDocument();
  });

  it('ユーザーID入力がある', () => {
    render(
      <MemberAddDialog open={true} onOpenChange={mockOnOpenChange} groupId="group-1" />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByPlaceholderText('ユーザーID')).toBeInTheDocument();
  });

  it('追加ボタンでmutate呼び出し', () => {
    render(
      <MemberAddDialog open={true} onOpenChange={mockOnOpenChange} groupId="group-1" />,
      { wrapper: createWrapper() }
    );

    const input = screen.getByPlaceholderText('ユーザーID');
    fireEvent.change(input, { target: { value: 'user-123' } });

    const addButton = screen.getByRole('button', { name: '追加' });
    fireEvent.click(addButton);

    expect(mockAddMutate).toHaveBeenCalledWith(
      { groupId: 'group-1', userId: 'user-123' },
      expect.objectContaining({ onSuccess: expect.any(Function) })
    );
  });

  it('空のユーザーIDでは追加ボタンがdisabled', () => {
    render(
      <MemberAddDialog open={true} onOpenChange={mockOnOpenChange} groupId="group-1" />,
      { wrapper: createWrapper() }
    );

    const addButton = screen.getByRole('button', { name: '追加' });
    expect(addButton).toBeDisabled();
  });
});
