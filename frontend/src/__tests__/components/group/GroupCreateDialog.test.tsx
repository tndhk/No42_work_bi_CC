import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { GroupCreateDialog } from '@/components/group/GroupCreateDialog';
import { createWrapper } from '@/__tests__/helpers/test-utils';

const mockCreateMutate = vi.fn();

vi.mock('@/hooks', () => ({
  useCreateGroup: vi.fn(() => ({ mutate: mockCreateMutate, isPending: false })),
}));

describe('GroupCreateDialog', () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('openがtrueの時にダイアログを表示する', () => {
    render(
      <GroupCreateDialog open={true} onOpenChange={mockOnOpenChange} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('新規グループ')).toBeInTheDocument();
  });

  it('openがfalseの時はダイアログを表示しない', () => {
    render(
      <GroupCreateDialog open={false} onOpenChange={mockOnOpenChange} />,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByText('新規グループ')).not.toBeInTheDocument();
  });

  it('名前入力して作成ボタンでmutate呼び出し', () => {
    render(
      <GroupCreateDialog open={true} onOpenChange={mockOnOpenChange} />,
      { wrapper: createWrapper() }
    );

    const input = screen.getByPlaceholderText('グループ名');
    fireEvent.change(input, { target: { value: 'New Group' } });

    const createButton = screen.getByRole('button', { name: '作成' });
    fireEvent.click(createButton);

    expect(mockCreateMutate).toHaveBeenCalledWith(
      { name: 'New Group' },
      expect.objectContaining({ onSuccess: expect.any(Function) })
    );
  });

  it('空名前では作成ボタンがdisabled', () => {
    render(
      <GroupCreateDialog open={true} onOpenChange={mockOnOpenChange} />,
      { wrapper: createWrapper() }
    );

    const createButton = screen.getByRole('button', { name: '作成' });
    expect(createButton).toBeDisabled();
  });

  it('キャンセルボタンでクローズ', () => {
    render(
      <GroupCreateDialog open={true} onOpenChange={mockOnOpenChange} />,
      { wrapper: createWrapper() }
    );

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' });
    fireEvent.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });
});
