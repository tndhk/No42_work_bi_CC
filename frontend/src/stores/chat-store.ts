import { create } from 'zustand';
import type { ChatMessage, ChatSource } from '@/types';

export interface ChatState {
  messages: ChatMessage[];
  isOpen: boolean;
  isPending: boolean;
  sources: ChatSource[];
  error: string | null;
  addMessage: (message: ChatMessage) => void;
  appendToLastAssistant: (text: string) => void;
  setOpen: (open: boolean) => void;
  setPending: (pending: boolean) => void;
  setSources: (sources: ChatSource[]) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  messages: [] as ChatMessage[],
  isOpen: false,
  isPending: false,
  sources: [] as ChatSource[],
  error: null as string | null,
};

export const useChatStore = create<ChatState>((set) => ({
  ...initialState,

  addMessage: (message: ChatMessage) =>
    set((state) => ({
      messages: [...state.messages, message],
      error: null,
    })),

  appendToLastAssistant: (text: string) =>
    set((state) => {
      const lastAssistantIndex = state.messages.findLastIndex(
        (m) => m.role === 'assistant',
      );
      if (lastAssistantIndex === -1) return state;

      const updated = state.messages.map((m, i) =>
        i === lastAssistantIndex ? { ...m, content: m.content + text } : m,
      );
      return { messages: updated };
    }),

  setOpen: (open: boolean) => set({ isOpen: open }),

  setPending: (pending: boolean) => set({ isPending: pending }),

  setSources: (sources: ChatSource[]) => set({ sources }),

  setError: (error: string | null) => set({ error }),

  reset: () => set({ ...initialState }),
}));
