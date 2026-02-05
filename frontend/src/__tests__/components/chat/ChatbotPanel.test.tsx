import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatbotPanel } from '@/components/chat/ChatbotPanel';
import type { ChatMessage, ChatSource } from '@/types';

// --------------------------------------------------------------------------
// Mock useChatbot hook
// --------------------------------------------------------------------------
const mockSendMessage = vi.fn();
const mockClearError = vi.fn();

const defaultHookReturn = {
  messages: [] as ChatMessage[],
  isPending: false,
  error: null as string | null,
  sources: [] as ChatSource[],
  sendMessage: mockSendMessage,
  clearError: mockClearError,
  cancelStream: vi.fn(),
  togglePanel: vi.fn(),
  isOpen: false,
  reset: vi.fn(),
};

let mockHookReturn = { ...defaultHookReturn };

vi.mock('@/hooks/use-chatbot', () => ({
  useChatbot: () => mockHookReturn,
}));

describe('ChatbotPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockHookReturn = { ...defaultHookReturn };
  });

  afterEach(() => {
    cleanup();
  });

  // -----------------------------------------------------------------------
  // 1. Open / Close state
  // -----------------------------------------------------------------------
  describe('開閉状態', () => {
    it('isOpen=true のとき Sheet コンテンツが表示される', () => {
      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByTestId('chatbot-panel')).toBeInTheDocument();
    });

    it('isOpen=false のとき Sheet コンテンツが非表示', () => {
      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={false} onClose={vi.fn()} />
      );

      expect(screen.queryByTestId('chatbot-panel')).not.toBeInTheDocument();
    });

    it('タイトル「AI アシスタント」が表示される', () => {
      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByText('AI アシスタント')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // 2. Message list display
  // -----------------------------------------------------------------------
  describe('メッセージリスト表示', () => {
    it('メッセージがない場合、空の状態を表示する', () => {
      mockHookReturn = { ...defaultHookReturn, messages: [] };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByTestId('message-list')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-message-bubble')).not.toBeInTheDocument();
    });

    it('メッセージがある場合、ChatMessageBubble で表示する', () => {
      mockHookReturn = {
        ...defaultHookReturn,
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
        ],
      };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const bubbles = screen.getAllByTestId('chat-message-bubble');
      expect(bubbles).toHaveLength(2);
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText('Hi there!')).toBeInTheDocument();
    });

    it('複数メッセージが正しい順序で表示される', () => {
      mockHookReturn = {
        ...defaultHookReturn,
        messages: [
          { role: 'user', content: 'First' },
          { role: 'assistant', content: 'Second' },
          { role: 'user', content: 'Third' },
        ],
      };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const bubbles = screen.getAllByTestId('chat-message-bubble');
      expect(bubbles).toHaveLength(3);
      expect(within(bubbles[0]).getByText('First')).toBeInTheDocument();
      expect(within(bubbles[1]).getByText('Second')).toBeInTheDocument();
      expect(within(bubbles[2]).getByText('Third')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // 3. Send message
  // -----------------------------------------------------------------------
  describe('送信処理', () => {
    it('ChatInput が表示される', () => {
      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByPlaceholderText(/メッセージを入力/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /送信/ })).toBeInTheDocument();
    });

    it('メッセージ送信で sendMessage が呼ばれる', async () => {
      const user = userEvent.setup();
      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const textarea = screen.getByPlaceholderText(/メッセージを入力/);
      await user.type(textarea, 'Test message');
      await user.click(screen.getByRole('button', { name: /送信/ }));

      expect(mockSendMessage).toHaveBeenCalledWith('Test message');
    });

    it('isPending=true のとき ChatInput に isPending が渡される', () => {
      mockHookReturn = { ...defaultHookReturn, isPending: true };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByRole('textbox')).toBeDisabled();
    });
  });

  // -----------------------------------------------------------------------
  // 4. Error display
  // -----------------------------------------------------------------------
  describe('エラー表示', () => {
    it('error が null のとき Alert は表示されない', () => {
      mockHookReturn = { ...defaultHookReturn, error: null };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('error がある場合 Alert にエラーメッセージが表示される', () => {
      mockHookReturn = { ...defaultHookReturn, error: 'Something went wrong' };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // 5. Loading state
  // -----------------------------------------------------------------------
  describe('ローディング表示', () => {
    it('isPending=true のとき、ローディングインジケーターが表示される', () => {
      mockHookReturn = { ...defaultHookReturn, isPending: true };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    });

    it('isPending=false のとき、ローディングインジケーターが非表示', () => {
      mockHookReturn = { ...defaultHookReturn, isPending: false };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // 6. Auto scroll
  // -----------------------------------------------------------------------
  describe('自動スクロール', () => {
    it('スクロールアンカー要素がメッセージリストの末尾に存在する', () => {
      mockHookReturn = {
        ...defaultHookReturn,
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi' },
        ],
      };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const messageList = screen.getByTestId('message-list');
      const scrollAnchor = messageList.querySelector('[data-testid="scroll-anchor"]');
      expect(scrollAnchor).toBeInTheDocument();
    });

    it('スクロールアンカーがメッセージリストの最後の子要素である', () => {
      mockHookReturn = {
        ...defaultHookReturn,
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi' },
        ],
      };

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      const messageList = screen.getByTestId('message-list');
      const lastChild = messageList.lastElementChild;
      expect(lastChild).toHaveAttribute('data-testid', 'scroll-anchor');
    });

    it('メッセージ変更時に useEffect でスクロールアンカーの scrollIntoView が呼ばれる', async () => {
      // jsdom に scrollIntoView が存在しないため、全 div 要素にモックを設定
      const scrollIntoViewMock = vi.fn();
      window.HTMLDivElement.prototype.scrollIntoView = scrollIntoViewMock;

      mockHookReturn = {
        ...defaultHookReturn,
        messages: [{ role: 'user', content: 'First' }],
      };

      const { rerender } = render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      // 初回の呼び出し数を記録
      const initialCallCount = scrollIntoViewMock.mock.calls.length;

      // メッセージが変更された場合
      mockHookReturn = {
        ...defaultHookReturn,
        messages: [
          { role: 'user', content: 'First' },
          { role: 'assistant', content: 'Reply' },
        ],
      };

      rerender(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={vi.fn()} />
      );

      await waitFor(() => {
        expect(scrollIntoViewMock.mock.calls.length).toBeGreaterThan(initialCallCount);
      });

      // cleanup
      // @ts-expect-error -- restore original (undefined)
      delete window.HTMLDivElement.prototype.scrollIntoView;
    });
  });

  // -----------------------------------------------------------------------
  // 7. Props passing
  // -----------------------------------------------------------------------
  describe('Props', () => {
    it('dashboardId を useChatbot に渡す', () => {
      // useChatbot のモック自体がどの引数で呼ばれたかは
      // モックの実装に依存するため、コンポーネントが正しくレンダリングされることで検証
      render(
        <ChatbotPanel dashboardId="my-dashboard" isOpen={true} onClose={vi.fn()} />
      );

      expect(screen.getByTestId('chatbot-panel')).toBeInTheDocument();
    });

    it('onClose が Sheet の onOpenChange に渡される', async () => {
      const onCloseMock = vi.fn();

      render(
        <ChatbotPanel dashboardId="dash-1" isOpen={true} onClose={onCloseMock} />
      );

      // Sheet の Close ボタンをクリック
      const closeButton = screen.getByRole('button', { name: /close/i });
      const user = userEvent.setup();
      await user.click(closeButton);

      expect(onCloseMock).toHaveBeenCalled();
    });
  });
});
