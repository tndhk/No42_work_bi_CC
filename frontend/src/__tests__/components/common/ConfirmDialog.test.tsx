import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

describe('ConfirmDialog', () => {
  afterEach(() => {
    cleanup();
  });
  it('open=trueでダイアログが表示される', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="テストタイトル"
        description="テスト説明"
        onConfirm={vi.fn()}
      />
    );

    expect(screen.getByText('テストタイトル')).toBeInTheDocument();
  });

  it('タイトルと説明が表示される', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="削除確認"
        description="本当に削除しますか？"
        onConfirm={vi.fn()}
      />
    );

    expect(screen.getByText('削除確認')).toBeInTheDocument();
    expect(screen.getByText('本当に削除しますか？')).toBeInTheDocument();
  });

  it('確認ボタンにカスタムラベルを表示する', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="テスト"
        description="テスト"
        confirmLabel="削除する"
        onConfirm={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: '削除する' })).toBeInTheDocument();
  });

  it('キャンセルボタンにカスタムラベルを表示する', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="テスト"
        description="テスト"
        cancelLabel="戻る"
        onConfirm={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: '戻る' })).toBeInTheDocument();
  });

  it('確認クリックでonConfirmが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnConfirm = vi.fn();

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="テスト"
        description="テスト"
        onConfirm={mockOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: '確認' });
    await user.click(confirmButton);

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
  });

  it('キャンセルクリックでonOpenChangeが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnOpenChange = vi.fn();

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="テスト"
        description="テスト"
        onConfirm={vi.fn()}
      />
    );

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' });
    await user.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('destructiveバリアントでスタイルが変わる', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={vi.fn()}
        title="テスト"
        description="テスト"
        variant="destructive"
        onConfirm={vi.fn()}
      />
    );

    const confirmButton = screen.getByRole('button', { name: '確認' });
    expect(confirmButton).toHaveClass('bg-destructive');
  });
});
