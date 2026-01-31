import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { CardPreview } from '@/components/card/CardPreview';

// Mock dependencies
vi.mock('@/components/common/LoadingSpinner', () => ({
  LoadingSpinner: ({ size }: { size?: string }) => (
    <div data-testid="loading-spinner" data-size={size}>Loading...</div>
  ),
}));

vi.mock('@/components/dashboard/CardContainer', () => ({
  CardContainer: ({ cardId, html }: { cardId: string; html: string }) => (
    <div data-testid="card-container" data-card-id={cardId}>
      {html}
    </div>
  ),
}));

describe('CardPreview', () => {
  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    render(<CardPreview html="" isLoading={true} />);

    const spinner = screen.getByTestId('loading-spinner');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('data-size', 'lg');
  });

  it('HTMLが空の場合はプレビューメッセージを表示する', () => {
    render(<CardPreview html="" isLoading={false} />);

    expect(screen.getByText('プレビューを実行してください')).toBeInTheDocument();
    expect(screen.queryByTestId('card-container')).not.toBeInTheDocument();
  });

  it('HTMLがある場合はCardContainerを表示する', () => {
    const htmlContent = '<div>Test Content</div>';
    render(<CardPreview html={htmlContent} isLoading={false} />);

    const container = screen.getByTestId('card-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveAttribute('data-card-id', 'preview');
    expect(container).toHaveTextContent('Test Content');
  });
});
