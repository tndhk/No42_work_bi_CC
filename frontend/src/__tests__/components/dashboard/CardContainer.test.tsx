import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { CardContainer } from '@/components/dashboard/CardContainer';

describe('CardContainer', () => {
  afterEach(() => {
    cleanup();
  });

  it('iframeをレンダリングする', () => {
    render(<CardContainer cardId="test-card" html="<div>Test</div>" />);

    const iframe = screen.getByTitle('card-test-card');
    expect(iframe).toBeInTheDocument();
    expect(iframe.tagName).toBe('IFRAME');
  });

  it('タイトル属性にcardIdを含む', () => {
    render(<CardContainer cardId="my-card-123" html="<div>Test</div>" />);

    const iframe = screen.getByTitle('card-my-card-123');
    expect(iframe).toBeInTheDocument();
  });

  it('sandbox="allow-scripts"が設定されている', () => {
    render(<CardContainer cardId="test-card" html="<div>Test</div>" />);

    const iframe = screen.getByTitle('card-test-card');
    expect(iframe).toHaveAttribute('sandbox', 'allow-scripts');
  });

  it('srcDocにHTMLコンテンツが含まれる', () => {
    const htmlContent = '<div>My Content</div>';
    render(<CardContainer cardId="test-card" html={htmlContent} />);

    const iframe = screen.getByTitle('card-test-card') as HTMLIFrameElement;
    expect(iframe.getAttribute('srcdoc')).toContain(htmlContent);
  });

  it('CSPメタタグが含まれる', () => {
    render(<CardContainer cardId="test-card" html="<div>Test</div>" />);

    const iframe = screen.getByTitle('card-test-card') as HTMLIFrameElement;
    const srcDoc = iframe.getAttribute('srcdoc');
    expect(srcDoc).toContain('Content-Security-Policy');
    expect(srcDoc).toContain("default-src 'none'");
  });

  it('filterAppliedがfalseの場合はBadgeを表示しない', () => {
    render(<CardContainer cardId="test-card" html="<div>Test</div>" filterApplied={false} />);

    expect(screen.queryByText('filtered')).not.toBeInTheDocument();
  });

  it('filterAppliedがtrueの場合はBadgeを表示する', () => {
    render(<CardContainer cardId="test-card" html="<div>Test</div>" filterApplied={true} />);

    expect(screen.getByText('filtered')).toBeInTheDocument();
  });
});
