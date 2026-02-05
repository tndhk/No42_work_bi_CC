import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatbot } from '@/hooks/use-chatbot';
import { useChatStore } from '@/stores/chat-store';
import type { ChatSource } from '@/types';

// Mock sendChatMessage from the API layer
vi.mock('@/lib/api/chat', () => ({
  sendChatMessage: vi.fn(),
}));

import { sendChatMessage } from '@/lib/api/chat';
const mockSendChatMessage = sendChatMessage as Mock;

describe('useChatbot', () => {
  const dashboardId = 'dashboard-1';

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset zustand store between tests
    useChatStore.getState().reset();
  });

  // -------------------------------------------------------------------------
  // Initial state
  // -------------------------------------------------------------------------
  it('returns initial state correctly', () => {
    const { result } = renderHook(() => useChatbot(dashboardId));

    expect(result.current.messages).toEqual([]);
    expect(result.current.isOpen).toBe(false);
    expect(result.current.isPending).toBe(false);
    expect(result.current.sources).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.sendMessage).toBe('function');
    expect(typeof result.current.cancelStream).toBe('function');
    expect(typeof result.current.togglePanel).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  // -------------------------------------------------------------------------
  // sendMessage basic flow
  // -------------------------------------------------------------------------
  describe('sendMessage', () => {
    it('adds user message and empty assistant message, then calls sendChatMessage', async () => {
      // sendChatMessage resolves immediately (simulating instant done)
      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          callbacks.onDone([]);
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      // Should have 2 messages: user + assistant
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0]).toEqual({
        role: 'user',
        content: 'Hello',
      });
      expect(result.current.messages[1]).toEqual({
        role: 'assistant',
        content: '',
      });

      // sendChatMessage should have been called with correct args
      expect(mockSendChatMessage).toHaveBeenCalledTimes(1);
      expect(mockSendChatMessage).toHaveBeenCalledWith(
        dashboardId,
        {
          message: 'Hello',
          conversation_history: [],
        },
        expect.objectContaining({
          onToken: expect.any(Function),
          onDone: expect.any(Function),
          onError: expect.any(Function),
        }),
        expect.any(AbortSignal),
      );
    });

    it('sets isPending true during streaming and false when done', async () => {
      let capturedOnDone: ((sources: ChatSource[]) => void) | null = null;

      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          capturedOnDone = callbacks.onDone;
          // Do NOT call onDone yet - simulate ongoing stream
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      // Start sending (don't await - it won't resolve until onDone)
      let sendPromise: Promise<void>;
      act(() => {
        sendPromise = result.current.sendMessage('Hello');
      });

      // isPending should be true while streaming
      expect(result.current.isPending).toBe(true);

      // Now simulate stream completion
      await act(async () => {
        capturedOnDone!([]);
        await sendPromise!;
      });

      // isPending should be false after completion
      expect(result.current.isPending).toBe(false);
    });

    it('does not send empty messages', async () => {
      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('');
      });

      expect(result.current.messages).toHaveLength(0);
      expect(mockSendChatMessage).not.toHaveBeenCalled();
    });

    it('does not send whitespace-only messages', async () => {
      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('   ');
      });

      expect(result.current.messages).toHaveLength(0);
      expect(mockSendChatMessage).not.toHaveBeenCalled();
    });

    it('does not send a new message while isPending', async () => {
      mockSendChatMessage.mockImplementation(async () => {
        // Never resolves callbacks - stays pending
      });

      const { result } = renderHook(() => useChatbot(dashboardId));

      act(() => {
        result.current.sendMessage('First');
      });

      expect(result.current.isPending).toBe(true);

      await act(async () => {
        await result.current.sendMessage('Second');
      });

      // Only one sendChatMessage call (the first)
      expect(mockSendChatMessage).toHaveBeenCalledTimes(1);
    });

    it('passes conversation_history excluding the current user message and empty assistant', async () => {
      // Pre-populate store with history
      useChatStore.getState().addMessage({ role: 'user', content: 'Previous Q' });
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Previous A' });

      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          callbacks.onDone([]);
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('New question');
      });

      // conversation_history should contain the previous messages (before adding new ones)
      expect(mockSendChatMessage).toHaveBeenCalledWith(
        dashboardId,
        {
          message: 'New question',
          conversation_history: [
            { role: 'user', content: 'Previous Q' },
            { role: 'assistant', content: 'Previous A' },
          ],
        },
        expect.any(Object),
        expect.any(AbortSignal),
      );
    });
  });

  // -------------------------------------------------------------------------
  // Streaming tokens
  // -------------------------------------------------------------------------
  describe('streaming tokens', () => {
    it('appends tokens to the last assistant message via onToken', async () => {
      let capturedOnToken: ((token: string) => void) | null = null;
      let capturedOnDone: ((sources: ChatSource[]) => void) | null = null;

      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: {
            onToken: (token: string) => void;
            onDone: (sources: ChatSource[]) => void;
          },
        ) => {
          capturedOnToken = callbacks.onToken;
          capturedOnDone = callbacks.onDone;
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      let sendPromise: Promise<void>;
      act(() => {
        sendPromise = result.current.sendMessage('Hello');
      });

      // Simulate streaming tokens
      act(() => {
        capturedOnToken!('Hello');
      });

      expect(result.current.messages[1].content).toBe('Hello');

      act(() => {
        capturedOnToken!(' world');
      });

      expect(result.current.messages[1].content).toBe('Hello world');

      // Finish stream
      await act(async () => {
        capturedOnDone!([]);
        await sendPromise!;
      });

      expect(result.current.messages[1].content).toBe('Hello world');
    });

    it('sets sources when onDone is called', async () => {
      const mockSources: ChatSource[] = [
        { dataset_name: 'Sales Data', relevance: 'high' },
        { dataset_name: 'Users', relevance: 'medium' },
      ];

      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          callbacks.onDone(mockSources);
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('What is the sales trend?');
      });

      expect(result.current.sources).toEqual(mockSources);
    });
  });

  // -------------------------------------------------------------------------
  // Error handling
  // -------------------------------------------------------------------------
  describe('error handling', () => {
    it('sets error and stops pending when onError is called', async () => {
      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onError: (error: string) => void },
        ) => {
          callbacks.onError('Server error');
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      expect(result.current.error).toBe('Server error');
      expect(result.current.isPending).toBe(false);
    });

    it('clears previous error when sending a new message', async () => {
      // First call: error
      mockSendChatMessage.mockImplementationOnce(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onError: (error: string) => void },
        ) => {
          callbacks.onError('First error');
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      expect(result.current.error).toBe('First error');

      // Second call: success
      mockSendChatMessage.mockImplementationOnce(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          callbacks.onDone([]);
        },
      );

      await act(async () => {
        await result.current.sendMessage('Hello again');
      });

      // Error should be cleared (addMessage resets error in the store)
      expect(result.current.error).toBeNull();
    });
  });

  // -------------------------------------------------------------------------
  // cancelStream
  // -------------------------------------------------------------------------
  describe('cancelStream', () => {
    it('aborts the current stream and resets isPending', async () => {
      let capturedSignal: AbortSignal | null = null;

      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          _callbacks: unknown,
          signal?: AbortSignal,
        ) => {
          capturedSignal = signal ?? null;
          // Keep the promise pending indefinitely by returning a new promise
          return new Promise<void>((resolve) => {
            signal?.addEventListener('abort', () => resolve());
          });
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      let sendPromise: Promise<void>;
      act(() => {
        sendPromise = result.current.sendMessage('Hello');
      });

      expect(result.current.isPending).toBe(true);
      expect(capturedSignal).not.toBeNull();
      expect(capturedSignal!.aborted).toBe(false);

      // Cancel the stream
      await act(async () => {
        result.current.cancelStream();
        await sendPromise!;
      });

      expect(capturedSignal!.aborted).toBe(true);
      expect(result.current.isPending).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // togglePanel
  // -------------------------------------------------------------------------
  describe('togglePanel', () => {
    it('toggles isOpen from false to true and back', () => {
      const { result } = renderHook(() => useChatbot(dashboardId));

      expect(result.current.isOpen).toBe(false);

      act(() => {
        result.current.togglePanel();
      });

      expect(result.current.isOpen).toBe(true);

      act(() => {
        result.current.togglePanel();
      });

      expect(result.current.isOpen).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // reset
  // -------------------------------------------------------------------------
  describe('reset', () => {
    it('resets all state to initial values', async () => {
      mockSendChatMessage.mockImplementation(
        async (
          _dashboardId: string,
          _request: unknown,
          callbacks: { onDone: (sources: ChatSource[]) => void },
        ) => {
          callbacks.onDone([{ dataset_name: 'Test', relevance: 'high' }]);
        },
      );

      const { result } = renderHook(() => useChatbot(dashboardId));

      // Add some state
      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      act(() => {
        result.current.togglePanel();
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.isOpen).toBe(true);
      expect(result.current.sources).toHaveLength(1);

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.messages).toEqual([]);
      expect(result.current.isOpen).toBe(false);
      expect(result.current.isPending).toBe(false);
      expect(result.current.sources).toEqual([]);
      expect(result.current.error).toBeNull();
    });
  });
});
