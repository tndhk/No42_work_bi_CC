import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/stores/chat-store';
import type { ChatMessage, ChatSource } from '@/types';

describe('useChatStore', () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });

  // -----------------------------------------------------------------------
  // Initial State
  // -----------------------------------------------------------------------
  describe('initial state', () => {
    it('has empty messages array', () => {
      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
    });

    it('has isOpen set to false', () => {
      const state = useChatStore.getState();
      expect(state.isOpen).toBe(false);
    });

    it('has isPending set to false', () => {
      const state = useChatStore.getState();
      expect(state.isPending).toBe(false);
    });

    it('has empty sources array', () => {
      const state = useChatStore.getState();
      expect(state.sources).toEqual([]);
    });

    it('has error set to null', () => {
      const state = useChatStore.getState();
      expect(state.error).toBeNull();
    });
  });

  // -----------------------------------------------------------------------
  // addMessage
  // -----------------------------------------------------------------------
  describe('addMessage', () => {
    it('appends a user message to messages array', () => {
      const msg: ChatMessage = { role: 'user', content: 'Hello' };
      useChatStore.getState().addMessage(msg);

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0]).toEqual(msg);
    });

    it('appends an assistant message to messages array', () => {
      const msg: ChatMessage = { role: 'assistant', content: 'Hi there' };
      useChatStore.getState().addMessage(msg);

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0]).toEqual(msg);
    });

    it('appends multiple messages in order', () => {
      const msg1: ChatMessage = { role: 'user', content: 'Hello' };
      const msg2: ChatMessage = { role: 'assistant', content: 'Hi' };
      const msg3: ChatMessage = { role: 'user', content: 'How are you?' };

      useChatStore.getState().addMessage(msg1);
      useChatStore.getState().addMessage(msg2);
      useChatStore.getState().addMessage(msg3);

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(3);
      expect(state.messages[0]).toEqual(msg1);
      expect(state.messages[1]).toEqual(msg2);
      expect(state.messages[2]).toEqual(msg3);
    });

    it('clears error when adding a message', () => {
      useChatStore.getState().setError('previous error');
      const msg: ChatMessage = { role: 'user', content: 'Hello' };
      useChatStore.getState().addMessage(msg);

      expect(useChatStore.getState().error).toBeNull();
    });
  });

  // -----------------------------------------------------------------------
  // appendToLastAssistant
  // -----------------------------------------------------------------------
  describe('appendToLastAssistant', () => {
    it('appends text to the last assistant message', () => {
      const msg: ChatMessage = { role: 'assistant', content: 'Hello' };
      useChatStore.getState().addMessage(msg);
      useChatStore.getState().appendToLastAssistant(' world');

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].content).toBe('Hello world');
    });

    it('only modifies the last assistant message, not user messages', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'Question' });
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Answer' });
      useChatStore.getState().addMessage({ role: 'user', content: 'Follow up' });

      useChatStore.getState().appendToLastAssistant(' more');

      const state = useChatStore.getState();
      expect(state.messages[1].content).toBe('Answer more');
      expect(state.messages[0].content).toBe('Question');
      expect(state.messages[2].content).toBe('Follow up');
    });

    it('does nothing when there are no messages', () => {
      useChatStore.getState().appendToLastAssistant('text');

      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
    });

    it('does nothing when there are no assistant messages', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'Hello' });
      useChatStore.getState().appendToLastAssistant('text');

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].content).toBe('Hello');
    });

    it('handles streaming by appending multiple tokens sequentially', () => {
      useChatStore.getState().addMessage({ role: 'assistant', content: '' });
      useChatStore.getState().appendToLastAssistant('Hello');
      useChatStore.getState().appendToLastAssistant(' ');
      useChatStore.getState().appendToLastAssistant('world');

      const state = useChatStore.getState();
      expect(state.messages[0].content).toBe('Hello world');
    });
  });

  // -----------------------------------------------------------------------
  // setOpen
  // -----------------------------------------------------------------------
  describe('setOpen', () => {
    it('sets isOpen to true', () => {
      useChatStore.getState().setOpen(true);
      expect(useChatStore.getState().isOpen).toBe(true);
    });

    it('sets isOpen to false', () => {
      useChatStore.getState().setOpen(true);
      useChatStore.getState().setOpen(false);
      expect(useChatStore.getState().isOpen).toBe(false);
    });
  });

  // -----------------------------------------------------------------------
  // setPending
  // -----------------------------------------------------------------------
  describe('setPending', () => {
    it('sets isPending to true', () => {
      useChatStore.getState().setPending(true);
      expect(useChatStore.getState().isPending).toBe(true);
    });

    it('sets isPending to false', () => {
      useChatStore.getState().setPending(true);
      useChatStore.getState().setPending(false);
      expect(useChatStore.getState().isPending).toBe(false);
    });
  });

  // -----------------------------------------------------------------------
  // setSources
  // -----------------------------------------------------------------------
  describe('setSources', () => {
    it('sets sources array', () => {
      const sources: ChatSource[] = [
        { dataset_name: 'sales', relevance: 'high' },
        { dataset_name: 'users', relevance: 'medium' },
      ];
      useChatStore.getState().setSources(sources);

      expect(useChatStore.getState().sources).toEqual(sources);
    });

    it('replaces existing sources', () => {
      const sources1: ChatSource[] = [{ dataset_name: 'old', relevance: 'low' }];
      const sources2: ChatSource[] = [{ dataset_name: 'new', relevance: 'high' }];

      useChatStore.getState().setSources(sources1);
      useChatStore.getState().setSources(sources2);

      expect(useChatStore.getState().sources).toEqual(sources2);
    });

    it('can set empty sources array', () => {
      useChatStore.getState().setSources([{ dataset_name: 'x', relevance: 'y' }]);
      useChatStore.getState().setSources([]);

      expect(useChatStore.getState().sources).toEqual([]);
    });
  });

  // -----------------------------------------------------------------------
  // setError
  // -----------------------------------------------------------------------
  describe('setError', () => {
    it('sets error message', () => {
      useChatStore.getState().setError('Something went wrong');
      expect(useChatStore.getState().error).toBe('Something went wrong');
    });

    it('clears error by setting null', () => {
      useChatStore.getState().setError('error');
      useChatStore.getState().setError(null);
      expect(useChatStore.getState().error).toBeNull();
    });
  });

  // -----------------------------------------------------------------------
  // reset
  // -----------------------------------------------------------------------
  describe('reset', () => {
    it('resets all state to initial values', () => {
      // Set up non-default state
      useChatStore.getState().addMessage({ role: 'user', content: 'Hello' });
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Hi' });
      useChatStore.getState().setOpen(true);
      useChatStore.getState().setPending(true);
      useChatStore.getState().setSources([{ dataset_name: 'ds', relevance: 'high' }]);
      useChatStore.getState().setError('some error');

      // Reset
      useChatStore.getState().reset();

      // Verify all back to defaults
      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
      expect(state.isOpen).toBe(false);
      expect(state.isPending).toBe(false);
      expect(state.sources).toEqual([]);
      expect(state.error).toBeNull();
    });

    it('can be called multiple times without issue', () => {
      useChatStore.getState().reset();
      useChatStore.getState().reset();

      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
      expect(state.isOpen).toBe(false);
    });
  });

  // -----------------------------------------------------------------------
  // Immutability / State isolation
  // -----------------------------------------------------------------------
  describe('state isolation', () => {
    it('does not mutate previous messages array reference when adding', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'First' });
      const messagesBefore = useChatStore.getState().messages;

      useChatStore.getState().addMessage({ role: 'user', content: 'Second' });
      const messagesAfter = useChatStore.getState().messages;

      expect(messagesBefore).not.toBe(messagesAfter);
      expect(messagesBefore).toHaveLength(1);
      expect(messagesAfter).toHaveLength(2);
    });

    it('does not mutate previous messages array reference when appending to assistant', () => {
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Start' });
      const messagesBefore = useChatStore.getState().messages;

      useChatStore.getState().appendToLastAssistant(' end');
      const messagesAfter = useChatStore.getState().messages;

      expect(messagesBefore).not.toBe(messagesAfter);
    });
  });
});
