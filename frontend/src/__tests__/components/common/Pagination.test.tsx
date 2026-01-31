import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Pagination } from '@/components/common/Pagination';

describe('Pagination', () => {
  afterEach(() => {
    cleanup();
  });
  it('総ページ数が1以下の場合は何も表示しない', () => {
    const { container } = render(
      <Pagination total={5} limit={10} offset={0} onPageChange={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('件数表示テキストを表示する', () => {
    render(<Pagination total={100} limit={10} offset={0} onPageChange={vi.fn()} />);
    expect(screen.getByText('100件中 1-10件を表示')).toBeInTheDocument();
  });

  it('現在ページ/総ページ数を表示する', () => {
    render(<Pagination total={100} limit={10} offset={20} onPageChange={vi.fn()} />);
    expect(screen.getByText('3 / 10')).toBeInTheDocument();
  });

  it('最初のページで「前へ」が無効化される', () => {
    render(<Pagination total={100} limit={10} offset={0} onPageChange={vi.fn()} />);
    const prevButton = screen.getByRole('button', { name: /前へ/ });
    expect(prevButton).toBeDisabled();
  });

  it('最後のページで「次へ」が無効化される', () => {
    render(<Pagination total={100} limit={10} offset={90} onPageChange={vi.fn()} />);
    const nextButton = screen.getByRole('button', { name: /次へ/ });
    expect(nextButton).toBeDisabled();
  });

  it('「前へ」クリックでonPageChangeが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();
    render(<Pagination total={100} limit={10} offset={20} onPageChange={mockOnPageChange} />);

    const prevButton = screen.getByRole('button', { name: /前へ/ });
    await user.click(prevButton);

    expect(mockOnPageChange).toHaveBeenCalledWith(10);
  });

  it('「次へ」クリックでonPageChangeが呼ばれる', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();
    render(<Pagination total={100} limit={10} offset={20} onPageChange={mockOnPageChange} />);

    const nextButton = screen.getByRole('button', { name: /次へ/ });
    await user.click(nextButton);

    expect(mockOnPageChange).toHaveBeenCalledWith(30);
  });
});
