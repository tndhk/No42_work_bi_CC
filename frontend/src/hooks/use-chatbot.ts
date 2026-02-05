import { useCallback, useRef } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { sendChatMessage } from '@/lib/api/chat';

/**
 * Custom hook that orchestrates the chatbot interaction for a given dashboard.
 *
 * Manages message sending with SSE streaming, cancellation via AbortController,
 * panel toggling, and state reset -- all backed by the shared useChatStore.
 */
export function useChatbot(dashboardId: string) {
  const {
    messages,
    isOpen,
    isPending,
    sources,
    error,
    addMessage,
    appendToLastAssistant,
    setOpen,
    setPending,
    setSources,
    setError,
    reset: resetStore,
  } = useChatStore();

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessageFn = useCallback(
    async (text: string): Promise<void> => {
      // Guard: skip empty / whitespace-only messages
      if (!text.trim()) return;

      // Guard: do not allow concurrent sends
      if (useChatStore.getState().isPending) return;

      // Capture conversation history BEFORE adding the new messages
      const conversationHistory = [...useChatStore.getState().messages];

      // 1. Add user message
      addMessage({ role: 'user', content: text });

      // 2. Add empty assistant message (will be filled by streaming tokens)
      addMessage({ role: 'assistant', content: '' });

      // 3. Set pending
      setPending(true);

      // 4. Create AbortController for this stream
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // 5. Call sendChatMessage with SSE callbacks
      await sendChatMessage(
        dashboardId,
        {
          message: text,
          conversation_history: conversationHistory,
        },
        {
          onToken: (token: string) => {
            appendToLastAssistant(token);
          },
          onDone: (sourcesData) => {
            setSources(sourcesData);
            setPending(false);
          },
          onError: (errorMsg: string) => {
            setError(errorMsg);
            setPending(false);
          },
        },
        controller.signal,
      );
    },
    [dashboardId, addMessage, appendToLastAssistant, setPending, setSources, setError],
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setPending(false);
  }, [setPending]);

  const togglePanel = useCallback(() => {
    setOpen(!useChatStore.getState().isOpen);
  }, [setOpen]);

  const reset = useCallback(() => {
    // Abort any in-flight stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    resetStore();
  }, [resetStore]);

  return {
    messages,
    isOpen,
    isPending,
    sources,
    error,
    sendMessage: sendMessageFn,
    cancelStream,
    togglePanel,
    reset,
  };
}
