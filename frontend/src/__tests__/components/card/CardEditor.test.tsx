import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CardEditor } from '@/components/card/CardEditor';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

describe('CardEditor', () => {
  afterEach(() => {
    cleanup();
  });

  it('Monacoエディタをレンダリングする', () => {
    render(<CardEditor code="" onChange={vi.fn()} />);

    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toBeInTheDocument();
  });

  it('codeの値を表示する', () => {
    const code = 'print("Hello, World!")';
    render(<CardEditor code={code} onChange={vi.fn()} />);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    expect(editor.value).toBe(code);
  });

  it('変更時にonChangeを呼ぶ', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();
    render(<CardEditor code="" onChange={mockOnChange} />);

    const editor = screen.getByTestId('monaco-editor');
    await user.type(editor, 'test');

    expect(mockOnChange).toHaveBeenCalled();
  });

  it('空の値でonChangeに空文字列を渡す', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();
    render(<CardEditor code="initial" onChange={mockOnChange} />);

    const editor = screen.getByTestId('monaco-editor');
    await user.clear(editor);

    expect(mockOnChange).toHaveBeenCalledWith('');
  });
});
