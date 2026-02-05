import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from '@/components/chat/ChatInput';

describe('ChatInput', () => {
  afterEach(() => {
    cleanup();
  });

  // --- Rendering ---

  it('テキストエリアと送信ボタンをレンダリングする', () => {
    render(<ChatInput onSend={vi.fn()} isPending={false} />);

    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /送信/ })).toBeInTheDocument();
  });

  it('プレースホルダーを表示する', () => {
    render(<ChatInput onSend={vi.fn()} isPending={false} />);

    expect(screen.getByPlaceholderText(/メッセージを入力/)).toBeInTheDocument();
  });

  // --- Send via Button ---

  it('送信ボタンクリックでonSendが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Hello, world!');
    await user.click(screen.getByRole('button', { name: /送信/ }));

    expect(mockOnSend).toHaveBeenCalledWith('Hello, world!');
  });

  it('送信後にテキストエリアがクリアされる', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Hello, world!');
    await user.click(screen.getByRole('button', { name: /送信/ }));

    expect(textarea).toHaveValue('');
  });

  it('空メッセージでは送信しない', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    await user.click(screen.getByRole('button', { name: /送信/ }));

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('空白のみのメッセージでは送信しない', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, '   ');
    await user.click(screen.getByRole('button', { name: /送信/ }));

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  // --- Send via Enter key ---

  it('Enterキーで送信する', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Enter test');
    await user.keyboard('{Enter}');

    expect(mockOnSend).toHaveBeenCalledWith('Enter test');
  });

  it('Enterキー送信後にテキストエリアがクリアされる', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Enter test');
    await user.keyboard('{Enter}');

    expect(textarea).toHaveValue('');
  });

  it('Shift+Enterで改行する（送信しない）', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={false} />);

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Line 1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    await user.type(textarea, 'Line 2');

    expect(mockOnSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue('Line 1\nLine 2');
  });

  // --- isPending state ---

  it('isPending中はテキストエリアが無効化される', () => {
    render(<ChatInput onSend={vi.fn()} isPending={true} />);

    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('isPending中は送信ボタンが無効化される', () => {
    render(<ChatInput onSend={vi.fn()} isPending={true} />);

    expect(screen.getByRole('button', { name: /送信/ })).toBeDisabled();
  });

  it('isPending中はローディング表示がある', () => {
    render(<ChatInput onSend={vi.fn()} isPending={true} />);

    expect(screen.getByText(/送信中/)).toBeInTheDocument();
  });

  it('isPending中はEnterキーで送信しない', async () => {
    const user = userEvent.setup();
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} isPending={true} />);

    const textarea = screen.getByRole('textbox');
    // disabled textarea won't accept type, so we test the handler won't fire
    await user.keyboard('{Enter}');

    expect(mockOnSend).not.toHaveBeenCalled();
  });
});
