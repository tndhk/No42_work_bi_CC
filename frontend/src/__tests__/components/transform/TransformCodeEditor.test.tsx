import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { TransformCodeEditor } from '@/components/transform/TransformCodeEditor';

// Monaco Editor をモック（テスト環境では動作しないため）
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange, defaultLanguage, theme }: any) => (
    <textarea
      data-testid="transform-code-editor"
      data-language={defaultLanguage}
      data-theme={theme}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

describe('TransformCodeEditor', () => {
  afterEach(() => {
    cleanup();
  });

  it('コードを表示する', () => {
    render(<TransformCodeEditor code="print('hello')" onChange={vi.fn()} />);
    const editor = screen.getByTestId('transform-code-editor');
    expect(editor).toBeInTheDocument();
    expect(editor).toHaveValue("print('hello')");
  });

  it('コード変更時にonChangeを呼び出す', () => {
    const onChange = vi.fn();
    render(<TransformCodeEditor code="" onChange={onChange} />);
    const editor = screen.getByTestId('transform-code-editor');
    fireEvent.change(editor, { target: { value: 'new code' } });
    expect(onChange).toHaveBeenCalledWith('new code');
  });

  it('Pythonをデフォルト言語として設定する', () => {
    render(<TransformCodeEditor code="" onChange={vi.fn()} />);
    const editor = screen.getByTestId('transform-code-editor');
    expect(editor).toHaveAttribute('data-language', 'python');
  });

  it('vs-darkテーマを使用する', () => {
    render(<TransformCodeEditor code="" onChange={vi.fn()} />);
    const editor = screen.getByTestId('transform-code-editor');
    expect(editor).toHaveAttribute('data-theme', 'vs-dark');
  });
});
