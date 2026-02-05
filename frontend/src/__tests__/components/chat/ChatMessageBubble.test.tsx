import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { ChatMessageBubble } from '@/components/chat/ChatMessageBubble';
import type { ChatMessage } from '@/types';

describe('ChatMessageBubble', () => {
  afterEach(() => {
    cleanup();
  });

  // --- メッセージ内容の表示 ---

  it('userメッセージの内容を表示する', () => {
    const message: ChatMessage = { role: 'user', content: 'こんにちは' };
    render(<ChatMessageBubble message={message} />);

    expect(screen.getByText('こんにちは')).toBeInTheDocument();
  });

  it('assistantメッセージの内容を表示する', () => {
    const message: ChatMessage = { role: 'assistant', content: 'お手伝いします' };
    render(<ChatMessageBubble message={message} />);

    expect(screen.getByText('お手伝いします')).toBeInTheDocument();
  });

  // --- レイアウト (配置) ---

  it('userメッセージは右寄せで表示される', () => {
    const message: ChatMessage = { role: 'user', content: 'ユーザーの質問' };
    render(<ChatMessageBubble message={message} />);

    const wrapper = screen.getByTestId('chat-message-bubble');
    expect(wrapper.className).toMatch(/justify-end/);
  });

  it('assistantメッセージは左寄せで表示される', () => {
    const message: ChatMessage = { role: 'assistant', content: 'AIの回答' };
    render(<ChatMessageBubble message={message} />);

    const wrapper = screen.getByTestId('chat-message-bubble');
    expect(wrapper.className).toMatch(/justify-start/);
  });

  // --- 背景色 ---

  it('userメッセージはprimary背景を持つ', () => {
    const message: ChatMessage = { role: 'user', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble.className).toMatch(/bg-primary/);
  });

  it('assistantメッセージはmuted背景を持つ', () => {
    const message: ChatMessage = { role: 'assistant', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble.className).toMatch(/bg-muted/);
  });

  // --- テキスト色 ---

  it('userメッセージはprimary-foregroundテキスト色を持つ', () => {
    const message: ChatMessage = { role: 'user', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble.className).toMatch(/text-primary-foreground/);
  });

  it('assistantメッセージはforegroundテキスト色を持つ', () => {
    const message: ChatMessage = { role: 'assistant', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble.className).toMatch(/text-foreground/);
  });

  // --- アクセシビリティ ---

  it('適切なrole属性を持つ', () => {
    const message: ChatMessage = { role: 'user', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble).toHaveAttribute('role', 'log');
  });

  // --- エッジケース ---

  it('空文字のメッセージも表示できる', () => {
    const message: ChatMessage = { role: 'user', content: '' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble).toBeInTheDocument();
    expect(bubble.textContent).toBe('');
  });

  it('長いメッセージも正しく表示される', () => {
    const longContent = 'あ'.repeat(1000);
    const message: ChatMessage = { role: 'assistant', content: longContent };
    render(<ChatMessageBubble message={message} />);

    expect(screen.getByText(longContent)).toBeInTheDocument();
  });

  it('特殊文字を含むメッセージを表示できる', () => {
    const message: ChatMessage = {
      role: 'user',
      content: '<script>alert("xss")</script> & "quotes"',
    };
    render(<ChatMessageBubble message={message} />);

    expect(
      screen.getByText('<script>alert("xss")</script> & "quotes"')
    ).toBeInTheDocument();
  });

  // --- 最大幅制限 ---

  it('バブルにmax-widthが設定されている', () => {
    const message: ChatMessage = { role: 'user', content: 'テスト' };
    render(<ChatMessageBubble message={message} />);

    const bubble = screen.getByTestId('chat-bubble');
    expect(bubble.className).toMatch(/max-w-/);
  });
});
